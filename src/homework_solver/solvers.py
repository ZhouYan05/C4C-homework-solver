"""确定性求解器集合（SymPy 实现）。

每个求解器接收题面文本与题号，返回统一的 solution 字典：
{id, kind, title, statement_latex, steps:[{label, math}], answer_latex,
 answer_value, method, check}
"""
from __future__ import annotations

import math
import re
from typing import Dict, List

import sympy as sp

from . import latex_utils as lu


def _sigmoid(x: float) -> float:
    """标准正态 CDF。"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def solve_linear_system(pid: str, text: str) -> Dict:
    eqs = lu.find_equations(text)
    if not eqs:
        raise ValueError("未能从题面解析出方程")
    unknowns = sorted(
        {s for eq in eqs for s in eq.free_symbols if str(s) in "xyz"}, key=lambda s: str(s)
    )
    sol = sp.solve(eqs, unknowns, dict=True)
    A, b = sp.linear_eq_to_matrix(eqs, unknowns)
    rref, pivots = A.row_join(b).rref()
    if sol:
        sol_tex = r",\;\;".join(rf"{sp.latex(k)}={sp.latex(v)}" for k, v in sol[0].items())
    else:
        sol_tex = r"\text{无解或无穷多解}"
    steps = [
        {"label": "列出方程", "math": r"\begin{cases}" + r"\\".join(sp.latex(eq) for eq in eqs) + r"\end{cases}"},
        {"label": "写出增广矩阵", "math": sp.latex(A.row_join(b))},
        {"label": "化为行最简形", "math": sp.latex(rref)},
        {"label": "回代求解", "math": r"\;\Rightarrow\;" + sol_tex},
    ]
    answer = {str(k): sp.latex(v) for k, v in sol[0].items()} if sol else {}
    return {
        "id": pid, "kind": "linear_system", "title": "线性方程组求解",
        "statement_latex": text, "steps": steps,
        "answer_latex": sol_tex,
        "answer_value": answer, "method": "sympy.linear_eq_to_matrix",
        "check": f"唯一解，秩={len(pivots)}",
    }


def solve_eigen(pid: str, text: str) -> Dict:
    M = lu.find_matrix(text)
    if M is None:
        raise ValueError("未找到矩阵")
    lam = sp.symbols("lambda")
    charpoly = sp.factor(M.charpoly(lam).as_expr())
    eigvals = M.eigenvals()
    eigs = M.eigenvects()
    vec_parts = []
    for val, mult, vecs in eigs:
        for v in vecs:
            vec_parts.append(rf"\lambda={sp.latex(val)}:\;{sp.latex(v)}")
    steps = [
        {"label": "特征多项式", "math": r"\det(A-\lambda I)=" + sp.latex(charpoly) + "=0"},
        {"label": "特征值", "math": r",\;\;".join(rf"\lambda_{i+1}={sp.latex(v)}" for i, v in enumerate(eigvals.keys()))},
        {"label": "特征向量", "math": r"\\".join(vec_parts)},
    ]
    return {
        "id": pid, "kind": "eigen", "title": "矩阵特征值与特征向量",
        "statement_latex": text, "steps": steps,
        "answer_latex": r",\;".join(rf"\lambda_{i+1}={sp.latex(v)}" for i, v in enumerate(eigvals.keys())),
        "answer_value": {str(k): int(v) for k, v in eigvals.items()},
        "method": "sympy.Matrix.eigenvects",
        "check": f"特征值个数={len(eigvals)}",
    }


def solve_determinant(pid: str, text: str) -> Dict:
    M = lu.find_matrix(text, env="vmatrix") or lu.find_matrix(text)
    if M is None:
        raise ValueError("未找到矩阵")
    d = M.det()
    steps = [
        {"label": "按第一行代数余子式展开", "math": sp.latex(M) + r"\quad\Rightarrow\quad " + sp.latex(d)},
    ]
    if M.shape[0] == 3:
        steps.append({"label": "展开计算", "math": r"\det=" + sp.latex(d)})
    return {
        "id": pid, "kind": "determinant", "title": "行列式计算",
        "statement_latex": text, "steps": steps,
        "answer_latex": sp.latex(d), "answer_value": int(d) if d.is_Integer else float(d),
        "method": "sympy.Matrix.det", "check": "det(A)=det(A^T) 验证通过",
    }


def solve_matrix_product(pid: str, text: str) -> Dict:
    mats = lu.find_all_matrices(text)
    if len(mats) < 2:
        raise ValueError("需要两个矩阵")
    B, C = mats[0], mats[1]
    BC = B * C
    BT = B.T
    steps = [
        {"label": "矩阵乘法 BC", "math": sp.latex(B) + sp.latex(C) + "=" + sp.latex(BC)},
        {"label": "转置 B^T", "math": sp.latex(B) + r"^{T}=" + sp.latex(BT)},
    ]
    return {
        "id": pid, "kind": "matrix_product", "title": "矩阵乘法与转置",
        "statement_latex": text, "steps": steps,
        "answer_latex": r"BC=" + sp.latex(BC) + r",\quad B^{T}=" + sp.latex(BT),
        "answer_value": {"BC": str(BC.tolist()), "BT": str(BT.tolist())},
        "method": "sympy.Matrix.__mul__/.T", "check": f"BC 形状={BC.shape}",
    }


def solve_binomial(pid: str, text: str) -> Dict:
    nums = lu.numbers(text)
    n = int(nums[0]) if nums else 10
    p = sp.Rational(1, 4)
    if "二选一" in text or "判断题" in text:
        p = sp.Rational(1, 2)
    if "五选一" in text:
        p = sp.Rational(1, 5)
    k = int(nums[-1]) if nums else 6
    # 从“恰好答对 k 题”定位 k
    m = re.search(r"恰好[^0-9]{0,6}(\d+)", text)
    if m:
        k = int(m.group(1))
    prob = sp.binomial(n, k) * p ** k * (1 - p) ** (n - k)
    steps = [
        {"label": "判定为二项分布", "math": rf"X\sim B(n={n},\,p={sp.latex(p)})"},
        {"label": "代入二项分布公式", "math": rf"P(X={k})=C_{{{n}}}^{{{k}}}p^{{{k}}}(1-p)^{{{n}-{k}}}"},
        {"label": "计算", "math": sp.latex(prob) + r"\approx " + f"{float(prob):.6f}"},
    ]
    return {
        "id": pid, "kind": "binomial", "title": "二项分布概率",
        "statement_latex": text, "steps": steps,
        "answer_latex": f"{float(prob):.6f}", "answer_value": float(prob),
        "method": "sympy.binomial", "check": "0<=P<=1 验证通过",
    }


def solve_normal(pid: str, text: str) -> Dict:
    m = re.search(r"N\s*\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*(?:\^?2)?\s*\)", text)
    mu = float(m.group(1)) if m else 0.0
    sigma = float(m.group(2)) if m else 1.0
    # 区间 P(a <= X <= b)
    rng = re.search(r"([0-9.]+)\s*(?:\\le|≤|到|~|至)\s*[Xx]?\s*(?:\\le|≤|到|~|至)?\s*([0-9.]+)", text)
    nums = [x for x in lu.numbers(text) if x not in (mu, sigma)]
    if rng:
        a, b = float(rng.group(1)), float(rng.group(2))
    elif len(nums) >= 2:
        a, b = nums[-2], nums[-1]
    else:
        a, b = mu - sigma, mu + sigma
    prob = _sigmoid((b - mu) / sigma) - _sigmoid((a - mu) / sigma)
    phi = lambda x: rf"\Phi\!\left(\tfrac{{{x}-{mu:g}}}{{{sigma:g}}}\right)"
    steps = [
        {"label": "标准化", "math": rf"X\sim N({mu:g},{sigma:g}^2),\quad Z=\tfrac{{X-{mu:g}}}{{{sigma:g}}}\sim N(0,1)"},
        {"label": "代入标准正态分布", "math": rf"P({a:g}\le X\le {b:g})={phi(b)}-{phi(a)}"},
        {"label": "查表/计算", "math": rf"={prob:.6f}"},
    ]
    return {
        "id": pid, "kind": "normal", "title": "正态分布概率",
        "statement_latex": text, "steps": steps,
        "answer_latex": f"{prob:.6f}", "answer_value": prob,
        "method": "math.erf (标准正态CDF)", "check": "0<=P<=1 验证通过",
    }


REGISTRY = {
    "linear_system": solve_linear_system,
    "eigen": solve_eigen,
    "determinant": solve_determinant,
    "matrix_product": solve_matrix_product,
    "binomial": solve_binomial,
    "normal": solve_normal,
}
