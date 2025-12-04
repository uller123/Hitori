#!/usr/bin/env python3
"""
Простой CSP-решатель для прямоугольной сетки:

Правила:
 - Числа 1..K
 - Соседи по стороне различны
 - Диагональные соседи различны (единственное доп. правило)

CLI:
 - Проверка корректности входа
 - Поиск 1/N/всех решений
 - Генератор задач (--generate)
 - Сохранение состояния (--save-state) и загрузка (--resume)
 - Обработка отсутствия решения
 - Прямоугольная геометрия
"""

import argparse
from copy import deepcopy
import time
import json
import random

# ---------------- utils ----------------

def neighbors_orth(H,W,r,c):
    for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
        nr,nc = r+dr, c+dc
        if 0 <= nr < H and 0 <= nc < W:
            yield nr,nc

def neighbors_diag(H,W,r,c):
    for dr,dc in ((-1,-1),(-1,1),(1,-1),(1,1)):
        nr,nc = r+dr, c+dc
        if 0 <= nr < H and 0 <= nc < W:
            yield nr,nc

def grid_str(g):
    return "\n".join(" ".join(map(str,row)) for row in g)

# ---------------- solver ----------------

class GridSolver:

    def __init__(self, H, W, K, initial=None):
        self.H = H
        self.W = W
        self.K = K

        if initial:
            self.grid = deepcopy(initial)
        else:
            self.grid = [[0]*W for _ in range(H)]

    # ------------------------------------

    def validate_initial(self):
        """Проверяем, что начальная сетка не нарушает правил."""
        for r in range(self.H):
            for c in range(self.W):
                v = self.grid[r][c]
                if v == 0:
                    continue
                # стороны
                for nr,nc in neighbors_orth(self.H,self.W,r,c):
                    if self.grid[nr][nc] == v:
                        raise ValueError(
                            f"Одинаковые ортогональные соседи ({r},{c}) и ({nr},{nc})"
                        )
                # диагонали
                for nr,nc in neighbors_diag(self.H,self.W,r,c):
                    if self.grid[nr][nc] == v:
                        raise ValueError(
                            f"Одинаковые диагональные соседи ({r},{c}) и ({nr},{nc})"
                        )

    # ------------------------------------

    def allowed_values(self, r, c):
        used = set()
        for nr,nc in neighbors_orth(self.H,self.W,r,c):
            if self.grid[nr][nc] != 0:
                used.add(self.grid[nr][nc])
        for nr,nc in neighbors_diag(self.H,self.W,r,c):
            if self.grid[nr][nc] != 0:
                used.add(self.grid[nr][nc])
        return [v for v in range(1,self.K+1) if v not in used]

    def find_empty(self):
        for r in range(self.H):
            for c in range(self.W):
                if self.grid[r][c] == 0:
                    return r,c
        return None

    # ------------------------------------

    def solve(self, need=1, timeout=None, save_state=None, resume_state=None):
        """
        need = 1, N, или 0 (все).
        save_state — путь для JSON-чекпоинта.
        resume_state — загруженный словарь с состоянием.
        """

        # ------ resume ------
        if resume_state:
            try:
                self.grid = resume_state["grid"]
                print("Состояние восстановлено.")
            except:
                print("Ошибка при resume — продолжаем с нуля.")

        start = time.time()
        solutions = []

        def backtrack():
            nonlocal start, solutions

            if timeout and time.time() - start > timeout:
                return

            empty = self.find_empty()
            if not empty:
                solutions.append(deepcopy(self.grid))

                # чекпоинт при каждом найденном решении
                if save_state:
                    with open(save_state, "w") as f:
                        json.dump({"grid": self.grid}, f)
                return

            r,c = empty
            vals = self.allowed_values(r,c)
            random.shuffle(vals)

            for v in vals:
                self.grid[r][c] = v
                backtrack()
                self.grid[r][c] = 0

                if need != 0 and len(solutions) >= need:
                    return

                # периодические чекпоинты
                if save_state:
                    with open(save_state, "w") as f:
                        json.dump({"grid": self.grid}, f)

        backtrack()
        return solutions

# ---------------- generator ----------------

def generate(H,W,K, timeout=10):
    """Генератор — создаёт полностью заполненную корректную сетку."""

    solver = GridSolver(H,W,K)
    sol = solver.solve(need=1, timeout=timeout)
    if sol:
        return sol[0]
    return None

# ---------------- I/O ----------------

def parse_grid(path, H, W):
    if not path:
        return None
    g = []
    with open(path,"r") as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) != H:
        raise ValueError("Неверное число строк")
    for line in lines:
        row = list(map(int, line.split()))
        if len(row) != W:
            raise ValueError("Неверная длина строки")
        g.append(row)
    return g

# ---------------- CLI ----------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--H", type=int, default=4)
    p.add_argument("--W", type=int, default=4)
    p.add_argument("--K", type=int, default=4)

    p.add_argument("--initial", type=str, default=None)
    p.add_argument("--find", type=int, default=1)
    p.add_argument("--timeout", type=float, default=None)

    p.add_argument("--generate", action="store_true",
                   help="Сгенерировать полное корректное решение")

    p.add_argument("--save-state", type=str, default=None,
                   help="Сохранить прогресс поиска в JSON")

    p.add_argument("--resume", type=str, default=None,
                   help="Загрузить состояние из JSON")

    args = p.parse_args()

    # ---------- generator ----------
    if args.generate:
        sol = generate(args.H, args.W, args.K, timeout=args.timeout)
        if sol:
            print("Сгенерировано решение:")
            print(grid_str(sol))
        else:
            print("Не найдено решения (генератор не смог заполнить).")
        return

    # ---------- solving ----------
    resume_data = None
    if args.resume:
        with open(args.resume, "r") as f:
            resume_data = json.load(f)

    initial = parse_grid(args.initial, args.H, args.W) if args.initial else None

    solver = GridSolver(args.H, args.W, args.K, initial)
    try:
        solver.validate_initial()
    except Exception as e:
        print("Ошибка:", e)
        return

    print("Поиск решений...")
    sols = solver.solve(
        need=args.find,
        timeout=args.timeout,
        save_state=args.save_state,
        resume_state=resume_data
    )

    if not sols:
        print("Решений нет.")
        return

    print(f"Найдено {len(sols)} решение(й).")
    for i,sol in enumerate(sols,1):
        print(f"\n--- Решение {i} ---")
        print(grid_str(sol))


if __name__ == "__main__":
    main()
