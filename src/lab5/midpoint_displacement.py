
import random

class MountainMirthMachine:
    def __init__(self, base_points):
        self.roughness = 0.5  # насколько сильно уменьшается амплитуда
        self.displacement = 100  # начальная амплитуда

        self.history = [ base_points ]

    def steps(self):
        return len(self.history)

    def current_displacement(self, step):
        return self.displacement * (self.roughness ** (step-1))

    def midpoint_displacement(self, points):
        # чем больше шаг тем меньше displacement ☝
        Δ = self.current_displacement(self.steps())
        
        res = []
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            mid_y += random.uniform(-Δ, +Δ)
            res.append( (x1, y1) )
            res.append( (mid_x, mid_y) )
        res.append(points[-1])
        return res

    def get_state(self, step):
        while step > self.steps():
            # обновляем пока не дойдем до нужной итерации
            self.history.append(self.midpoint_displacement(self.history[-1]))
        # нумерация с 1
        return self.history[step-1]
