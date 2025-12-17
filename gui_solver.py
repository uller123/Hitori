#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import sys
import os

# Импортируем логику из вашего решателя
from solver import (
    neighbors_orth,
    count_connected_components,
    validate_grid,
    HitoriSolver,
    display_grid as cli_display_grid
)


class HitoriCell(tk.Canvas):
    """Виджет для отображения одной клетки Hitori"""

    def __init__(self, parent, value, state=0, **kwargs):
        size = 50
        super().__init__(parent, width=size, height=size,
                         relief=tk.RAISED, bd=2, **kwargs)
        self.value = value
        self.state = state  # 0 - белая, 1 - черная
        self.size = size
        self.draw()

    def draw(self):
        self.delete("all")

        if self.state == 0:  # Белая клетка
            self.config(bg='white')
            self.create_text(self.size // 2, self.size // 2,
                             text=str(self.value),
                             font=('Arial', 14, 'bold'))
        else:  # Черная клетка
            self.config(bg='black')
            # Белый текст на черном фоне
            self.create_text(self.size // 2, self.size // 2,
                             text=str(self.value),
                             font=('Arial', 14, 'bold'),
                             fill='white')


class HitoriGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hitori Solver - GUI")
        self.root.geometry("1200x800")

        # Переменные
        self.grid = []
        self.solutions = []
        self.current_solution = 0
        self.solver = None
        self.solving = False
        self.stop_solving = False

        # Настройка стилей
        self.setup_styles()

        # Создание интерфейса
        self.create_widgets()

    def setup_styles(self):
        """Настройка стилей для виджетов"""
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 10))

    def create_widgets(self):
        """Создание всех виджетов интерфейса"""
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Конфигурация сетки
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Панель управления (сверху)
        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Кнопки управления
        ttk.Button(control_frame, text="Загрузить файл",
                   command=self.load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Проверить сетку",
                   command=self.validate_grid).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Найти 1 решение",
                   command=lambda: self.solve_puzzle(1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Найти N решений",
                   command=self.find_n_solutions).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Найти все решения",
                   command=lambda: self.solve_puzzle(0)).pack(side=tk.LEFT, padx=5)

        # Кнопки навигации (будем обновлять состояние)
        self.btn_prev = ttk.Button(control_frame, text="← Предыдущее",
                                   command=self.prev_solution, state='disabled')
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        self.btn_next = ttk.Button(control_frame, text="Следующее →",
                                   command=self.next_solution, state='disabled')
        self.btn_next.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Очистить",
                   command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # Панель параметров
        param_frame = ttk.Frame(control_frame)
        param_frame.pack(side=tk.LEFT, padx=20)

        ttk.Label(param_frame, text="M (компоненты):").pack(side=tk.LEFT)
        self.m_var = tk.StringVar(value="1")
        ttk.Spinbox(param_frame, from_=0, to=10, textvariable=self.m_var,
                    width=5).pack(side=tk.LEFT, padx=5)

        ttk.Label(param_frame, text="N решений:").pack(side=tk.LEFT, padx=(10, 0))
        self.n_var = tk.StringVar(value="1")
        ttk.Spinbox(param_frame, from_=1, to=1000, textvariable=self.n_var,
                    width=5).pack(side=tk.LEFT, padx=5)

        # Фрейм для сетки
        grid_frame = ttk.LabelFrame(main_frame, text="Сетка Hitori", padding="10")
        grid_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Контейнер для клеток
        self.grid_container = tk.Frame(grid_frame)
        self.grid_container.pack()

        # Информационная панель
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding="10")
        info_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S),
                        padx=(10, 0), pady=(0, 10))

        # Текстовое поле для информации
        self.info_text = scrolledtext.ScrolledText(info_frame, width=40, height=20)
        self.info_text.pack(fill=tk.BOTH, expand=True)

        # Панель статуса
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.grid(row=2, column=0, columnspan=2,
                               sticky=(tk.W, tk.E, tk.S), pady=(10, 0))

        # Прогресс бар
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Статус
        self.status_label = ttk.Label(self.status_frame, text="Готов",
                                      style='Status.TLabel')
        self.status_label.pack(side=tk.RIGHT)

    def log(self, message: str):
        """Добавление сообщения в информационное окно"""
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.root.update_idletasks()

    def set_status(self, message: str):
        """Установка статуса"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def load_file(self):
        """Загрузка файла с головоломкой"""
        filename = filedialog.askopenfilename(
            title="Выберите файл с головоломкой",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if not filename:
            return

        try:
            with open(filename, 'r') as f:
                grid = []
                file_M = None

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
                            messagebox.showerror("Ошибка",
                                                 f"Ошибка в строке {line_num}: {e}")
                            return

                # Валидация
                is_valid, message = validate_grid(grid)
                if not is_valid:
                    messagebox.showerror("Ошибка", message)
                    return

                self.grid = grid

                if file_M is not None:
                    self.m_var.set(str(file_M))
                    self.log(f"Загружено M={file_M} из файла")

                self.display_grid()
                self.log(f"Загружен файл: {filename}")
                self.log(f"Размер сетки: {len(grid)}x{len(grid[0])}")
                self.solutions = []
                self.current_solution = 0
                self.update_navigation_buttons()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке файла: {e}")

    def display_grid(self, state=None):
        """Отображение сетки"""
        # Очистка предыдущей сетки
        for widget in self.grid_container.winfo_children():
            widget.destroy()

        if not self.grid:
            return

        H = len(self.grid)
        W = len(self.grid[0])

        # Создание новой сетки
        for r in range(H):
            row_frame = tk.Frame(self.grid_container)
            row_frame.pack()
            for c in range(W):
                cell_state = 0
                if state:
                    cell_state = state[r][c] if state[r][c] is not None else 0

                cell = HitoriCell(row_frame, self.grid[r][c], cell_state)
                cell.pack(side=tk.LEFT)

    def validate_grid(self):
        """Проверка корректности сетки"""
        if not self.grid:
            messagebox.showwarning("Предупреждение", "Сетка не загружена")
            return

        is_valid, message = validate_grid(self.grid)
        if is_valid:
            messagebox.showinfo("Проверка", "Сетка корректна!")
            self.log("✓ Сетка прошла проверку")
        else:
            messagebox.showerror("Ошибка", message)
            self.log(f"✗ Ошибка проверки: {message}")

    def find_n_solutions(self):
        """Найти N решений (пользовательский ввод)"""
        try:
            n = int(self.n_var.get())
            if n <= 0:
                raise ValueError
        except:
            messagebox.showerror("Ошибка", "Введите положительное число N")
            return

        self.solve_puzzle(n)

    def solve_puzzle(self, need: int = None):
        """Запуск решения головоломки"""
        if not self.grid:
            messagebox.showwarning("Предупреждение", "Сетка не загружена")
            return

        if need is None:
            try:
                need = int(self.n_var.get())
                if need < 0:
                    raise ValueError
            except:
                messagebox.showerror("Ошибка", "Некорректное значение N")
                return

        try:
            M = int(self.m_var.get())
            if M < 0:
                raise ValueError
        except:
            messagebox.showerror("Ошибка", "Некорректное значение M")
            return

        # Сброс предыдущих решений
        self.solutions = []
        self.current_solution = 0

        # Запуск в отдельном потоке, чтобы не блокировать GUI
        self.stop_solving = False
        self.solving = True
        self.progress.start()
        self.set_status("Решение...")
        self.log(f"\nНачинаю решение... (M={M}, N={need})")

        thread = threading.Thread(
            target=self.solve_thread,
            args=(need, M),
            daemon=True
        )
        thread.start()

        # Периодическая проверка завершения
        self.check_solving_complete()

    def solve_thread(self, need: int, M: int):
        """Поток для решения головоломки"""
        try:
            solver = HitoriSolver(self.grid, max_components=M)
            self.solutions = solver.solve(need)
        except Exception as e:
            self.solutions = []
            self.log(f"Ошибка при решении: {e}")

    def check_solving_complete(self):
        """Проверка завершения решения"""
        if self.solving:
            if self.solutions or not threading.active_count() > 1:
                # Решение завершено
                self.solving = False
                self.stop_solving = False
                self.progress.stop()

                if self.solutions:
                    self.set_status(f"Найдено решений: {len(self.solutions)}")
                    self.log(f"✓ Найдено {len(self.solutions)} решений")
                    self.display_solution(0)
                else:
                    self.set_status("Решений нет")
                    self.log("✗ Решений не найдено")
                    messagebox.showinfo("Результат", "Решений не найдено")

                self.update_navigation_buttons()
            else:
                # Продолжаем ждать
                self.root.after(100, self.check_solving_complete)

    def display_solution(self, index: int):
        """Отображение конкретного решения"""
        if not self.solutions or index >= len(self.solutions):
            return

        self.current_solution = index
        solution = self.solutions[index]

        # Отображение сетки с решением
        self.display_grid(solution)

        # Вычисление статистики
        H = len(self.grid)
        W = len(self.grid[0])
        white_count = sum(1 for r in range(H) for c in range(W)
                          if solution[r][c] == 0)
        black_count = sum(1 for r in range(H) for c in range(W)
                          if solution[r][c] == 1)

        # Создание карты белых клеток для подсчета компонент
        white_map = [[1] * W for _ in range(H)]
        for r in range(H):
            for c in range(W):
                if solution[r][c] == 0:
                    white_map[r][c] = 0

        components = count_connected_components(white_map)
        M = int(self.m_var.get())

        # Логирование информации
        self.log(f"\nРешение {index + 1}/{len(self.solutions)}:")
        self.log(f"  Белых клеток: {white_count}")
        self.log(f"  Черных клеток: {black_count}")
        self.log(f"  Компонент связности: {components}")

        if components > M:
            self.log(f"  ⚠ Нарушение: {components} > M={M}")
        else:
            self.log(f"  ✓ Условие M={M} выполнено")

        # Обновление заголовка окна
        self.root.title(f"Hitori Solver - Решение {index + 1}/{len(self.solutions)}")

    def next_solution(self):
        """Переход к следующему решению"""
        if self.solutions and self.current_solution < len(self.solutions) - 1:
            self.display_solution(self.current_solution + 1)
            self.update_navigation_buttons()

    def prev_solution(self):
        """Переход к предыдущему решению"""
        if self.solutions and self.current_solution > 0:
            self.display_solution(self.current_solution - 1)
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Обновление состояния кнопок навигации"""
        has_solutions = len(self.solutions) > 0
        can_next = has_solutions and self.current_solution < len(self.solutions) - 1
        can_prev = has_solutions and self.current_solution > 0

        state_next = 'normal' if can_next else 'disabled'
        state_prev = 'normal' if can_prev else 'disabled'

        self.btn_next.config(state=state_next)
        self.btn_prev.config(state=state_prev)

    def clear_all(self):
        """Очистка всего"""
        self.grid = []
        self.solutions = []
        self.current_solution = 0

        # Очистка отображения
        for widget in self.grid_container.winfo_children():
            widget.destroy()

        self.info_text.delete(1.0, tk.END)
        self.set_status("Готов")
        self.update_navigation_buttons()
        self.log("Очищено")
        self.root.title("Hitori Solver - GUI")

    def run(self):
        """Запуск GUI"""
        self.root.mainloop()


def main():
    """Точка входа для GUI"""
    app = HitoriGUI()
    app.run()


if __name__ == "__main__":
    main()