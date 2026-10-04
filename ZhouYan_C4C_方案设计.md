# ZhouYan_C4C_方案设计

## 一、目标

实现一个**中文作业自动求解与排版**流水线 `homework-solver`：输入一份非微积分作业
（线性代数 / 概率论），输出带完整解题步骤、可核验、排版规范的 PDF 成品。
核心指标是**正确率**，且正确性必须能被独立证明，而不是"看起来对"。

## 二、总体架构

```
ingest ──> parse ──> classify ──> solve ──> verify ──> render ──> PDF
 摄入       切题        6规则路由    符号求解    独立交叉核验   xelatex
```

各 Stage 独立文件、单一职责，通过 JSON 中间产物（`1_parsed.json` / `3_solutions.json`）解耦，
任一段可单独替换或测试。

| 模块 | 职责 |
| --- | --- |
| `ingest.py` | 摄入 md/txt（pdf/docx/ocr 为可选扩展），统一为纯文本 |
| `parse.py` | 按题号规则切分题目，抽取题干 |
| `classify.py` | 规则路由到 6 类题型之一 |
| `solvers.py` | 确定性求解器注册表（SymPy 精确计算） |
| `verify.py` | **独立核验层**，用与求解不同的方法复算 |
| `llm.py` | Qwen/Kimi/DeepSeek（OpenAI 兼容）兜底，可选 |
| `render.py` | 生成 LaTeX 并调用 xelatex 编译 + 数学定界符规范化 |
| `pipeline.py` | 编排与报告 |
| `cli.py` | 命令行入口 |

## 三、关键设计决策

### 1. 确定性优先，LLM 只做兜底

大模型在数学推导上会"一本正经地出错"。因此凡是能被 SymPy 符号化的题目
（方程组、特征值、行列式、矩阵运算、二项/正态分布概率），一律走符号引擎得到**精确解**；
只有符号引擎无法处理的题目才交给国产大模型，且其输出同样必须通过核验层。

### 2. 独立核验（本方案的核心）

"用同一个引擎求两次"不构成核验。每类题型都用一条**不同原理**的路径复算：

| 题型 | 求解方法 | 核验方法（独立） |
| --- | --- | --- |
| 线性方程组 | `sympy.solve` / `rref` | 解代回原方程，要求**残差 = 0** |
| 特征值 | `Matrix.eigenvects` | `trace = Σλ` 且 `det = Πλ` |
| 行列式 | `Matrix.det` | LU 分解与符号展开对比 |
| 矩阵乘法/转置 | `Matrix.__mul__` / `.T` | 与外层积逐元素求和对比 |
| 二项分布 | `sympy.binomial` | 概率必须落在 `[0, 1]` |
| 正态分布 | `math.erf` | 概率必须落在 `[0, 1]` |

核验不通过的题目会被标为 `verified:false` 并在 PDF 中显式标注，**绝不称其为正确**。

### 3. 题面鲁棒性（抗 `Missing $`）

真实题面里常有裸写的 `\begin{cases}`、`pmatrix` 或行内 `x^2`、`\lambda_1`。
`latex_utils.normalize_math()` 会：
- 把裸的 display 环境用 `\[ ... \]` 包裹；
- 把裸的行内 `^ _ \` 片段用 `$...$` 包裹；
- 用占位符保护用户已写好的 `$...$` / `\[...\]` / `\(...\)`，避免二次包裹。

这是从三次真实 xelatex 编译失败（`Missing $ inserted`）中迭代出来的修复。

### 4. 中文排版

`xelatex + ctex`，A4 版式，`题目`/`解答` 环境 + 答案框（`tcolorbox`），
页眉页脚（`fancyhdr`），支持插图嵌入。编译通过后校验 PDF 魔数 `%PDF-` 与退出码。

## 四、边界与错误处理

- **无 LLM 密钥**：自动降级为纯确定性模式，`llm_backend` 记为 `qwen(disabled:no-key)`，不抛异常。
- **编译失败**：保留 `.tex` 与 xelatex 日志尾部（`compile.log_tail`），报告 `compile.ok=false`，
  不伪装成功。
- **无法分类的题目**：标记为 `unknown`，走 LLM 或标为待人工复核。
- **核验失败**：计入 `verified/total` 准确率，逐题给出 `detail`。

## 五、与 Claude 基线的关系

Claude 基线（starter kit）面向**微积分极限**题型，并给出 94.4% 的参考正确率。
本方案按挑战要求**切换到非微积分题型（线性代数 + 概率论）**，并额外加入独立核验层——
基线只"生成"，本方案"生成 + 证明"。由于本机无 LLM 密钥，本次运行以纯确定性符号引擎完成，
6/6 题核验通过，准确率 100%（验证报告中有说明与对比口径）。

## 六、交付物

| 交付物 | 文件 |
| --- | --- |
| 方案设计 | `ZhouYan_C4C_方案设计.md`（本文件） |
| 求解器源码 | GitHub 公开仓库 + `ZhouYan_C4C_homework-solver.zip` |
| 作业原件 | `ZhouYan_C4C_作业原件.md` |
| 排版成品 | `ZhouYan_C4C_output.pdf` |
| 验证报告 | `ZhouYan_C4C_验证报告.md` |
| 教学说明 | `ZhouYan_C4C_教学说明.md` |
| AI 日志 | `ZhouYan_C4C_AI日志.md` |
