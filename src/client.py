"""OpenRouter chat client: retries, on-disk caching, usage logging, budget guard.

OpenRouter is OpenAI-API-compatible, so we use the ``openai`` SDK pointed at
``https://openrouter.ai/api/v1``.

IMPORTANT: this is a text-in / text-out API. It returns no activations or
hidden states. Any mechanistic-interpretability follow-up must run the
open-weight models locally (TransformerLens / nnsight) or via NDIF -- not here.

Caching is keyed by (model, messages, params, run_index). Re-running analysis
or resuming a crashed run must never re-call the API, so every successful call
is written to ``cache/<key>.json`` and served from there next time.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class BudgetExceeded(RuntimeError):
    """Raised when cumulative spend would exceed the configured hard cap."""


class Client:
    """Thin wrapper around the OpenRouter chat-completions endpoint."""

    def __init__(self, cache_dir: str = "cache", budget_usd_max: float = 10.0):
        load_dotenv()
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY not set. Put it in .env (see .env.example)."
            )
        self._client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.budget_usd_max = budget_usd_max
        self.spend_usd = 0.0
        self.call_log: list[dict] = []

    # -- cache key ---------------------------------------------------------- #
    def _cache_key(self, model: str, messages: list[dict], params: dict, run_index: int) -> str:
        blob = json.dumps(
            {"model": model, "messages": messages, "params": params, "run_index": run_index},
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # -- actual network call (retried) ------------------------------------- #
    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
    )
    def _raw_call(self, model: str, messages: list[dict], params: dict):
        return self._client.chat.completions.create(
            model=model,
            messages=messages,
            # Ask OpenRouter to include cost in the usage object when available.
            extra_body={"usage": {"include": True}},
            **params,
        )

    # -- public API --------------------------------------------------------- #
    def chat(self, model: str, messages: list[dict], run_index: int = 0, **params) -> dict:
        """Return a record dict with content + usage. Cached and budget-guarded."""
        key = self._cache_key(model, messages, params, run_index)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            record = json.loads(cache_file.read_text(encoding="utf-8"))
            record["cached"] = True
            return record

        if self.spend_usd >= self.budget_usd_max:
            raise BudgetExceeded(
                f"spend ${self.spend_usd:.4f} >= cap ${self.budget_usd_max:.2f}"
            )

        t0 = time.time()
        resp = self._raw_call(model, messages, params)
        latency = time.time() - t0

        choice = resp.choices[0]
        content = choice.message.content or ""
        usage = getattr(resp, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        # OpenRouter returns a float cost (USD) in usage.cost when include=True.
        cost = float(getattr(usage, "cost", 0.0) or 0.0)
        self.spend_usd += cost

        record = {
            "model": model,
            "model_version": getattr(resp, "model", model),
            "params": params,
            "run_index": run_index,
            "content": content,
            "finish_reason": getattr(choice, "finish_reason", None),
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_usd": cost,
            },
            "latency_s": round(latency, 3),
            "timestamp": time.time(),
            "cached": False,
        }
        self.call_log.append(record)
        cache_file.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        return record
