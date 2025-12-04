# Решатель Hitori

Консольный решатель Hitori для прямоугольной сетки чисел.  
Цель: закрасить клетки так, чтобы одинаковые числа в строках/столбцах оставались только в белых клетках, черные клетки не соприкасались, а все белые были связны.

**Запуск:**
```bash
python solver.py --file puzzle.txt --find 1
python solver.py --file puzzle.txt --find 0 --save-state state.json
python solver.py --file puzzle.txt --resume state.json
```
