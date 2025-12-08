#!/usr/bin/env python3
import argparse
from copy import deepcopy
from typing import List, Tuple, Optional, Set
from collections import deque


# ---------------- utils ----------------
def neighbors_orth(H: int, W: int, r: int, c: int):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W:
            yield nr, nc


def count_connected_components(grid: List[List[int]]) -> int:
    """Считает количество компонент связности белых клеток (0 - белая, 1 - черная)."""
    H = len(grid)
    W = len(grid[0])
    visited = [[False] * W for _ in range(H)]
    components = 0

    for r in range(H):
        for c in range(W):
            if grid[r][c] == 0 and not visited[r][c]:
                # Нашли новую компоненту
                components += 1
                # BFS для всей компоненты
                queue = deque([(r, c)])
                visited[r][c] = True

                while queue:
                    cr, cc = queue.popleft()
                    for nr, nc in neighbors_orth(H, W, cr, cc):
                        if grid[nr][nc] == 0 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            queue.append((nr, nc))

    return components


def white_connected(grid: List[List[int]]) -> bool:
    """Проверяет, что белые клетки образуют одну компоненту связности."""
    return count_connected_components(grid) == 1


def validate_grid(grid: List[List[int]]) -> Tuple[bool, str]:
    """Проверяет корректность входной сетки."""
    if not grid:
        return False, "Сетка пуста"

    H = len(grid)
    W = len(grid[0])

    # Проверка прямоугольности
    for r, row in enumerate(grid):
        if len(row) != W:
            return False, f"Строка {r} имеет длину {len(row)}, ожидалось {W}"

    # Проверка значений (должны быть положительными целыми)
    for r in range(H):
        for c in range(W):
            val = grid[r][c]
            if not isinstance(val, int) or val <= 0:
                return False, f"Неверное значение в ({r},{c}): {val}. Ожидалось положительное целое число"

    # Проверка размера
    if H < 2 or W < 2:
        return False, "Сетка должна быть минимум 2x2"

    return True, "OK"


# ---------------- solver ----------------
class HitoriSolver:
    def __init__(self, grid: List[List[int]],
                 state: Optional[List[List[Optional[int]]]] = None,
                 max_components: int = 1):  # Новый параметр
        self.H = len(grid)
        self.W = len(grid[0])
        self.grid = grid
        self.state = deepcopy(state) if state else [[None] * self.W for _ in range(self.H)]
        self.max_components = max_components
        self.solutions: List[List[List[Optional[int]]]] = []

    def allowed(self, r: int, c: int) -> List[int]:
        """Возвращает возможные значения (0-белая, 1-черная) для клетки."""
        options = [0]

        # Проверка на смежные черные клетки
        can_be_black = True
        for nr, nc in neighbors_orth(self.H, self.W, r, c):
            if self.state[nr][nc] == 1:
                can_be_black = False
                break

        if can_be_black:
            options.append(1)

        return options

    def find_empty(self) -> Optional[Tuple[int, int]]:
        """Находит первую неопределенную клетку."""
        for r in range(self.H):
            for c in range(self.W):
                if self.state[r][c] is None:
                    return r, c
        return None

    def valid_partial(self, r: int, c: int) -> bool:
        """Проверяет частичное решение после установки клетки (r,c)."""
        H, W = self.H, self.W
        val = self.state[r][c]

        if val == 1:  # Черная клетка
            # Проверка смежных черных
            for nr, nc in neighbors_orth(H, W, r, c):
                if self.state[nr][nc] == 1:
                    return False
        else:  # Белая клетка
            # Проверка уникальности в строке
            row_vals = set()
            for col in range(W):
                if self.state[r][col] == 0:  # Белая
                    v = self.grid[r][col]
                    if v in row_vals:
                        return False
                    row_vals.add(v)

            # Проверка уникальности в столбце
            col_vals = set()
            for row in range(H):
                if self.state[row][c] == 0:  # Белая
                    v = self.grid[row][c]
                    if v in col_vals:
                        return False
                    col_vals.add(v)

        return True

    def check_components(self) -> bool:
        """Проверяет количество компонент связности для текущего состояния."""
        # Создаем бинарную сетку (0 - белая, 1 - черная или None)
        binary_grid = [[1] * self.W for _ in range(self.H)]
        for r in range(self.H):
            for c in range(self.W):
                if self.state[r][c] == 0:  # Белая
                    binary_grid[r][c] = 0
                elif self.state[r][c] is None:  # Неопределенная
                    # Неопределенные клетки считаем как белые для проверки связности
                    binary_grid[r][c] = 0

        components = count_connected_components(binary_grid)
        return components <= self.max_components

    def valid_full(self) -> bool:
        """Проверяет полное решение."""
        H, W = self.H, self.W

        # Проверка связности белых клеток
        white_map = [[1] * W for _ in range(H)]
        for r in range(H):
            for c in range(W):
                if self.state[r][c] == 0:
                    white_map[r][c] = 0

        components = count_connected_components(white_map)
        if components > self.max_components:
            return False

        return True

    def solve(self, need: int = 1) -> List[List[List[Optional[int]]]]:
        """Находит решения (все или N)."""

        def backtrack():
            if need > 0 and len(self.solutions) >= need:
                return

            # Проверка связности на частичном решении
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


# ---------------- CUI ----------------
def display_grid(grid: List[List[int]], state: Optional[List[List[Optional[int]]]] = None):
    """Отображает сетку Hitori."""
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


def display_solution(grid: List[List[int]], state: List[List[Optional[int]]],
                     idx: int = 1, max_components: int = 1):
    """Отображает одно решение."""
    print(f"\n--- Решение {idx} ---")
    display_grid(grid, state)

    H = len(grid)
    W = len(grid[0])

    # Подсчет статистики
    white_count = sum(1 for r in range(H) for c in range(W) if state[r][c] == 0)
    black_count = sum(1 for r in range(H) for c in range(W) if state[r][c] == 1)

    print(f"Белых клеток: {white_count}, Черных клеток: {black_count}")

    # Подсчет компонент связности
    white_map = [[1] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if state[r][c] == 0:
                white_map[r][c] = 0

    components = count_connected_components(white_map)
    print(f"Компонент связности белых клеток: {components}")

    # Проверка ограничения M
    if components > max_components:
        print(f"⚠  Нарушение! Компонент ({components}) > M ({max_components})")
    else:
        print(f"✓  Условие выполнено: {components} ≤ {max_components}")


def main():
    parser = argparse.ArgumentParser(
        description='Решатель головоломки Hitori с ограничением M на компоненты связности',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python solver.py --file puzzle.txt                     # M=1 (по умолчанию)
  python solver.py --file puzzle.txt --M 1              # Классический Hitori
  python solver.py --file puzzle.txt --M 2              # Допускаем 2 компоненты
  python solver.py --file puzzle.txt --M 0              # Без ограничений
  python solver.py --file puzzle.txt --M 3 --all        # Все решения с M=3
  python solver.py --file puzzle.txt --M 2 --find 5     # 5 решений с M=2
        """
    )
    parser.add_argument("--file", type=str, required=True,
                        help="Файл с головоломкой (каждая строка - числа через пробел)")
    parser.add_argument("--all", action="store_true",
                        help="Найти все решения")
    parser.add_argument("--find", type=int, default=None,
                        help="Найти N решений (0 для всех, не указано - одно)")
    parser.add_argument("--M", type=int, default=1,
                        help="Максимальное количество компонент связности (по умолчанию 1)")

    args = parser.parse_args()

    # Проверка аргумента M
    if args.M < 0:
        print("Ошибка: значение --M должно быть неотрицательным")
        return

    # Определение количества решений для поиска
    if args.all:
        need = 0
    elif args.find is not None:
        if args.find == 0:
            need = 0
        elif args.find > 0:
            need = args.find
        else:
            print("Ошибка: значение --find должно быть неотрицательным")
            return
    else:
        need = 1

    # Чтение сетки
    try:
        file_M = None  # M из файла (если указано)
        with open(args.file, 'r') as f:
            grid = []
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line.startswith('# M='):
                    # Извлекаем M из комментария
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

        # Если M указано в файле, используем его (приоритет над --M)
        if file_M is not None:
            print(f"Найдено значение M={file_M} в файле")
            args.M = file_M
    except FileNotFoundError:
        print(f"Файл '{args.file}' не найден")
        return
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    # Валидация сетки
    is_valid, message = validate_grid(grid)
    if not is_valid:
        print(f"Ошибка в входных данных: {message}")
        return

    print("=" * 50)
    print("Входная головоломка:")
    display_grid(grid)
    print(f"\nРазмер: {len(grid)}x{len(grid[0])}")
    print(f"Максимум компонент связности M: {args.M}")
    print("=" * 50)

    # Решение
    solver = HitoriSolver(grid, max_components=args.M)

    if need == 0:
        print("\nПоиск всех решений...")
    else:
        print(f"\nПоиск {need} решения(ий)...")

    solutions = solver.solve(need)

    # Вывод результатов
    if not solutions:
        print("\nРешений нет")
        return

    if need == 0:
        print(f"\nНайдено всего решений: {len(solutions)}")
    else:
        print(f"\nНайдено решение(й): {len(solutions)}")
        if len(solutions) < need:
            print(f"Примечание: запрошено {need}, но найдено только {len(solutions)}")

    print("=" * 50)
    for idx, sol in enumerate(solutions, 1):
        display_solution(grid, sol, idx, max_components=args.M)  # ← ВОТ ТУТ передаем M
        if idx < len(solutions):
            print("-" * 30)

    if need == 0:
        print("\n" + "=" * 50)
        print("Поиск всех решений завершен.")


if __name__ == "__main__":
    main()