"""求解器单元测试：对 6 类题型做端到端断言（离线、确定性）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from homework_solver import verify  # noqa: E402
from homework_solver.solvers import REGISTRY  # noqa: E402

CASES = {
    "linear_system": r"解方程组 \begin{cases} x + y + z = 6 \\ 2x - y + z = 3 \\ 3x + 2y - z = 4 \end{cases}",
    "eigen": r"求矩阵 \begin{pmatrix} 2 & 1 \\ 1 & 3 \end{pmatrix} 的特征值",
    "determinant": r"计算行列式 \begin{vmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \\ 7 & 8 & 10 \end{vmatrix}",
    "matrix_product": r"矩阵乘法 \begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}\begin{pmatrix} 2 & 0 \\ 1 & 2 \end{pmatrix} 转置",
    "binomial": r"10 道四选一，求恰好答对 6 题的概率",
    "normal": r"X 服从正态分布 N(75, 10^2)，求 P(65 ≤ X ≤ 85)",
}


def test_all_kinds():
    for kind, text in CASES.items():
        sol = REGISTRY[kind]("t", text)
        verify.verify(sol, text)
        assert sol["verified"], f"{kind} 核验失败: {sol.get('verify_detail')}"


if __name__ == "__main__":
    test_all_kinds()
    print("ALL SOLVER TESTS PASSED")
