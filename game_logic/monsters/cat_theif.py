import pico2d as p2
import random
import math

import game_framework
from ..state_machine import StateMachine
from ..stats import CatAssassinStats
from ..damage_indicator import DamageIndicator
from ..ui_overlay import MonsterHealthBar

# ========== Idle State ==========
class Idle:
    images = None

    def __init__(self, cat):
        self.cat = cat
        self.detection_range = 300  # 플레이어 감지 범위 (픽셀)

        if Idle.images is None:
            Idle.images = []
            try:
                for i in range(6):  # Cat_Assassin_Idle0 ~ Idle5
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Thief/character/Cat_Thief_Idle{i}.png')
                    Idle.images.append(img)
                print(f"[CatThief Idle] Loaded {len(Idle.images)} images")
            except Exception as e:
                print(f"\033[91m[CatThief Idle] Failed to load images: {e}\033[0m")
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
        self.cat.animation_time += game_framework.get_delta_time()
        if self.cat.animation_time >= 1.0 / self.cat.animation_speed:
            self.cat.frame = (self.cat.frame + 1) % len(Idle.images)
            self.cat.animation_time = 0

        # AI: Check if player is nearby and chase
        if self.cat.world and 'player' in self.cat.world:
            player = self.cat.world['player']
            dx = player.x - self.cat.x
            dy = player.y - self.cat.y
            distance = math.sqrt(dx**2 + dy**2)

            # 감지 범위 내에 플레이어가 있으면 Chase 상태로 전환
            if distance <= self.detection_range:
                self.cat.state_machine.handle_state_event(('DETECT_PLAYER', player))

    def draw(self, draw_x, draw_y):
        if Idle.images and len(Idle.images) > 0:
            Idle.images[self.cat.frame].draw(draw_x, draw_y,
                                             Idle.images[self.cat.frame].w * self.cat.scale,
                                             Idle.images[self.cat.frame].h * self.cat.scale)

# ========== Chase State (상위 상태) ==========
class Chase:
    """플레이어를 추적하는 상태 - Run, Kiting, Attack 하위 상태를 가짐"""

    def __init__(self, cat):
        self.cat = cat
        self.lose_range = 600  # 플레이어를 놓치는 거리
        self.attack_range = 300  # 공격 범위
        self.attack_range_exit = 350  # 공격 범위를 벗어나는 거리 (여유를 둠)
        self.kiting_min_range = 250  # 너무 가까우면 후퇴할 거리

        # 공격 쿨타임 관련
        self.attack_cooldown = 2.0  # 공격 후 2초 대기
        self.attack_cooldown_timer = 0.0  # 쿨타임 타이머
        self.can_attack = False  # 공격 가능 여부 - 처음에는 False로 시작

        # 하위 상태 머신 생성
        self.RUN = Run(cat)
        self.KITING = Kiting(cat, self)  # 새로운 Kiting 상태 추가
        self.ATTACK = Attack(cat, self)  # Chase 상태 참조 전달

        self.sub_state_machine = StateMachine(
            self.RUN,
            {
                self.RUN: {in_attack_range: self.KITING},
                self.KITING: {out_attack_range: self.RUN, ready_to_attack: self.ATTACK},
                self.ATTACK: {attack_end: self.KITING},
            }
        )

    def enter(self, e):
        print("[Chase State] 추적 시작")
        # 추적 시작 시 쿨타임 초기화
        self.can_attack = False
        self.attack_cooldown_timer = 0.0
        # 하위 상태 머신을 Run 상태로 초기화 (이미 __init__에서 초기화됨)
        # sub_state_machine의 cur_state는 이미 RUN으로 설정되어 있음
        self.sub_state_machine.cur_state.enter(e)

    def exit(self, e):
        print("[Chase State] 추적 종료")
        self.sub_state_machine.cur_state.exit(e)

    def do(self):
        dt = game_framework.get_delta_time()

        # 공격 쿨타임 업데이트
        if not self.can_attack:
            self.attack_cooldown_timer += dt
            if self.attack_cooldown_timer >= self.attack_cooldown:
                self.can_attack = True
                self.attack_cooldown_timer = 0.0
                print("[Chase State] 공격 쿨타임 완료 - 공격 가능")

        # 플레이어와의 거리 체크
        if self.cat.world and 'player' in self.cat.world:
            player = self.cat.world['player']
            dx = player.x - self.cat.x
            dy = player.y - self.cat.y
            distance = math.sqrt(dx**2 + dy**2)

            # 플레이어를 놓쳤으면 Idle로 복귀
            if distance > self.lose_range:
                self.cat.state_machine.handle_state_event(('LOSE_PLAYER', None))
                return

            # 현재 하위 상태 확인
            current_sub_state = self.sub_state_machine.cur_state
            current_state_name = current_sub_state.__class__.__name__

            # 거리에 따른 상태 전환 (Hysteresis 적용)
            if isinstance(current_sub_state, Run):
                # Run 상태: attack_range 이하면 Kiting으로
                if distance <= self.attack_range:
                    print(f"[Chase State] 거리 {distance:.1f} - Kiting 상태로 전환")
                    self.sub_state_machine.handle_state_event(('IN_ATTACK_RANGE', player))

            elif isinstance(current_sub_state, Kiting):
                # Kiting 상태: attack_range_exit 초과하면 Run으로, can_attack이면 Attack으로
                if distance > self.attack_range_exit:
                    print(f"[Chase State] 거리 {distance:.1f} > {self.attack_range_exit} - Run 상태로 전환")
                    self.sub_state_machine.handle_state_event(('OUT_ATTACK_RANGE', player))
                elif self.can_attack:
                    # 쿨타임 끝나고 공격 가능 - Attack 상태로
                    print(f"[Chase State] 거리 {distance:.1f} - 공격 준비! (can_attack: {self.can_attack})")
                    self.sub_state_machine.handle_state_event(('READY_TO_ATTACK', player))
                    # 공격 쿨타임 시작 (Attack 상태 진입 시점에 쿨타임 시작)
                    self.can_attack = False
                    print(f"[Chase State] 공격 쿨타임 시작 - 다음 공격까지 {self.attack_cooldown}초")

            elif isinstance(current_sub_state, Attack):
                # Attack 상태는 애니메이션이 끝나면 자동으로 Kiting으로 복귀
                pass

        # 하위 상태 머신 업데이트
        self.sub_state_machine.update()

    def draw(self, draw_x, draw_y):
        # 하위 상태 머신의 draw 호출
        self.sub_state_machine.draw(draw_x, draw_y)

# ========== Run State (Chase의 하위 상태) ==========
class Run:
    images = None

    def __init__(self, cat):
        self.cat = cat

        if Run.images is None:
            Run.images = []
            try:
                for i in range(8):  # Cat_Assassin_Move0 ~ Move8
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Thief/character/Cat_Thief_Move{i}.png')
                    Run.images.append(img)
                print(f"[CatThief Run] Loaded {len(Run.images)} images")
            except Exception as e:
                print(f"\033[91m[CatThief Run] Failed to load images: {e}\033[0m")
                Run.images = []

        # 랜덤 움직임 관련 변수
        self.wander_angle = 0  # 현재 방향에서 벗어나는 각도
        self.wander_change_timer = 0  # 방향 변경 타이머
        self.wander_change_interval = 0.3  # 방향 변경 주기 (초)
        self.wander_strength = 0.6  # 랜덤 움직임의 강도 (0~1)

    def enter(self, e):
        self.cat.frame = 0
        self.cat.animation_time = 0
        self.cat.animation_speed = 12
        self.wander_angle = random.uniform(-math.pi/4, math.pi/4)  # -45도 ~ 45도
        self.wander_change_timer = 0
        print("[Run State] 달리기 시작")

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.get_delta_time()

        # 애니메이션 업데이트
        self.cat.animation_time += dt
        if self.cat.animation_time >= 1.0 / self.cat.animation_speed:
            if len(Run.images) > 0:
                self.cat.frame = (self.cat.frame + 1) % len(Run.images)
            self.cat.animation_time = 0

        # 플레이어 추적 with 랜덤 움직임
        if self.cat.world and 'player' in self.cat.world:
            player = self.cat.world['player']
            dx = player.x - self.cat.x
            dy = player.y - self.cat.y
            distance = math.sqrt(dx**2 + dy**2)

            # 방향 계산 (정규화)
            if distance > 0:
                # 플레이어 방향으로의 기본 방향
                base_dx = dx / distance
                base_dy = dy / distance

                # 랜덤 방향 변경 타이머 업데이트
                self.wander_change_timer += dt
                if self.wander_change_timer >= self.wander_change_interval:
                    # 랜덤 각도 변경 (-60도 ~ 60도)
                    self.wander_angle = random.uniform(-math.pi/3, math.pi/3)
                    self.wander_change_timer = 0

                # 기본 방향의 각도 계산
                base_angle = math.atan2(base_dy, base_dx)

                # 랜덤 각도를 적용한 최종 각도
                final_angle = base_angle + (self.wander_angle * self.wander_strength)

                # 최종 이동 방향 벡터
                move_dx = math.cos(final_angle)
                move_dy = math.sin(final_angle)

                # 위치 업데이트
                self.cat.x += move_dx * self.cat.speed * dt
                self.cat.y += move_dy * self.cat.speed * dt

    def draw(self, draw_x, draw_y):
        if Run.images and len(Run.images) > 0:
            Run.images[self.cat.frame].draw(draw_x, draw_y,
                                            Run.images[self.cat.frame].w * self.cat.scale,
                                            Run.images[self.cat.frame].h * self.cat.scale)

# ========== Kiting State (Chase의 하위 상태) ==========
class Kiting:
    """공격 사거리 내에서 거리를 유지하며 조금씩 움직이는 상태"""

    def __init__(self, cat, chase_state = None):
        self.cat = cat
        self.chase_state = chase_state  # Chase 상태에 대한 참조

        # Run 이미지 사용 (Kiting은 빠르게 움직이므로)
        # Run 클래스의 이미지를 공유

        # 측면 이동 관련 변수
        self.strafe_direction = random.choice([-1, 1])  # -1: 왼쪽, 1: 오른쪽
        self.strafe_change_timer = 0
        self.strafe_change_interval = 1.5  # 1.5초마다 방향 변경
        self.strafe_speed_multiplier = 1.0  # 원래 속도의 1.0배

    def enter(self, e):
        self.cat.frame = 0
        self.cat.animation_time = 0
        self.cat.animation_speed = 12  # Run과 같은 빠른 애니메이션
        self.strafe_direction = random.choice([-1, 1])
        self.strafe_change_timer = 0
        print("[Kiting State] 거리 유지하며 움직이기 시작")

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.get_delta_time()

        # 애니메이션 업데이트 (Run 이미지 사용)
        self.cat.animation_time += dt
        if self.cat.animation_time >= 1.0 / self.cat.animation_speed:
            if Run.images and len(Run.images) > 0:
                self.cat.frame = (self.cat.frame + 1) % len(Run.images)
            self.cat.animation_time = 0

        # 측면 이동 방향 변경 타이머
        self.strafe_change_timer += dt
        if self.strafe_change_timer >= self.strafe_change_interval:
            self.strafe_direction = random.choice([-1, 1])
            self.strafe_change_timer = 0
            print(f"[Kiting State] 이동 방향 변경: {'왼쪽' if self.strafe_direction == -1 else '오른쪽'}")

        # 플레이어와의 거리 체크 및 이동
        if self.cat.world and 'player' in self.cat.world:
            player = self.cat.world['player']
            dx = player.x - self.cat.x
            dy = player.y - self.cat.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                # 플레이어 방향으로의 단위 벡터
                to_player_x = dx / distance
                to_player_y = dy / distance

                # 기본 이동 속도 (1.0배)
                base_speed = self.cat.speed * self.strafe_speed_multiplier

                # 너무 가까우면 후퇴
                if distance < self.chase_state.kiting_min_range:
                    # 후퇴 (플레이어 반대 방향으로) - 빠르게
                    flee_dx = -to_player_x
                    flee_dy = -to_player_y
                    self.cat.x += flee_dx * base_speed * dt
                    self.cat.y += flee_dy * base_speed * dt

                elif distance > self.chase_state.attack_range:
                    # 너무 멀면 조금 다가가기 (적당한 속도로)
                    self.cat.x += to_player_x * base_speed * 0.5 * dt
                    self.cat.y += to_player_y * base_speed * 0.5 * dt

                else:
                    # 적정 거리 - 측면으로 이동 (strafing)
                    # 플레이어를 향한 벡터에 수직인 벡터로 이동
                    perpendicular_x = -to_player_y * self.strafe_direction
                    perpendicular_y = to_player_x * self.strafe_direction

                    self.cat.x += perpendicular_x * base_speed * dt
                    self.cat.y += perpendicular_y * base_speed * dt

    def draw(self, draw_x, draw_y):
        # Run 이미지 사용
        if Run.images and len(Run.images) > 0:
            Run.images[self.cat.frame].draw(draw_x, draw_y,
                                            Run.images[self.cat.frame].w * self.cat.scale,
                                            Run.images[self.cat.frame].h * self.cat.scale)

# ========== Attack State (Chase의 하위 상태) ==========
class Attack:
    images = None

    def __init__(self, cat, chase_state = None):
        self.cat = cat
        self.chase_state = chase_state  # Chase 상태에 대한 참조 (optional)

        if Attack.images is None:
            Attack.images = []
            try:
                for i in range(7):  # Cat_Assassin_Attack0 ~ Attack6
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Thief/character/Cat_Thief_Attack{i}.png')
                    Attack.images.append(img)
                print(f"[CatThief Attack] Loaded {len(Attack.images)} images")
            except Exception as e:
                print(f"\033[91m[CatThief Attack] Failed to load images: {e}\033[0m")
                Attack.images = []

        self.animation_finished = False

    def enter(self, e):
        self.cat.frame = 0
        self.cat.animation_time = 0
        self.cat.animation_speed = 10  # 공격 애니메이션은 빠르게
        self.animation_finished = False
        print("[Attack State] 공격 시작")

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.get_delta_time()

        # 애니메이션 업데이트
        self.cat.animation_time += dt
        if self.cat.animation_time >= 1.0 / self.cat.animation_speed:
            self.cat.frame += 1
            self.cat.animation_time = 0

            # 애니메이션이 끝나면 Kiting으로 복귀
            if len(Attack.images) > 0 and self.cat.frame >= len(Attack.images):
                if not self.animation_finished:
                    self.animation_finished = True
                    print("[Attack State] 공격 애니메이션 완료")
                    # Chase 상태의 can_attack을 False로 설정 (쿨타임 시작)
                    if self.chase_state:
                        self.chase_state.can_attack = False

                    self.cat.state_machine.cur_state.sub_state_machine.handle_state_event(('ATTACK_END', None))

    def draw(self, draw_x, draw_y):
        if Attack.images and len(Attack.images) > 0:
            frame_idx = min(self.cat.frame, len(Attack.images) - 1)
            Attack.images[frame_idx].draw(draw_x, draw_y,
                                          Attack.images[frame_idx].w * self.cat.scale,
                                          Attack.images[frame_idx].h * self.cat.scale)

# ========== Hit State ==========
class Hit:
    images = None

    def __init__(self, cat):
        self.cat = cat

        if Hit.images is None:
            Hit.images = []
            try:
                for i in range(3):  # Cat_Assassin_Airborne0 ~ Airborne2
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Thief/character/Cat_Thief_Airborne{i}.png')
                    Hit.images.append(img)
                print(f"[CatThief Hit] Loaded {len(Hit.images)} images")
            except Exception as e:
                print(f"\033[91m[CatThief Hit] Failed to load images: {e}\033[0m")
                Hit.images = []

        self.cat.animation_speed = 12  # 피격 애니메이션은 빠르게
        self.animation_finished = False

        # 넉백 관련 변수
        self.knockback_dx = 0
        self.knockback_dy = 0
        self.knockback_speed = 200
        self.knockback_duration = 0.2
        self.knockback_timer = 0.0

    def enter(self, e):
        self.cat.frame = 0
        self.cat.animation_time = 0
        self.animation_finished = False
        self.knockback_timer = 0.0

        # 넉백 방향 계산
        if e and len(e) > 1 and e[1] is not None:
            attacker = e[1]
            attacker_x = attacker.x if hasattr(attacker, 'x') else self.cat.x
            attacker_y = attacker.y if hasattr(attacker, 'y') else self.cat.y

            if hasattr(attacker, 'owner') and attacker.owner:
                attacker_x = attacker.owner.x
                attacker_y = attacker.owner.y

            dx = self.cat.x - attacker_x
            dy = self.cat.y - attacker_y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                self.knockback_dx = dx / distance
                self.knockback_dy = dy / distance
            else:
                self.knockback_dx = 1.0
                self.knockback_dy = 0.0
        else:
            self.knockback_dx = 1.0
            self.knockback_dy = 0.0

        print(f"[CatThief Hit State] 피격 애니메이션 시작")

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.get_delta_time()

        # 넉백 효과 적용
        if self.knockback_timer < self.knockback_duration:
            progress = self.knockback_timer / self.knockback_duration
            current_speed = self.knockback_speed * (1.0 - progress)
            self.cat.x += self.knockback_dx * current_speed * dt
            self.cat.y += self.knockback_dy * current_speed * dt
            self.knockback_timer += dt

        # 애니메이션 업데이트
        self.cat.animation_time += dt
        if self.cat.animation_time >= 1.0 / self.cat.animation_speed:
            self.cat.frame += 1
            self.cat.animation_time = 0

            if len(Hit.images) > 0 and self.cat.frame >= len(Hit.images):
                if not self.animation_finished:
                    self.animation_finished = True
                    print(f"[CatThief Hit State] 피격 애니메이션 완료, Idle 복귀")
                    self.cat.state_machine.handle_state_event(('HIT_END', None))

    def draw(self, draw_x, draw_y):
        if Hit.images and len(Hit.images) > 0:
            frame_idx = min(self.cat.frame, len(Hit.images) - 1)
            Hit.images[frame_idx].draw(draw_x, draw_y,
                                       Hit.images[frame_idx].w * self.cat.scale,
                                       Hit.images[frame_idx].h * self.cat.scale)

# ========== Death State ==========
class Death:
    image = None

    def __init__(self, cat):
        self.cat = cat

        if Death.image is None:
            try:
                Death.image = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Thief/character/Cat_Thief_Down0.png')
                print(f"[CatThief Death] Loaded Down0 image")
            except Exception as e:
                print(f"\033[91m[CatThief Death] Failed to load image: {e}\033[0m")
                Death.image = None

        self.death_timer = 0.0
        self.death_duration = 3.0
        self.mark_for_removal = False

        # 넉백 관련 변수 (일반 피격보다 강함)
        self.knockback_dx = 0
        self.knockback_dy = 0
        self.knockback_speed = 350  # Hit의 200보다 크게 (1.75배)
        self.knockback_duration = 0.4  # Hit의 0.2초보다 길게 (2배)
        self.knockback_timer = 0.0

    def enter(self, e):
        self.death_timer = 0.0
        self.mark_for_removal = False
        self.knockback_timer = 0.0

        # 넉백 방향 계산 (Hit State와 동일한 로직)
        if e and len(e) > 1 and e[1] is not None:
            attacker = e[1]
            attacker_x = attacker.x if hasattr(attacker, 'x') else self.cat.x
            attacker_y = attacker.y if hasattr(attacker, 'y') else self.cat.y

            if hasattr(attacker, 'owner') and attacker.owner:
                attacker_x = attacker.owner.x
                attacker_y = attacker.owner.y

            dx = self.cat.x - attacker_x
            dy = self.cat.y - attacker_y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                self.knockback_dx = dx / distance
                self.knockback_dy = dy / distance
            else:
                self.knockback_dx = 1.0
                self.knockback_dy = 0.0
        else:
            self.knockback_dx = 1.0
            self.knockback_dy = 0.0

        print(f"[CatThief Death State] 사망 상태 시작 (3초 후 제거) - 넉백 적용")

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.get_delta_time()

        self.death_timer += dt

        # 넉백 효과 적용 (사망 시에도 밀려남)
        if self.knockback_timer < self.knockback_duration:
            progress = self.knockback_timer / self.knockback_duration
            # 더 부드러운 감속을 위해 제곱 사용
            current_speed = self.knockback_speed * (1.0 - progress) ** 1.5
            self.cat.x += self.knockback_dx * current_speed * dt
            self.cat.y += self.knockback_dy * current_speed * dt
            self.knockback_timer += dt

        if self.death_timer >= self.death_duration and not self.mark_for_removal:
            self.mark_for_removal = True
            self.cat.mark_for_removal = True
            print(f"[CatThief Death State] 3초 경과, 제거 표시 완료")

    def draw(self, draw_x, draw_y):
        if Death.image is not None:
            Death.image.draw(draw_x, draw_y,
                           Death.image.w * self.cat.scale,
                           Death.image.h * self.cat.scale)

# ========== Event Predicates ==========
def detect_player(e):
    return e[0] == 'DETECT_PLAYER'

def lose_player(e):
    return e[0] == 'LOSE_PLAYER'

def in_attack_range(e):
    return e[0] == 'IN_ATTACK_RANGE'

def out_attack_range(e):
    return e[0] == 'OUT_ATTACK_RANGE'

def ready_to_attack(e):
    return e[0] == 'READY_TO_ATTACK'

def attack_end(e):
    return e[0] == 'ATTACK_END'

def take_hit(e):
    return e[0] == 'TAKE_HIT'

def hit_end(e):
    return e[0] == 'HIT_END'

def die(e):
    return e[0] == 'DIE'

# CatThief (monster)
class CatThief:
    def __init__(self, x = 800, y = 450):
        self.x, self.y = x, y
        self.speed = 100
        self.scale = 3.0
        self.world = None

        self.mark_for_removal = False

        self.attack_cooldown = 2.0
        self.attack_timer = random.uniform(0, self.attack_cooldown)

        # Animation variables
        self.frame = 0
        self.animation_speed = 10
        self.animation_time = 0

        # Collision box
        self.collision_width = 15 * self.scale
        self.collision_height = 15 * self.scale

        # 무적시간 관련 변수
        self.invincible = False
        self.invincible_timer = 0.0
        self.invincible_duration = 0.3

        # 스탯 시스템
        self.stats = CatAssassinStats()
        self.health_bar = MonsterHealthBar(self)

        # State machine setup with rules
        self.IDLE = Idle(self)
        self.CHASE = Chase(self)
        self.HIT = Hit(self)
        self.DEATH = Death(self)

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {detect_player: self.CHASE, take_hit: self.HIT, die: self.DEATH},
                self.CHASE: {lose_player: self.IDLE, take_hit: self.HIT, die: self.DEATH},
                self.HIT: {hit_end: self.IDLE, die: self.DEATH},
                self.DEATH: {},
            }
        )

    def update(self):
        # 무적시간 업데이트
        if self.invincible:
            self.invincible_timer -= game_framework.get_delta_time()
            if self.invincible_timer <= 0:
                self.invincible = False
                self.invincible_timer = 0.0

        self.state_machine.update()
        return True

    def draw(self, draw_x, draw_y):
        self.state_machine.draw(draw_x, draw_y)

        # 체력 바 그리기 (카메라 좌표 적용)
        self.health_bar.draw(draw_x, draw_y)

    def attack(self, target):
        """공격 - 나중에 다른 공격 방식으로 구현 예정"""
        print(f"[CatThief] 공격 - 구현 예정")
        pass

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

        # 충돌 체크
        collision = not (cat_right < effect_left or
                        cat_left > effect_right or
                        cat_top < effect_bottom or
                        cat_bottom > effect_top)

        return collision

    def take_damage(self, damage, attacker=None):
        """데미지를 받는 메서드"""
        # 이미 죽었으면 데미지 무시
        if isinstance(self.state_machine.cur_state, Death):
            return

        # 무적 상태면 데미지 무시
        if self.invincible:
            print(f"[CatThief] 무적 상태 - 데미지 무시")
            return

        # 무적 시간 활성화
        self.invincible = True
        self.invincible_timer = self.invincible_duration

        # 스탯에서 방어력 가져오기
        defense = self.stats.get('defense')
        # 최종 데미지 계산 (방어력만큼 감소, 최소 1)
        final_damage = max(1, damage - defense)

        # 체력 감소
        current_health = self.stats.get('health')
        max_health = self.stats.get('max_health')
        new_health = max(0, current_health - final_damage)
        self.stats.set('health', new_health)

        # 데미지 인디케이터 생성
        try:
            if self.world and 'damage_indicators' in self.world:
                indicator = DamageIndicator(self.x, self.y, final_damage)
                self.world['damage_indicators'].append(indicator)
        except Exception as e:
            print(f"[CatThief] 데미지 인디케이터 생성 실패: {e}")

        # 피격 정보 출력 (디버그)
        attacker_name = attacker.__class__.__name__ if attacker else "Unknown"
        print(f"\n{'='*60}")
        print(f"[CatThief 피격] at ({int(self.x)}, {int(self.y)})")
        print(f"  공격자: {attacker_name}")
        print(f"  원본 데미지: {damage:.1f}")
        print(f"  방어력: {defense:.1f}")
        print(f"  최종 데미지: {final_damage:.1f}")
        print(f"  체력 변화: {current_health:.1f} -> {new_health:.1f} (최대: {max_health:.1f})")
        print(f"  체력 비율: {(new_health/max_health)*100:.1f}%")
        print(f"  무적시간: {self.invincible_duration}초 활성화")

        # 체력이 0 이하면 사망 상태로 전환
        if new_health <= 0:
            print(f"  >>> CatThief 체력 0 - 사망 상태로 전환")
            print(f"{'='*60}\n")
            self.state_machine.handle_state_event(('DIE', attacker))
        else:
            # 피격 상태로 전환 (공격자 정보를 함께 전달)
            print(f"  >>> 피격 상태로 전환")
            print(f"{'='*60}\n")
            self.state_machine.handle_state_event(('TAKE_HIT', attacker))

    def on_death(self):
        """사망 처리 - 이제 상태 머신에서 처리하므로 deprecated"""
        pass
