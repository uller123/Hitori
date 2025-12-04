#!/usr/bin/env python3
import argparse
from copy import deepcopy
import json

# ---------------- utils ----------------

def neighbors_orth(H,W,r,c):
    for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
        nr,nc = r+dr, c+dc
        if 0 <= nr < H and 0 <= nc < W:
            yield nr,nc

def white_connected(grid):
    H = len(grid)
    W = len(grid[0])
    visited = [[False]*W for _ in range(H)]
    found = False
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 0:
                sr, sc = r, c
                found = True
                break
        if found: break
    if not found:
        return True
    stack = [(sr, sc)]
    visited[sr][sc] = True
    count = 1
    while stack:
        r,c = stack.pop()
        for nr,nc in neighbors_orth(H,W,r,c):
            if not visited[nr][nc] and grid[nr][nc]==0:
                visited[nr][nc]=True
                stack.append((nr,nc))
                count+=1
    total_white = sum(row.count(0) for row in grid)
    return count==total_white

# ---------------- solver ----------------

class HitoriSolver:
    def __init__(self, grid, state=None):
        self.H = len(grid)
        self.W = len(grid[0])
        self.grid = deepcopy(grid)
        if state:
            self.state = deepcopy(state)
        else:
            self.state = [[None]*self.W for _ in range(self.H)]

    def allowed(self,r,c):
        for nr,nc in neighbors_orth(self.H,self.W,r,c):
            if self.state[nr][nc]==1:
                return [0]
        return [0,1]

    def find_empty(self):
        for r in range(self.H):
            for c in range(self.W):
                if self.state[r][c] is None:
                    return r,c
        return None

    def valid(self):
        H,W = self.H,self.W
        for r in range(H):
            for c in range(W):
                if self.state[r][c]==1:
                    for nr,nc in neighbors_orth(H,W,r,c):
                        if self.state[nr][nc]==1:
                            return False
        for r in range(H):
            seen=set()
            for c in range(W):
                if self.state[r][c]==0:
                    val=self.grid[r][c]
                    if val in seen:
                        return False
                    seen.add(val)
        for c in range(W):
            seen=set()
            for r in range(H):
                if self.state[r][c]==0:
                    val=self.grid[r][c]
                    if val in seen:
                        return False
                    seen.add(val)
        if not white_connected([[0 if self.state[r][c]==0 else 1 for c in range(W)] for r in range(H)]):
            return False
        return True

    def solve(self, need=1, save_state=None):
        solutions=[]
        def backtrack():
            if need!=0 and len(solutions)>=need:
                return
            pos=self.find_empty()
            if not pos:
                if self.valid():
                    solutions.append(deepcopy(self.state))
                    if save_state:
                        with open(save_state,"w") as f:
                            json.dump({"state": self.state}, f)
                return
            r,c=pos
            for val in self.allowed(r,c):
                self.state[r][c]=val
                backtrack()
                self.state[r][c]=None
                if save_state:
                    with open(save_state,"w") as f:
                        json.dump({"state": self.state}, f)
        backtrack()
        return solutions

# ---------------- CLI ----------------

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--file",type=str,help="файл с числами")
    parser.add_argument("--find",type=int,default=1,help="сколько решений искать, 0=все")
    parser.add_argument("--save-state",type=str,help="сохранение прогресса поиска")
    parser.add_argument("--resume",type=str,help="возобновление из state.json")
    args=parser.parse_args()

    grid=[]
    with open(args.file) as f:
        for line in f:
            if line.strip():
                grid.append(list(map(int,line.strip().split())))

    state=None
    if args.resume:
        with open(args.resume) as f:
            state=json.load(f)["state"]

    solver=HitoriSolver(grid,state)
    sols=solver.solve(args.find, save_state=args.save_state)

    if not sols:
        print("Решений нет")
        return

    print(f"Найдено {len(sols)} решение(й)")
    for idx,s in enumerate(sols,1):
        print(f"\n--- Решение {idx} ---")
        for r in range(solver.H):
            row=[]
            for c in range(solver.W):
                row.append('█' if s[r][c]==1 else str(grid[r][c]))
            print(' '.join(row))

if __name__=="__main__":
    main()
