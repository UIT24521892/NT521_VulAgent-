#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm.py — Lớp gọi LLM của pipeline nhóm (Giai đoạn B).

Khác `call_llm` của repo gốc ở một điểm cốt lõi (source_audit §7.2): lời gọi thất bại
thì NÉM `LLMError`, không trả chuỗi "ERROR: LLM call failed" để bước sau hiểu nhầm
thành "không có lỗ hổng". Pipeline bắt `LLMError` và ghi quyết định `unknown`.

Ba backend:
  - ReplayBackend      : phát lại output từng agent đã lưu trong một file `*_full.json`
                         mà repo gốc công bố. 0 đồng, không cần mạng. Kết quả là
                         "phát lại output công bố", KHÔNG phải nhóm chạy model.
  - ScriptedBackend    : trả lời theo kịch bản, chỉ dùng cho test.
  - OpenAICompatBackend: gọi API thật (DashScope/OpenAI-compatible). Key đọc từ biến
                         môi trường; không bao giờ ghi key ra log/trace.
  - AnthropicBackend   : gọi API Claude (SDK `anthropic` chính thức). Dùng khi chạy
                         pipeline trên backend Claude — LƯU Ý: đây là thí nghiệm
                         "đánh giá phương pháp trên backend khác", KHÔNG phải tái hiện
                         đúng model của paper (Qwen3/GPT-4o).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

# Sentinel của repo gốc (VulAgent-Qwen.py, call_llm). Gặp trong fixture nghĩa là lượt
# chạy công bố đã lỗi hạ tầng ở agent đó.
LLM_ERROR_SENTINEL = "ERROR: LLM call failed"


class LLMError(Exception):
    """Lời gọi LLM không cho ra văn bản dùng được (lỗi mạng, timeout, thiếu output...)."""


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int | None = None      # None = backend không đo được
    completion_tokens: int | None = None
    latency_s: float = 0.0


class Backend:
    name = "base"
    model = "n/a"

    def complete(self, agent: str, prompt: str) -> LLMResult:  # pragma: no cover
        raise NotImplementedError


# ───────────────────────── Replay ─────────────────────────
class ReplayBackend(Backend):
    """Phát lại output đã lưu trong một `*_full.json` của repo gốc.

    Ánh xạ agent → trường trong fixture (đọc từ `analyse()` của repo):
      MetaAgent / agent phát hiện → chuỗi thô lưu ở khóa cùng tên
      AggregatorAgent            → repo chỉ lưu bản ĐÃ PARSE; dump lại thành JSON
      TriggerPlannerAgent        → chuỗi thô
      UnifiedPrunerAgent         → FinalValidatorAgent.per_issue_reports[0].ProtectionAgent_output
      FinalValidatorAgent        → FinalValidatorAgent.per_issue_reports[0].FinalValidatorAgent_raw
    """
    name = "replay"

    def __init__(self, fixture: dict, model: str = "upstream-published-output"):
        self.fixture = fixture
        self.model = model

    def _lookup(self, agent: str):
        d = self.fixture
        if agent == "AggregatorAgent":
            agg = d.get("AggregatorAgent")
            return None if agg is None else json.dumps(agg, ensure_ascii=False)
        if agent in ("UnifiedPrunerAgent", "FinalValidatorAgent"):
            reports = (d.get("FinalValidatorAgent") or {}).get("per_issue_reports") or []
            if not reports or not isinstance(reports[0], dict):
                return None
            key = "ProtectionAgent_output" if agent == "UnifiedPrunerAgent" else "FinalValidatorAgent_raw"
            return reports[0].get(key)
        return d.get(agent)

    def complete(self, agent: str, prompt: str) -> LLMResult:
        out = self._lookup(agent)
        if not isinstance(out, str):
            raise LLMError(f"fixture không lưu output của {agent}")
        if LLM_ERROR_SENTINEL in out:
            raise LLMError(f"fixture ghi nhận lỗi LLM ở {agent} (sentinel của repo gốc)")
        return LLMResult(text=out)


# ───────────────────────── Scripted (test) ─────────────────────────
class ScriptedBackend(Backend):
    """Trả lời theo dict {agent: str | Exception}. Thiếu agent → LLMError."""
    name = "scripted"

    def __init__(self, script: dict):
        self.script = script
        self.calls: list[tuple[str, str]] = []

    def complete(self, agent: str, prompt: str) -> LLMResult:
        self.calls.append((agent, prompt))
        out = self.script.get(agent)
        if isinstance(out, Exception):
            raise out
        if out is None:
            raise LLMError(f"kịch bản không có output cho {agent}")
        return LLMResult(text=out, prompt_tokens=len(prompt) // 4, completion_tokens=len(out) // 4)


# ───────────────────────── API thật ─────────────────────────
class OpenAICompatBackend(Backend):
    """Gọi endpoint OpenAI-compatible. TỐN PHÍ — chỉ tạo khi người chạy đã xác nhận.

    Tham số suy luận giữ như repo gốc: temperature 0, top_p 1, max_tokens 4096,
    enable_thinking=False, cùng system prompt.
    """
    name = "openai-compat"
    SYSTEM = "Please output strictly in JSON format. Only output the JSON object."

    def __init__(self, api_key_env: str = "DASHSCOPE_API_KEY",
                 base_url_env: str = "DASHSCOPE_BASE_URL",
                 model_env: str = "VULAGENT_MODEL",
                 max_retries: int = 2, timeout_s: float = 120.0,
                 max_tokens: int = 4096):
        key = os.environ.get(api_key_env, "").strip()
        base_url = os.environ.get(base_url_env, "").strip()
        self.model = os.environ.get(model_env, "").strip()
        missing = [n for n, v in ((api_key_env, key), (base_url_env, base_url), (model_env, self.model)) if not v]
        if missing:
            raise LLMError("thiếu biến môi trường: " + ", ".join(missing))
        try:
            from openai import OpenAI  # import trễ: phần offline không cần thư viện này
        except ImportError as e:
            raise LLMError("chưa cài gói `openai` (xem experiment_manifest.yaml)") from e
        self._client = OpenAI(api_key=key, base_url=base_url, timeout=timeout_s, max_retries=0)
        self.max_retries = max_retries
        self.max_tokens = max_tokens

    def complete(self, agent: str, prompt: str) -> LLMResult:
        last = None
        for attempt in range(self.max_retries + 1):
            t0 = time.time()
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": self.SYSTEM},
                              {"role": "user", "content": prompt}],
                    temperature=0.0, top_p=1.0, max_tokens=self.max_tokens,
                    extra_body={"enable_thinking": False},
                )
                text = (resp.choices[0].message.content or "").strip()
                if not text:
                    raise LLMError("model trả nội dung rỗng")
                usage = getattr(resp, "usage", None)
                return LLMResult(
                    text=text,
                    prompt_tokens=getattr(usage, "prompt_tokens", None),
                    completion_tokens=getattr(usage, "completion_tokens", None),
                    latency_s=time.time() - t0,
                )
            except Exception as e:  # chỉ giữ tên lớp + thông điệp, không giữ header/khóa
                last = e
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
        raise LLMError(f"{agent}: {type(last).__name__}: {str(last)[:300]}")


# ───────────────────────── API thật — Claude ─────────────────────────
class AnthropicBackend(Backend):
    """Gọi API Claude qua SDK `anthropic` chính thức (không dùng shim OpenAI). TỐN PHÍ.

    KHÁC cấu hình paper: current Claude models (Opus/Sonnet/Haiku 5.x) **từ chối**
    `temperature`/`top_p`, nên không set — đây là một lý do đây là thí nghiệm backend
    khác, không phải tái hiện `temperature=0` của paper. Điều khiển độ sâu suy nghĩ
    bằng `effort` (mặc định "low" để tiết kiệm token cho tác vụ phân loại).

    Rủi ro cần theo dõi: bộ phân loại an toàn `cyber` của Claude có thể TỪ CHỐI một
    số mẫu mã lỗ hổng (stop_reason="refusal") → ta ném LLMError → mẫu thành `unknown`,
    không âm thầm biến thành benign.
    """
    name = "anthropic"
    SYSTEM = "Please output strictly in JSON format. Only output the JSON object."

    def __init__(self, api_key_env: str = "ANTHROPIC_API_KEY",
                 base_url_env: str = "ANTHROPIC_BASE_URL",
                 model_env: str = "VULAGENT_MODEL",
                 effort_env: str = "VULAGENT_EFFORT",
                 max_retries: int = 2, timeout_s: float = 600.0,
                 max_tokens: int = 4096):
        key = os.environ.get(api_key_env, "").strip()
        self.model = os.environ.get(model_env, "").strip()
        if not key:
            raise LLMError(f"thiếu biến môi trường: {api_key_env}")
        if not self.model:
            raise LLMError(f"thiếu biến môi trường: {model_env}")
        self.effort = os.environ.get(effort_env, "low").strip() or "low"
        try:
            from anthropic import Anthropic  # import trễ: phần offline không cần thư viện này
        except ImportError as e:
            raise LLMError("chưa cài gói `anthropic` (pip install anthropic)") from e
        kwargs = {"api_key": key, "timeout": timeout_s, "max_retries": max_retries}
        base_url = os.environ.get(base_url_env, "").strip()
        if base_url:
            kwargs["base_url"] = base_url
        self._client = Anthropic(**kwargs)
        self.max_tokens = max_tokens

    def complete(self, agent: str, prompt: str) -> LLMResult:
        t0 = time.time()
        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                output_config={"effort": self.effort},
            )
        except Exception as e:  # SDK tự retry; chỉ giữ tên lớp + thông điệp, không giữ key
            raise LLMError(f"{agent}: {type(e).__name__}: {str(e)[:300]}") from e

        if getattr(resp, "stop_reason", None) == "refusal":
            raise LLMError(f"{agent}: Claude từ chối (refusal) — không coi là benign")
        # Chỉ lấy khối văn bản, bỏ khối thinking.
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
        if not text:
            raise LLMError(f"{agent}: model trả nội dung rỗng (stop_reason={getattr(resp, 'stop_reason', None)})")
        usage = getattr(resp, "usage", None)
        return LLMResult(
            text=text,
            prompt_tokens=getattr(usage, "input_tokens", None),
            completion_tokens=getattr(usage, "output_tokens", None),
            latency_s=time.time() - t0,
        )
