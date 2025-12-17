#!/usr/bin/env python3
import argparse
from copy import deepcopy
from typing import List, Tuple, Optional
from collections import deque

__all__ = [
    'neighbors_orth',
    'count_connected_components',
    'validate_grid',
    'HitoriSolver',
    'display_grid'
]



def neighbors_orth(H: int, W: int, r: int, c: int):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W:
            yield nr, nc


def count_connected_components(grid: List[List[int]]) -> int:
    H = len(grid)
    W = len(grid[0])
    visited = [[False] * W for _ in range(H)]
    components = 0

    for r in range(H):
        for c in range(W):
            if grid[r][c] == 0 and not visited[r][c]:
                components += 1
                queue = deque([(r, c)])
                visited[r][c] = True

                while queue:
                    cr, cc = queue.popleft()
                    for nr, nc in neighbors_orth(H, W, cr, cc):
                        if grid[nr][nc] == 0 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
    return components


def validate_grid(grid: List[List[int]]) -> Tuple[bool, str]:
    if not grid:
        return False, "Сетка пуста"

    H = len(grid)
    W = len(grid[0])

    for r, row in enumerate(grid):
        if len(row) != W:
            return False, f"Строка {r} имеет длину {len(row)}, ожидалось {W}"

    for r in range(H):
        for c in range(W):
            val = grid[r][c]
            if not isinstance(val, int) or val <= 0:
                return False, f"Неверное значение в ({r},{c}): {val}"

    if H < 2 or W < 2:
        return False, "Сетка должна быть минимум 2x2"

    return True, "OK"


class HitoriSolver:
    def __init__(self, grid: List[List[int]],
                 state: Optional[List[List[Optional[int]]]] = None,
                 max_components: int = 1):
        self.H = len(grid)
        self.W = len(grid[0])
        self.grid = grid
        self.state = deepcopy(state) if state else [[None] * self.W for _ in range(self.H)]
        self.max_components = max_components
        self.solutions: List[List[List[Optional[int]]]] = []

    def allowed(self, r: int, c: int) -> List[int]:
        options = [0]
        can_be_black = True
        for nr, nc in neighbors_orth(self.H, self.W, r, c):
            if self.state[nr][nc] == 1:
                can_be_black = False
                break
        if can_be_black:
            options.append(1)
        return options

    def find_empty(self) -> Optional[Tuple[int, int]]:
        for r in range(self.H):
            for c in range(self.W):
                if self.state[r][c] is None:
                    return r, c
        return None

    def valid_partial(self, r: int, c: int) -> bool:
        H, W = self.H, self.W
        val = self.state[r][c]

        if val == 1:
            for nr, nc in neighbors_orth(H, W, r, c):
                if self.state[nr][nc] == 1:
                    return False
        else:
            row_vals = set()
            for col in range(W):
                if self.state[r][col] == 0:
                    v = self.grid[r][col]
                    if v in row_vals:
                        return False
                    row_vals.add(v)

            col_vals = set()
            for row in range(H):
                if self.state[row][c] == 0:
                    v = self.grid[row][c]
                    if v in col_vals:
                        return False
                    col_vals.add(v)
        return True

    def check_components(self) -> bool:
        binary_grid = [[1] * self.W for _ in range(self.H)]
        for r in range(self.H):
            for c in range(self.W):
                if self.state[r][c] == 0 or self.state[r][c] is None:
                    binary_grid[r][c] = 0

        return count_connected_components(binary_grid) <= self.max_components

    def valid_full(self) -> bool:
        H, W = self.H, self.W
        white_map = [[1] * W for _ in range(H)]
        for r in range(H):
            for c in range(W):
                if self.state[r][c] == 0:
                    white_map[r][c] = 0
        return count_connected_components(white_map) <= self.max_components

    def solve(self, need: int = 1):
        def backtrack():
            if need > 0 and len(self.solutions) >= need:
                return

            if not self.check_components():
                return

            pos = self.find_empty()
            if not pos:
                if self.valid_full():
                    self.solutions.append(deepcopy(self.state))
                return

            r, c = pos
            for val in self.allowed(r, c):
                self.state[r][c] = val
                if self.valid_partial(r, c):
                    backtrack()
                self.state[r][c] = None

        backtrack()
        return self.solutions


def display_grid(grid: List[List[int]], state=None):
    H = len(grid)
    W = len(grid[0])
    for r in range(H):
        row_str = []
        for c in range(W):
            if state and state[r][c] == 1:
                row_str.append('██')
            else:
                row_str.append(f"{grid[r][c]:2d}")
        print(' '.join(row_str))


def display_solution(grid, state, idx=1, max_components=1):
    print(f"\n--- Решение {idx} ---")
    display_grid(grid, state)

    H = len(grid)
    W = len(grid[0])
    white_count = sum(1 for r in range(H) for c in range(W) if state[r][c] == 0)
    black_count = sum(1 for r in range(H) for c in range(W) if state[r][c] == 1)

    print(f"Белых клеток: {white_count}, Черных клеток: {black_count}")

    white_map = [[1] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if state[r][c] == 0:
                white_map[r][c] = 0

    components = count_connected_components(white_map)
    print(f"Компонент связности белых клеток: {components}")

    if components > max_components:
        print(f"⚠  Нарушение: {components} > {max_components}")
    else:
        print(f"✓  Условие выполнено")


def main():
    parser = argparse.ArgumentParser(
        description='Решатель головоломки Hitori с ограничением M на компоненты связности',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--file", type=str, required=True)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--find", type=int, default=None)
    parser.add_argument("--M", type=int, default=1)

    args = parser.parse_args()

    if args.M < 0:
        print("Ошибка: --M должно быть неотрицательным")
        return

    if args.all:
        need = 0
    elif args.find is not None:
        if args.find < 0:
            print("Ошибка: --find должно быть неотрицательным")
            return
        need = args.find
    else:
        need = 1

    try:
        file_M = None
        with open(args.file, 'r') as f:
            grid = []
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line.startswith('# M='):
                    try:
                        file_M = int(line.split('=')[1])
                    except:
                        pass
                elif line and not line.startswith('#'):
                    try:
                        row = list(map(int, line.split()))
                        grid.append(row)
                    except ValueError as e:
                        print(f"Ошибка в строке {line_num}: {e}")
                        return

        if file_M is not None:
            print(f"Найдено M={file_M} в файле")
            args.M = file_M

    except FileNotFoundError:
        print(f"Файл '{args.file}' не найден")
        return

    is_valid, message = validate_grid(grid)
    if not is_valid:
        print(f"Ошибка: {message}")
        return

    print("=" * 50)
    print("Входная головоломка:")
    display_grid(grid)
    print(f"\nРазмер: {len(grid)}x{len(grid[0])}")
    print(f"Максимум компонент связности M: {args.M}")
    print("=" * 50)

    solver = HitoriSolver(grid, max_components=args.M)

    print("\nПоиск решений...")
    solutions = solver.solve(need)

    if not solutions:
        print("\nРешений нет")
        return

    print(f"\nНайдено решений: {len(solutions)}")
    print("=" * 50)

    for idx, sol in enumerate(solutions, 1):
        display_solution(grid, sol, idx, max_components=args.M)
        if idx < len(solutions):
            print("-" * 30)


if __name__ == "__main__":
    main()
