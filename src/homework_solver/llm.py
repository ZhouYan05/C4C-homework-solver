"""国产大模型可插拔后端（OpenAI 兼容协议）。

支持的提供商（按环境变量取密钥，均可自定义 base_url）：
- qwen    : DASHSCOPE_API_KEY  , 默认 https://dashscope.aliyuncs.com/compatible-mode/v1
- kimi    : MOONSHOT_API_KEY   , 默认 https://api.moonshot.cn/v1
- deepseek: DEEPSEEK_API_KEY   , 默认 https://api.deepseek.com/v1

设计：确定性引擎（SymPy）为主，大模型用于
(1) 题面解析/兜底（classify=unknown 时），(2) 非符号化题目的求解，
(3) 生成教学式讲解文本。大模型输出一律交由 verify.py 交叉核验后才计入正确率。
无密钥时后端 disabled，流水线自动走确定性路径并记录到 AI 日志。
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional

_PROVIDERS = {
    "qwen": ("DASHSCOPE_API_KEY", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
    "kimi": ("MOONSHOT_API_KEY", "https://api.moonshot.cn/v1", "moonshot-v1-8k"),
    "deepseek": ("DEEPSEEK_API_KEY", "https://api.deepseek.com/v1", "deepseek-chat"),
}


class LLMBackend:
    def __init__(self, provider: str = "qwen", model: Optional[str] = None, base_url: Optional[str] = None):
        self.provider = provider
        key_env, default_base, default_model = _PROVIDERS.get(provider, _PROVIDERS["qwen"])
        self.api_key = os.environ.get(key_env, "")
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL") or default_base).rstrip("/")
        self.model = model or os.environ.get("LLM_MODEL") or default_model
        self.enabled = bool(self.api_key)

    def chat(self, system: str, user: str, temperature: float = 0.0) -> Optional[str]:
        if not self.enabled:
            return None
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature,
        }
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except Exception as exc:  # 网络/鉴权失败降级
            return f"__LLM_ERROR__: {exc}"

    def solve_problem(self, text: str) -> Optional[str]:
        system = "你是严谨的大学数学助教。只给出可核验的解题步骤与最终答案，使用 LaTeX 数学记号。"
        return self.chat(system, f"请解答以下题目：\n{text}")

    def status(self) -> str:
        return f"{self.provider}({'enabled' if self.enabled else 'disabled:no-key'})"


def get_backend(provider: str = "qwen") -> LLMBackend:
    return LLMBackend(provider=provider)
