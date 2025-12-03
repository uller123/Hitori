import copy
import sys


def print_grid(grid):
    """Печать сетки Hitori"""
    for row in grid:
        print(' '.join(str(cell) for cell in row))
    print()

def valid_input(grid):
    """Проверка корректности входа"""
    if not grid:
        return False
    n = len(grid)
    m = len(grid[0])
    for row in grid:
        if len(row) != m:
            return False
        for val in row:
            if not isinstance(val, int):
                return False
    return True

def neighbors(r, c, n, m):
    """Соседи для Hitori (по горизонтали и вертикали)"""
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < n and 0 <= nc < m:
            yield nr, nc


def is_valid_hitori(grid, black_cells):
    """Проверка сетки на корректность правил Hitori"""
    n, m = len(grid), len(grid[0])
    
    # 1. Не должно быть одинаковых чисел в строке/столбце (если они белые)
    for r in range(n):
        seen = {}
        for c in range(m):
            if (r,c) not in black_cells:
                if grid[r][c] in seen:
                    return False
                seen[grid[r][c]] = True
    for c in range(m):
        seen = {}
        for r in range(n):
            if (r,c) not in black_cells:
                if grid[r][c] in seen:
                    return False
                seen[grid[r][c]] = True
                
    # 2. Черные клетки не должны быть смежными
    for r, c in black_cells:
        for nr, nc in neighbors(r,c,n,m):
            if (nr, nc) in black_cells:
                return False
    
    # 3. Все белые клетки должны быть соединены (M=1)
    visited = set()
    def dfs(r, c):
        if (r,c) in visited or (r,c) in black_cells:
            return
        visited.add((r,c))
        for nr, nc in neighbors(r,c,n,m):
            dfs(nr, nc)
    
    # Найдем первую белую клетку
    start = None
    for r in range(n):
        for c in range(m):
            if (r,c) not in black_cells:
                start = (r,c)
                break
        if start:
            break
    if start:
        dfs(*start)
        # Проверим, все белые клетки посещены
        for r in range(n):
            for c in range(m):
                if (r,c) not in black_cells and (r,c) not in visited:
                    return False

    return True


def solve_hitori(grid):
    n, m = len(grid), len(grid[0])
    solutions = []

    def backtrack(r=0, c=0, black_cells=set()):
        # Если дошли до конца сетки, проверяем полные правила
        if r == n:
            if is_valid_hitori(grid, black_cells):
                solutions.append(copy.deepcopy(black_cells))
            return

        nr, nc = (r, c+1) if c+1 < m else (r+1, 0)

        # Вариант 1: клетка белая
        backtrack(nr, nc, black_cells)

        # Вариант 2: клетка черная
        black_cells.add((r, c))
        # Проверка только для соседних черных (частичная проверка)
        if is_valid_partial(grid, black_cells, r, c):
            backtrack(nr, nc, black_cells)
        black_cells.remove((r, c))

    def is_valid_partial(grid, black_cells, r, c):
        """Быстрая проверка: только соседние черные клетки"""
        n, m = len(grid), len(grid[0])
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < n and 0 <= nc < m:
                if (nr, nc) in black_cells:
                    return False
        return True

    backtrack()
    return solutions



def main():
    print("Введите сетку Hitori через пробелы (пустая строка для конца ввода):")
    grid = []
    while True:
        line = input()
        if line.strip() == "":
            break
        row = [int(x) for x in line.split()]
        grid.append(row)
    
    if not valid_input(grid):
        print("Некорректный ввод.")
        sys.exit(1)
    
    solutions = solve_hitori(grid)
    if not solutions:
        print("Решений нет.")
    else:
        print(f"Найдено {len(solutions)} решение(й):")
        for sol in solutions:
            print_grid([['B' if (r,c) in sol else grid[r][c] for c in range(len(grid[0]))] for r in range(len(grid))])

if __name__ == "__main__":
    main()
