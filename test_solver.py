import os
import json
import pytest
from solver import HitoriSolver, white_connected

# ---------- Малые сетки ----------

def test_minimal_grid_1x1():
    grid = [[1]]
    solver = HitoriSolver(grid)
    sols = solver.solve(need=1)
    assert sols
    assert sols[0][0][0] in (0,1)  # белая или черная клетка

def test_simple_2x2_solution():
    grid = [
        [1,2],
        [2,1]
    ]
    solver = HitoriSolver(grid)
    sols = solver.solve(need=1)
    assert sols
    for r,row in enumerate(sols[0]):
        for c,val in enumerate(row):
            if val==0:
                # уникальность белых в строке
                row_vals = [grid[r][i] for i in range(len(row)) if row[i]==0]
                assert len(row_vals) == len(set(row_vals))
                # уникальность белых в столбце
                col_vals = [grid[i][c] for i in range(len(row)) if sols[0][i][c]==0]
                assert len(col_vals) == len(set(col_vals))

def test_no_solution_2x2():
    grid = [
        [1,1],
        [2,2]
    ]
    solver = HitoriSolver(grid)
    sols = solver.solve(need=1)
    assert sols == []

# ---------- Черные клетки ----------

def test_black_cells_not_adjacent_3x3():
    grid = [
        [1,2,3],
        [2,3,1],
        [3,1,2]
    ]
    solver = HitoriSolver(grid)
    sols = solver.solve(need=3)
    assert sols
    for s in sols:
        for r in range(len(s)):
            for c in range(len(s[0])):
                if s[r][c]==1:
                    for nr,nc in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                        if 0<=nr<len(s) and 0<=nc<len(s[0]):
                            assert s[nr][nc]!=1

# ---------- Связность белых клеток ----------

def test_white_connected_3x3():
    grid = [
        [1,2,3],
        [2,3,1],
        [3,1,2]
    ]
    solver = HitoriSolver(grid)
    sols = solver.solve(need=2)
    assert sols
    for s in sols:
        new_grid = [[0 if s[r][c]==0 else 1 for c in range(len(s[0]))] for r in range(len(s))]
        assert white_connected(new_grid)

# ---------- Сохранение и возобновление состояния ----------

def test_save_and_resume(tmp_path):
    grid = [
        [1,2],
        [2,1]
    ]
    state_file = tmp_path/"state.json"
    solver = HitoriSolver(grid)
    sols = solver.solve(need=0, save_state=str(state_file))
    assert os.path.exists(state_file)

    with open(state_file) as f:
        state = json.load(f)["state"]

    solver2 = HitoriSolver(grid, state)
    sols2 = solver2.solve(need=0)
    assert sols2

# ---------- Средние сетки ----------

def test_larger_grid_4x4():
    grid = [
        [1,2,3,4],
        [2,3,4,1],
        [3,4,1,2],
        [4,1,2,3]
    ]
    solver = HitoriSolver(grid)
    sols = solver.solve(need=2)
    assert sols

def test_all_solutions_count_2x2():
    grid = [
        [1,2],
        [2,1]
    ]
    solver = HitoriSolver(grid)
    sols = solver.solve(need=0)
    assert len(sols) >= 1

# ---------- Дополнительные проверки ----------

def test_white_cells_unique_in_rows_and_cols():
    grid = [
        [1,2,3],
        [2,3,1],
        [3,1,2]
    ]
    solver = HitoriSolver(grid)
    sols = solver.solve(need=2)
    for s in sols:
        # проверка уникальности белых по строкам
        for r in range(len(grid)):
            row_vals = [grid[r][c] for c in range(len(grid[0])) if s[r][c]==0]
            assert len(row_vals)==len(set(row_vals))
        # проверка уникальности белых по столбцам
        for c in range(len(grid[0])):
            col_vals = [grid[r][c] for r in range(len(grid)) if s[r][c]==0]
            assert len(col_vals)==len(set(col_vals))
