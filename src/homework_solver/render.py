"""LaTeX 渲染与 PDF 编译（中文，xelatex + ctex）。

- 排版规范：article + ctex，A4，1in 边距，题号/解环境，答案框
- 支持通过 matplotlib 生成插图并嵌入（正态分布曲线等）
- 编译优先使用 xelatex；失败时返回日志，不吞错
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import List

from . import latex_utils as lu

_PREAMBLE = r"""\documentclass[12pt, a4paper]{article}
\usepackage{ctex}
\usepackage{amsmath,amssymb,amsthm}
\usepackage[margin=1in]{geometry}
\usepackage{fancyhdr}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=blue}
\pagestyle{fancy}
\fancyhf{}
\rhead{作业自动求解系统}
\lhead{\leftmark}
\cfoot{\thepage}
\newenvironment{problem}[1]{\par\medskip\noindent\textbf{#1}\par}{\par}
\newcommand{\solutionname}{\textbf{解：}}
\newtcolorbox{answerbox}{colback=blue!4,colframe=blue!45!black,boxrule=0.5pt,arc=2pt}
"""


def _need_tcolorbox() -> str:
    return r"\usepackage{tcolorbox}"


def find_xelatex() -> str:
    exe = shutil.which("xelatex")
    if exe:
        return exe
    candidates = [
        r"C:\Users\35586\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe",
        r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return "xelatex"


def render_tex(solutions: List[dict], meta: dict) -> str:
    head = _PREAMBLE.replace(r"\usepackage{xcolor}",
                             r"\usepackage{xcolor}" + "\n" + _need_tcolorbox())
    lines = [head]
    lines.append(r"\title{%s}" % meta.get("title", "作业自动求解与排版"))
    lines.append(r"\author{%s}" % meta.get("author", ""))
    lines.append(r"\date{%s}" % meta.get("date", r"\today"))
    lines.append(r"\begin{document}")
    lines.append(r"\maketitle")
    lines.append(r"\tableofcontents")
    lines.append(r"\newpage")
    for i, s in enumerate(solutions, 1):
        lines.append(r"\section*{第 %s 题\quad %s}" % (s["id"], _esc(s.get("title", ""))))
        lines.append(r"\addcontentsline{toc}{section}{第 %s 题 %s}" % (s["id"], _esc(s.get("title", ""))))
        lines.append(r"\begin{problem}{题面}\end{problem}")
        lines.append(lu.normalize_math(s.get("statement_latex", "")))
        lines.append(r"\par\medskip\solutionname")
        for st in s.get("steps", []):
            lines.append(r"\textbf{%s}\quad" % lu.normalize_math(st["label"]))
            lines.append(r"\[ %s \]" % st["math"])
        lines.append(r"\begin{answerbox}\textbf{答案：}\[ %s \]\end{answerbox}" % s.get("answer_latex", ""))
        if s.get("figure"):
            lines.append(r"\begin{center}\includegraphics[width=0.62\textwidth]{%s}\end{center}" % s["figure"])
        lines.append(r"\medskip")
    lines.append(r"\end{document}")
    return "\n".join(lines)


def _esc(s: str) -> str:
    for a, b in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_")]:
        s = s.replace(a, b)
    return s


def compile_pdf(tex_path: str, out_dir: str | None = None) -> dict:
    tex = Path(tex_path).resolve()
    out = str(Path(out_dir).resolve()) if out_dir else str(tex.parent)
    engine = find_xelatex()
    cmd = [engine, "-interaction=nonstopmode", "-halt-on-error",
           "-output-directory", out, tex.name]
    proc = subprocess.run(cmd, cwd=str(tex.parent), capture_output=True, text=True, errors="ignore")
    pdf = Path(out) / (tex.stem + ".pdf")
    return {"ok": pdf.exists(), "pdf": str(pdf), "engine": engine,
            "exit": proc.returncode, "log_tail": proc.stdout[-1500:]}
