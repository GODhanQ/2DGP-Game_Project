class Goblin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        print(f"Goblin created at ({x}, {y})")

    def update(self):
        # Monster logic here
        return True

    def draw(self):
        # Drawing logic here
        pass

    def handle_event(self, e):
        pass

