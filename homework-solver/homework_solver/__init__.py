"""homework-solver: 端到端作业自动求解与排版流水线。

架构：ingest -> parse -> classify -> solve(hybrid: SymPy 确定性 + 大模型兜底) -> verify -> render(LaTeX) -> compile(PDF)
国产大模型为可插拔后端（Qwen/Kimi/DeepSeek，OpenAI 兼容协议），确定性引擎负责数值/符号求解并可对大模型结果做交叉核验。
"""
__version__ = "1.0.0"
__all__ = ["__version__"]
