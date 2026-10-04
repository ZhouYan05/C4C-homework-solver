# homework-solver · C4C 作业自动求解与排版

一个**以符号引擎为主、国产大模型为辅**的作业自动求解与 LaTeX 排版流水线。
给定一份非微积分作业（线性代数 / 概率论），自动完成：

```
摄入(ingest) → 解析(parse) → 分类(classify) → 求解(solve) → 核验(verify) → LaTeX → PDF
```

核心原则：**正确率可被证明**。所有确定性题型由 SymPy 求解，并再用一条独立路径交叉核验；
大模型只用于无法符号化的题型兜底，且其输出同样必须通过核验层。

## 特性

- **确定性优先**：线性方程组、特征值/特征向量、行列式、矩阵乘法，全部由 SymPy 精确求解。
- **独立核验**：每题用与原求解不同的方法复算（解代回 / trace=Σλ、det=Πλ / LU 对比 / 外层积对比），
  核验不通过会显式标记，绝不"自称正确"。
- **中文排版**：`xelatex + ctex`，A4、题面 / 解答环境、答案框，支持插图嵌入。
- **鲁棒题面**：自动为裸写的 `\begin{cases}` / `pmatrix` 等数学片段补数学定界符，避免 `Missing $`。
- **LLM 兜底可选**：配置 `DASHSCOPE_API_KEY`（Qwen）/ `MOONSHOT_API_KEY`（Kimi）/ `DEEPSEEK_API_KEY` 后启用；
  无密钥时自动降级为纯确定性模式，不报错。

## 快速开始

```bash
pip install -r requirements.txt

# 在 Linux/macOS，或 Windows 下先设置 PYTHONPATH=homework-solver
PYTHONPATH=homework-solver python -m homework_solver.cli \
    --input examples/homework_linalg_prob.md \
    --outdir out \
    --title "线性代数与概率论基础 作业解答" \
    --author "ZhouYan"
```

产物（`out/`）：

| 文件 | 说明 |
| --- | --- |
| `1_parsed.json` | 结构化题目 |
| `3_solutions.json` | 求解结果（含步骤 / 答案 / 核验） |
| `report.json` | 正确率与编译报告 |
| `homework.tex` / `homework.pdf` | LaTeX 源码与最终 PDF |

自检单元测试（离线，无需网络）：

```bash
PYTHONPATH=homework-solver python tests/test_solvers.py
# => ALL SOLVER TESTS PASSED
```

## 支持题型

| 题型 | 引擎 | 核验方式 |
| --- | --- | --- |
| 线性方程组 | `sympy.solve` + `rref` | 解代回原方程，残差为 0 |
| 特征值/特征向量 | `Matrix.eigenvects` | `trace=Σλ`、`det=Πλ` |
| 行列式 | `Matrix.det` | LU 分解与符号展开对比 |
| 矩阵乘法/转置 | `Matrix.__mul__/.T` | 矩阵乘法与外层积求和对比 |
| 二项分布 | `sympy.binomial` | 概率落在 [0,1] |
| 正态分布 | `math.erf` | 概率落在 [0,1] |

## 项目结构

```
homework-solver/homework_solver/
  ingest.py       # md/txt/pdf/docx/ocr 摄入
  parse.py        # 题目切分
  classify.py     # 6 规则路由
  solvers.py      # 确定性求解器注册表
  verify.py       # 独立核验层
  llm.py          # Qwen/Kimi/DeepSeek（OpenAI 兼容）
  render.py       # LaTeX 渲染 + xelatex 编译
  pipeline.py     # 编排
  cli.py          # 命令行入口
tests/test_solvers.py
examples/homework_linalg_prob.md
```

## 环境

- Python 3.12，SymPy 1.14
- LaTeX：MiKTeX（Windows）/ TeX Live，需 `xelatex` 与 `ctex`
- 可选：`pdfplumber` / `python-docx` / `pytesseract` / `Pillow` / `matplotlib`

## 许可

课程作业用途，MIT。
