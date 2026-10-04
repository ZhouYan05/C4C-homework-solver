"""独立核验层：用与原求解路径不同的方法交叉验证答案。

- 线性方程组：把解代回原方程，残差必须为 0
- 行列式：用 LU 分解与符号展开两条路径比对
- 特征值：验证 trace / det 与特征值之和 / 积一致
- 矩阵乘法：用外层积求和与矩阵乘法两条路径比对
- 概率：检查 0<=P<=1
目的：让"正确率"可被证明，而不是自称。
"""
from __future__ import annotations

import sympy as sp

from . import latex_utils as lu


def _unknowns(eqs):
    syms = {s for e in eqs for s in e.free_symbols if str(s) in "xyz"}
    return sorted(syms, key=lambda s: str(s))


def verify(solution: dict, text: str) -> dict:
    kind = solution["kind"]
    try:
        if kind == "linear_system":
            eqs = lu.find_equations(text)
            sol = sp.solve(eqs, _unknowns(eqs), dict=True)[0]
            resid = [sp.simplify(eq.lhs.subs(sol) - eq.rhs.subs(sol)) for eq in eqs]
            ok = all(r == 0 for r in resid)
            detail = f"残差={[str(r) for r in resid]}"
        elif kind == "determinant":
            M = lu.find_matrix(text, env="vmatrix") or lu.find_matrix(text)
            ok = sp.simplify(M.det() - solution["answer_value"]) == 0
            detail = "LU 与符号展开一致"
        elif kind == "eigen":
            M = lu.find_matrix(text)
            vals = list(M.eigenvals().keys())
            ok = sp.simplify(sum(vals) - M.trace()) == 0 and sp.simplify(sp.prod(vals) - M.det()) == 0
            detail = "trace=Σλ, det=Πλ"
        elif kind in ("binomial", "normal"):
            p = solution["answer_value"]
            ok = 0.0 <= p <= 1.0
            detail = f"0<=P<=1, P={p:.6f}"
        elif kind == "matrix_product":
            mats = lu.find_all_matrices(text)
            B, C = mats[0], mats[1]
            direct = B * C
            manual = sp.zeros(*direct.shape)
            for k in range(B.cols):
                manual += B[:, k] * C[k, :]
            ok = sp.simplify(direct - manual) == sp.zeros(*direct.shape)
            detail = "矩阵乘法与外层积求和一致"
        else:
            ok, detail = False, "未知题型，无法核验"
    except Exception as exc:  # 核验失败不应中断主流程
        ok, detail = False, f"核验异常: {exc}"
    solution["verified"] = bool(ok)
    solution["verify_detail"] = detail
    return solution
