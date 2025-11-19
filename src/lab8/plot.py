
class Plot:
    def __init__(self, f=lambda x, y: (x*x+y*y), cut_off=((-100, 100), (-100, 100)), pivot=(300, 300, 300), number_of_points=100):
        self.cut_off = cut_off
        self.pivot = pivot
        self.f = f
        self.render(number_of_points)

    def render(self, n):
        self.grid = [[0]*n for _ in range(n)]
        y = self.cut_off[1][0]
        Δx = (self.cut_off[0][1] - self.cut_off[0][0]) / n
        Δy = (self.cut_off[1][1] - self.cut_off[1][0]) / n
        for i in range(n):
            y += Δy
            x = self.cut_off[0][0]
            for j in range(n):
                x += Δx
                self.grid[i][j] = self.f(x, y)

    def export(self, fname='export.obj'):
        n = len(self.grid)
        x0 = self.cut_off[0][0]
        y0 = self.cut_off[1][0]
        Δx = (self.cut_off[0][1] - self.cut_off[0][0]) / n
        Δy = (self.cut_off[1][1] - self.cut_off[1][0]) / n

        lines = []

        # 1) вершины 🏔️🏔️
        for i in range(n):
            y = y0 + i*Δy
            for j in range(n):
                x = x0 + j*Δx
                z = self.grid[i][j]
                lines.append(f"v {x} {y} {z}")

        # 2) фейсы 😶😶
        def idx(i,j): return i*n + j + 1

        for i in range(n-1):
            for j in range(n-1):
                lines.append(f"f {idx(i,j)} {idx(i+1,j)} {idx(i,j+1)}")
                lines.append(f"f {idx(i+1,j)} {idx(i+1,j+1)} {idx(i,j+1)}")

        obj = "\n".join(lines)
        with open(fname, "w") as f:
            f.write(obj)

if __name__ == '__main__':
    Plot(number_of_points=4).export()
