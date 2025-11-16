import pico2d as p2
import random
import math

from .. import framework
from ..state_machine import StateMachine

# ========== Idle State ==========
class Idle:
    images = None

    def __init__(self, cat):
        self.cat = cat

        if Idle.images is None:
            Idle.images = []
            try:
                for i in range(6):  # Cat_Assassin_Idle0 ~ Idle5
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Assassin/character/Cat_Assassin_Idle{i}.png')
                    Idle.images.append(img)
                print(f"[CatAssassin Idle] Loaded {len(Idle.images)} images")
            except Exception as e:
                print(f"[CatAssassin Idle] Failed to load images: {e}")
                Idle.images = []

        self.cat.frame = 0
        self.cat.animation_speed = 10  # frames per second
        self.cat.animation_time = 0

    def enter(self, e):
        self.cat.frame = 0
        self.cat.animation_time = 0

    def exit(self, e):
        pass

    def do(self):
        # Update animation
        self.cat.animation_time += framework.get_delta_time()
        if self.cat.animation_time >= 1.0 / self.cat.animation_speed:
            self.cat.frame = (self.cat.frame + 1) % len(Idle.images)
            self.cat.animation_time = 0

        # AI: Check if player is nearby and chase
        # TODO: Implement Chase state before enabling this
        # if self.cat.world and self.cat.world.get('player'):
        #     player = self.cat.world['player']
        #     dx, dy = player.x - self.cat.x, player.y - self.cat.y
        #     dist = math.sqrt(dx**2 + dy**2)
        #
        #     # If player is close, start chasing
        #     if dist < 500:  # Detection range
        #         self.cat.state_machine.handle_state_event(('DETECT_PLAYER', None))

    def draw(self):
        if Idle.images and len(Idle.images) > 0:
            Idle.images[self.cat.frame].draw(self.cat.x, self.cat.y,
                                             Idle.images[self.cat.frame].w * self.cat.scale,
                                             Idle.images[self.cat.frame].h * self.cat.scale)

# ========== Event Predicates ==========
def detect_player(e):
    return e[0] == 'DETECT_PLAYER'

def lose_player(e):
    return e[0] == 'LOSE_PLAYER'

# Shuriken (projectile)
class Shuriken:
    images = None

    def __init__(self, x, y, target_x, target_y):
        if Shuriken.images is None:
            Shuriken.images = []
            try:
                for i in range(8):  # Cat_Assassin_Shuriken0 ~ Shuriken7
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Assassin/FX/Cat_Assassin_Shuriken{i}.png')
                    Shuriken.images.append(img)
            except Exception as e:
                print(f"[Shuriken] Failed to load images: {e}")
                # Create a dummy image list to prevent crashes
                Shuriken.images = []

        self.x, self.y = x, y
        self.speed = 400
        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 10

        # Calculate direction vector
        dx, dy = target_x - self.x, target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            self.dx = dx / dist
            self.dy = dy / dist
        else: # Failsafe
            self.dx, self.dy = 0, -1

    def update(self):
        self.x += self.dx * self.speed * framework.get_delta_time()
        self.y += self.dy * self.speed * framework.get_delta_time()

        # Update animation
        self.animation_time += framework.get_delta_time()
        if self.animation_time >= 1.0 / self.animation_speed:
            if len(Shuriken.images) > 0:
                self.frame = (self.frame + 1) % len(Shuriken.images)
            self.animation_time = 0

        # Remove shuriken if it goes off-screen
        if self.x < 0 or self.x > p2.get_canvas_width() or self.y < 0 or self.y > p2.get_canvas_height():
            return False # Signal to remove
        return True

    def draw(self):
        if Shuriken.images and len(Shuriken.images) > 0:
            Shuriken.images[self.frame].draw(self.x, self.y)

# CatAssassin (monster)
class CatAssassin:
    def __init__(self, x = 800, y = 450):  # Use default values instead of main.window_width
        self.x, self.y = x, y
        self.speed = 100
        self.scale = 3.0
        self.world = None # Will be set from play_mode

        self.attack_cooldown = 2.0 # Attack every 2 seconds
        self.attack_timer = random.uniform(0, self.attack_cooldown)

        # Animation variables
        self.frame = 0
        self.animation_speed = 10
        self.animation_time = 0

        # State machine setup with rules
        # Create state instances
        self.IDLE = Idle(self)
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {},
            }
        )

    def update(self):
        self.state_machine.update()
        return True

    def draw(self):
        self.state_machine.draw()

    def attack(self, target):
        if self.world:
            shuriken = Shuriken(self.x, self.y, target.x, target.y)
            self.world['effects_front'].append(shuriken)
            print(f"CatAssassin at ({int(self.x)}, {int(self.y)}) attacks!")

    def handle_event(self, e):
        pass
