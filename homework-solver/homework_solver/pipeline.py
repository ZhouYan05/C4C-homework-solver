"""端到端流水线：ingest -> parse -> classify -> solve -> verify -> render -> compile。

用法（编程接口）：
    from homework_solver.pipeline import run
    report = run("examples/homework.md", outdir="out", provider="qwen")
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from . import parse as _parse
from . import render as _render
from . import verify as _verify
from .ingest import ingest
from .llm import get_backend
from .solvers import REGISTRY


def _solve_unknown(problem, backend) -> Dict:
    """非确定性兜底：调用国产大模型求解，标记 method=llm 且未核验。"""
    text = backend.solve_problem(problem.statement) if backend.enabled else None
    if not text or text.startswith("__LLM_ERROR__"):
        return {
            "id": problem.id, "kind": problem.kind, "title": problem.title,
            "statement_latex": problem.statement, "steps": [],
            "answer_latex": r"\text{（确定性求解器未覆盖，且大模型后端不可用）}",
            "answer_value": None, "method": "unsupported", "verified": False,
            "verify_detail": "no-solver / no-llm",
        }
    if text.startswith("__LLM_ERROR__"):
        text = text.replace("__LLM_ERROR__: ", "")
    return {
        "id": problem.id, "kind": problem.kind or "llm", "title": problem.title,
        "statement_latex": problem.statement,
        "steps": [{"label": "大模型求解", "math": r"\text{见下方逐题解答}"}],
        "answer_latex": rf"\parbox{{0.95\textwidth}}{{{text}}}",
        "answer_value": None, "method": f"llm:{backend.provider}",
        "verified": False, "verify_detail": "LLM 输出未做符号核验",
    }


def run(input_path: str, outdir: str = "out", title: str = "作业自动求解与排版",
        author: str = "", provider: str = "qwen", date: str = r"\today") -> Dict:
    outdir_p = Path(outdir)
    outdir_p.mkdir(parents=True, exist_ok=True)

    raw = ingest(input_path)
    problems = _parse.split_problems(raw)
    backend = get_backend(provider)

    solved: List[Dict] = []
    for p in problems:
        solver = REGISTRY.get(p.kind)
        if solver is not None:
            try:
                sol = solver(p.id, p.statement)
                sol["title"] = sol.get("title", p.title)
                _verify.verify(sol, p.statement)
            except Exception as exc:
                sol = {"id": p.id, "kind": p.kind, "title": p.title,
                       "statement_latex": p.statement, "steps": [],
                       "answer_latex": rf"\text{{求解失败: {exc}}}", "answer_value": None,
                       "method": "solver-error", "verified": False, "verify_detail": str(exc)}
        else:
            sol = _solve_unknown(p, backend)
        solved.append(sol)

    # 持久化中间与结果
    (outdir_p / "1_parsed.json").write_text(
        json.dumps([p.__dict__ for p in problems], ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir_p / "3_solutions.json").write_text(
        json.dumps(solved, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    tex = _render.render_tex(solved, {"title": title, "author": author, "date": date})
    tex_path = outdir_p / "homework.tex"
    tex_path.write_text(tex, encoding="utf-8")
    comp = _render.compile_pdf(str(tex_path), str(outdir_p))

    total = len(solved)
    verified = sum(1 for s in solved if s.get("verified"))
    report = {
        "input": str(input_path), "outdir": str(outdir_p), "total": total,
        "verified": verified, "accuracy": (verified / total) if total else 0.0,
        "llm_backend": backend.status(), "compile": comp,
        "problems": [{"id": s["id"], "kind": s["kind"], "method": s["method"],
                      "verified": s.get("verified"), "detail": s.get("verify_detail")} for s in solved],
    }
    (outdir_p / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return report
