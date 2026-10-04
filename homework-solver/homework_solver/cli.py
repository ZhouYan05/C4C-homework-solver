"""命令行入口：python -m homework_solver.cli --input <file> --outdir <dir> ..."""
from __future__ import annotations

import argparse
import json

from .pipeline import run


def main() -> int:
    ap = argparse.ArgumentParser(prog="homework-solver", description="作业自动求解与排版流水线")
    ap.add_argument("--input", required=True, help="作业原件路径（md/txt/pdf/docx/图片）")
    ap.add_argument("--outdir", default="out", help="输出目录")
    ap.add_argument("--title", default="作业自动求解与排版")
    ap.add_argument("--author", default="")
    ap.add_argument("--provider", default="qwen", choices=["qwen", "kimi", "deepseek"])
    ap.add_argument("--json", action="store_true", help="以 JSON 形式输出报告")
    args = ap.parse_args()

    report = run(args.input, args.outdir, args.title, args.author, args.provider)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0 if report["compile"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
