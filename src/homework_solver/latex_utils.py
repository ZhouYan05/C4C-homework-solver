"""LaTeX 数学片段解析工具：从题面中抽取矩阵、方程组、标量等结构化对象。

设计原则：优先从题面的 LaTeX 源码直接抽取，尽量不依赖人工标注；
抽取失败时返回 None，由上层（classify/LLM 兜底路径）决定后续处理。
"""
from __future__ import annotations

import re
from typing import List, Optional

import sympy as sp

# 常用符号：x,y,z 为未知量；a,b,c 等作为可出现的系数符号
_SYMBOLS = sp.symbols("x y z a b c d e f g h", real=True)
_LOCAL = {str(s): s for s in _SYMBOLS}
_LOCAL.update({"pi": sp.pi, "e": sp.E, "sqrt": sp.sqrt, "log": sp.log, "ln": sp.log})

_MATRIX_ENVS = ("pmatrix", "bmatrix", "vmatrix", "matrix", "Bmatrix", "Vmatrix")

# 需要被自动包进数学模式（\[...\]）的显示数学环境
_DISPLAY_ENVS = ("cases", "align", "aligned", "gather", "gathered", "array", "equation",
                 "pmatrix", "bmatrix", "vmatrix", "matrix", "Bmatrix", "Vmatrix")

_INLINE_MATH_HINT = set("^_\\")


def normalize_math(text: str) -> str:
    """把题面里裸写的 LaTeX 数学补上数学定界符，使其可安全嵌入正文模式。

    处理三类情况：
    1. 已带 $...$ / \\[...\\] / \\(...\\) 的片段原样保留；
    2. 裸 \\begin{cases}...\\end{cases} 等显示环境 → 包成 \\[...\\]；
    3. 行内裸数学记号（含 ^ _ \\ 的 ASCII 片段）→ 包成 $...$。
    """
    store: dict[str, str] = {}

    def _stash_wrapped(m: "re.Match[str]") -> str:
        key = f"\x00M{len(store)}\x00"
        store[key] = "\\[" + m.group(0) + "\\]"
        return key

    def _stash_asis(m: "re.Match[str]") -> str:
        key = f"\x00M{len(store)}\x00"
        store[key] = m.group(0)
        return key

    # 1) 已有数学：先占位保护
    text = re.sub(r"\\\[.*?\\\]", _stash_asis, text, flags=re.S)
    text = re.sub(r"\$[^$]*\$", _stash_asis, text, flags=re.S)

    def _wrap_paren_math(m: "re.Match[str]") -> str:
        key = f"\x00M{len(store)}\x00"
        store[key] = "$" + m.group(0)[2:-2] + "$"
        return key

    text = re.sub(r"\\\(.*?\\\)", _wrap_paren_math, text, flags=re.S)
    # 2) 裸显示环境
    env_alt = "|".join(_DISPLAY_ENVS)
    text = re.sub(r"\\begin\{(" + env_alt + r")\}.*?\\end\{\1\}", _stash_wrapped, text, flags=re.S)
    # 3) 行内裸数学记号：ASCII 片段且含 ^ _ \ 之一
    def _wrap_inline(m: "re.Match[str]") -> str:
        tok = m.group(0)
        if any(c in _INLINE_MATH_HINT for c in tok):
            return "$" + tok + "$"
        return tok
    text = re.sub(r"[A-Za-z0-9\\\{\}\^\_\+\-\*/,\.\|\(\)]+", _wrap_inline, text)
    # 还原
    for k, v in store.items():
        text = text.replace(k, v)
    return text


def _sympify(expr: str):
    """把一段 ASCII 数学写成 sympy 表达式，容忍 LaTeX 常见写法。"""
    s = expr.strip()
    s = s.replace("\\times", "*").replace("\\cdot", "*")
    s = s.replace("\\pi", "pi").replace("\\sqrt", "sqrt")
    s = s.replace("\\left", "").replace("\\right", "").replace("\\,", "")
    s = s.replace("{", "(").replace("}", ")")
    s = s.replace("^", "**")
    s = re.sub(r"\s+", "", s)
    return sp.sympify(s, locals=_LOCAL)


def find_matrix(text: str, env: Optional[str] = None) -> Optional[sp.Matrix]:
    """从文本中提取第一个矩阵环境，返回 sympy.Matrix。

    env 指定时只匹配该环境（如 "vmatrix"）；否则匹配任意矩阵环境。
    """
    envs = (env,) if env else _MATRIX_ENVS
    for e in envs:
        m = re.search(r"\\begin\{" + e + r"\}(.*?)\\end\{" + e + r"\}", text, re.S)
        if not m:
            continue
        body = m.group(1)
        rows = [r for r in re.split(r"\\\\", body) if r.strip()]
        grid: List[List[sp.Expr]] = []
        for row in rows:
            cells = [c for c in row.split("&")]
            grid.append([_sympify(c) for c in cells])
        if grid:
            return sp.Matrix(grid)
    return None


def find_all_matrices(text: str, env: Optional[str] = None) -> List[sp.Matrix]:
    envs = (env,) if env else _MATRIX_ENVS
    out: List[sp.Matrix] = []
    for e in envs:
        for m in re.finditer(r"\\begin\{" + e + r"\}(.*?)\\end\{" + e + r"\}", text, re.S):
            body = m.group(1)
            rows = [r for r in re.split(r"\\\\", body) if r.strip()]
            grid = [[_sympify(c) for c in row.split("&")] for row in rows]
            if grid:
                out.append(sp.Matrix(grid))
    return out


def find_equations(text: str) -> List[sp.Eq]:
    """从 cases 环境或逐行的 `lhs = rhs` 中抽取线性方程。"""
    eqs: List[sp.Eq] = []
    m = re.search(r"\\begin\{cases\}(.*?)\\end\{cases\}", text, re.S)
    if m:
        body = m.group(1)
        parts = [p for p in re.split(r"\\\\", body) if p.strip()]
    else:
        parts = [ln for ln in text.splitlines() if "=" in ln and re.search(r"[xyz]", ln)]
    for p in parts:
        p = re.sub(r"&", "", p).strip()
        if "=" not in p or not re.search(r"[xyz]", p):
            continue
        lhs, rhs = p.split("=", 1)
        try:
            eqs.append(sp.Eq(_sympify(lhs), _sympify(rhs)))
        except Exception:
            continue
    return eqs


def numbers(text: str) -> List[float]:
    """抽取文本中的全部数字（含分数 a/b 与简单幂 n^2 的十进制值）。"""
    vals: List[float] = []
    for tok in re.findall(r"[0-9]+(?:\.[0-9]+)?(?:\s*/\s*[0-9]+(?:\.[0-9]+)?)?(?:\^[0-9]+)?", text):
        tok = tok.strip()
        try:
            if "/" in tok:
                a, b = tok.split("/")
                vals.append(float(a) / float(b))
            elif "^" in tok:
                a, b = tok.split("^")
                vals.append(float(a) ** float(b))
            else:
                vals.append(float(tok))
        except Exception:
            continue
    return vals
