import pico2d as p2
import random
import math

from .. import framework
from ..state_machine import StateMachine
from ..projectile import Projectile

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
class Shuriken(Projectile):
    """수리검 발사체 - Projectile을 상속받음"""
    images = None

    def __init__(self, x, y, target_x, target_y):
        # 부모 클래스 초기화 (몬스터가 쏘는 투사체이므로 from_player=False)
        super().__init__(x, y, target_x, target_y, speed=400, from_player=False)

        if Shuriken.images is None:
            Shuriken.images = []
            try:
                for i in range(8):  # Cat_Assassin_Shuriken0 ~ Shuriken7
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Assassin/FX/Cat_Assassin_Shuriken{i}.png')
                    Shuriken.images.append(img)
            except Exception as e:
                print(f"[Shuriken] Failed to load images: {e}")
                Shuriken.images = []

        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 10

    def update(self):
        # 부모 클래스의 update 호출 (위치 업데이트 및 화면 밖 체크)
        if not super().update():
            return False

        # 애니메이션 업데이트
        self.animation_time += framework.get_delta_time()
        if self.animation_time >= 1.0 / self.animation_speed:
            if len(Shuriken.images) > 0:
                self.frame = (self.frame + 1) % len(Shuriken.images)
            self.animation_time = 0

        return True

    def draw(self):
        if Shuriken.images and len(Shuriken.images) > 0:
            Shuriken.images[self.frame].draw(self.x, self.y)

    def get_collision_box(self):
        """수리검의 충돌 박스 크기"""
        return (30, 30)

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

        # Collision box (히트박스 크기 설정)
        # Cat_Assassin_Idle 이미지 크기를 기준으로 설정
        self.collision_width = 15 * self.scale  # 대략적인 크기
        self.collision_height = 15 * self.scale

        # 무적시간 관련 변수
        self.invincible = False  # 무적 상태인지
        self.invincible_timer = 0.0  # 무적 시간 타이머
        self.invincible_duration = 0.3  # 무적 시간 지속 시간 (1초)

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
        # 무적시간 업데이트
        if self.invincible:
            self.invincible_timer -= framework.get_delta_time()
            if self.invincible_timer <= 0:
                self.invincible = False
                self.invincible_timer = 0.0

        self.state_machine.update()
        return True

    def draw(self):
        self.state_machine.draw()

        # Debug: Draw collision box
        cat_left = self.x - self.collision_width / 2
        cat_right = self.x + self.collision_width / 2
        cat_bottom = self.y - self.collision_height / 2
        cat_top = self.y + self.collision_height / 2
        p2.draw_rectangle(cat_left, cat_bottom, cat_right, cat_top)

    def attack(self, target):
        if self.world:
            shuriken = Shuriken(self.x, self.y, target.x, target.y)
            self.world['effects_front'].append(shuriken)
            print(f"CatAssassin at ({int(self.x)}, {int(self.y)}) attacks!")

    def handle_event(self, e):
        pass

    def check_collision_with_effect(self, effect):
        """공격 이펙트와의 충돌 감지

        Args:
            effect: VFX_Tier1_Sword_Swing 객체

        Returns:
            bool: 충돌 여부
        """
        # 무적 상태이면 충돌 무시
        if self.invincible:
            return False

        # 이펙트의 크기 계산 (이펙트는 회전된 이미지이므로 대략적인 범위 사용)
        if hasattr(effect, 'frames') and len(effect.frames) > 0:
            effect_img = effect.frames[min(effect.frame, len(effect.frames) - 1)]
            effect_width = effect_img.w * effect.scale_factor
            effect_height = effect_img.h * effect.scale_factor
        else:
            # 기본값
            effect_width = 200
            effect_height = 200

        # AABB (Axis-Aligned Bounding Box) 충돌 감지
        cat_left = self.x - self.collision_width / 2
        cat_right = self.x + self.collision_width / 2
        cat_bottom = self.y - self.collision_height / 2
        cat_top = self.y + self.collision_height / 2

        effect_left = effect.x - effect_width / 2
        effect_right = effect.x + effect_width / 2
        effect_bottom = effect.y - effect_height / 2
        effect_top = effect.y + effect_height / 2
        p2.draw_rectangle(effect_left, effect_bottom, effect_right, effect_top)

        # 충돌 검사
        if (cat_left < effect_right and cat_right > effect_left and
            cat_bottom < effect_top and cat_top > effect_bottom):
            # 충돌 시 무적시간 활성화
            self.invincible = True
            self.invincible_timer = self.invincible_duration
            return True

        return False

    def check_collision_with_projectile(self, projectile):
        """플레이어 투사체와의 충돌 감지

        Args:
            projectile: Projectile을 상속받은 발사체 객체

        Returns:
            bool: 충돌 여부
        """
        # 무적 상태이면 충돌 무시
        if self.invincible:
            return False

        # 발사체 크기 (Projectile의 get_collision_box 메서드 사용)
        if hasattr(projectile, 'get_collision_box'):
            projectile_width, projectile_height = projectile.get_collision_box()
        else:
            projectile_width = 30
            projectile_height = 30

        # AABB (Axis-Aligned Bounding Box) 충돌 감지
        cat_left = self.x - self.collision_width / 2
        cat_right = self.x + self.collision_width / 2
        cat_bottom = self.y - self.collision_height / 2
        cat_top = self.y + self.collision_height / 2

        proj_left = projectile.x - projectile_width / 2
        proj_right = projectile.x + projectile_width / 2
        proj_bottom = projectile.y - projectile_height / 2
        proj_top = projectile.y + projectile_height / 2

        # 충돌 검사
        if (cat_left < proj_right and cat_right > proj_left and
            cat_bottom < proj_top and cat_top > proj_bottom):
            # 충돌 시 무적시간 활성화
            self.invincible = True
            self.invincible_timer = self.invincible_duration
            return True

        return False

