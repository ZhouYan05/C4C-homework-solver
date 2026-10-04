---
name: homework-solver
description: 中文作业自动求解与 LaTeX 排版技能。输入一份作业（线性代数/概率论，md/txt/pdf），输出可核验的解答、LaTeX 源码与 PDF 成品。所有确定性题目由 SymPy 求解并独立核验，无法符号化的题目可选用国产大模型兜底。
---

# homework-solver

**作业自动求解与排版**技能。流水线：摄入 → 解析 → 分类 → 求解 → 核验 → LaTeX → PDF。

## 何时使用

- 你有一份**非微积分**作业（线性方程组、特征值、行列式、矩阵运算、二项/正态分布），想自动得到带完整步骤的中文解答 PDF。
- 你想把一批题目从 Markdown / 文本 / PDF 转成排版规范的 LaTeX 文档。

## 输入

- `--input`：作业文件路径，支持 `.md` / `.txt`（`.pdf` / `.docx` / 图片 OCR 需相应可选依赖）。
- `--title` / `--author`：写入 PDF 的标题与作者。
- `--outdir`：输出目录。
- `--provider`：可选 `qwen` / `kimi` / `deepseek`，需对应的 API Key 环境变量。

## 输出

在 `outdir/` 下生成：`1_parsed.json`、`3_solutions.json`、`report.json`、`homework.tex`、`homework.pdf`。

## 使用

```bash
# 依赖
pip install -r requirements.txt

# 运行（Windows 需先设置 PYTHONPATH=homework-solver，Linux/macOS 同）
PYTHONPATH=homework-solver python -m homework_solver.cli \
    --input examples/homework_linalg_prob.md \
    --outdir out \
    --title "线性代数与概率论基础 作业解答" \
    --author "ZhouYan"
```

## 正确性保证

- 线性方程组：`sympy.solve` 求解后**代回原方程**，要求残差 = 0。
- 特征值：`eigenvects` 后核验 `trace = Σλ` 且 `det = Πλ`。
- 行列式：`Matrix.det` 与 LU 分解结果对比。
- 矩阵乘法：逐元素结果与外层积求和对比。
- 概率：结果必须落在 `[0, 1]`。

核验不通过的题目会在 `report.json` 中被标为 `verified:false`，并在 PDF 中显式标注，
**绝不称为"正确"**。

## 限制

- 覆盖的题型有限（见 README「支持题型」表）；超纲题目会走 LLM 兜底或标记为待人工复核。
- 未配置 LLM 密钥时自动降级为纯确定性模式，不影响确定性题目的正确性。
