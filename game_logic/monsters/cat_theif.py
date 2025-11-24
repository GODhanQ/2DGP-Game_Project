import pico2d as p2
import random
import math

import game_framework
from ..state_machine import StateMachine
from ..stats import CatThiefStats
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
        self.attack_cooldown = 3.0  # 공격 후 2초 대기
        self.attack_cooldown_timer = 0.0  # 쿨타임 타이머
        self.can_attack = True

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
    """2단계 공격 상태
    - 1단계: 플레이어 방향에서 ±45도 방향으로 회전 구르기 (Spin 모션)
    - 2단계: 플레이어 방향으로 3배속 돌진 공격 (Attack 모션 + Swing 이펙트)
    """
    character_images = None  # Attack 애니메이션 이미지
    spin_images = None  # Spin 애니메이션 이미지

    def __init__(self, cat, chase_state = None):
        self.cat = cat
        self.chase_state = chase_state  # Chase 상태에 대한 참조

        # Attack 캐릭터 이미지 로드
        if Attack.character_images is None:
            Attack.character_images = []
            try:
                for i in range(7):  # Cat_Thief_Attack0 ~ Attack6
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Thief/character/Cat_Thief_Attack{i}.png')
                    Attack.character_images.append(img)
                print(f"[CatThief Attack] Loaded {len(Attack.character_images)} attack images")
            except Exception as e:
                print(f"\033[91m[CatThief Attack] Failed to load attack images: {e}\033[0m")
                Attack.character_images = []

        # Spin 캐릭터 이미지 로드
        if Attack.spin_images is None:
            Attack.spin_images = []
            try:
                for i in range(7):  # Cat_Thief_Spin0 ~ Spin6
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Thief/character/Cat_Thief_Spin{i}.png')
                    Attack.spin_images.append(img)
                print(f"[CatThief Attack] Loaded {len(Attack.spin_images)} spin images")
            except Exception as e:
                print(f"\033[91m[CatThief Attack] Failed to load spin images: {e}\033[0m")
                Attack.spin_images = []

        # 공격 단계 (1: 회전 구르기, 2: 돌진 공격)
        self.attack_phase = 1
        self.animation_finished = False

        # 1단계: 회전 구르기 관련 변수
        self.roll_direction_x = 0  # 구르기 방향 X
        self.roll_direction_y = 0  # 구르기 방향 Y
        self.roll_speed = 300  # 구르기 속도
        self.roll_duration = 0.0  # 구르기 지속 시간 (애니메이션 기반)

        # 2단계: 돌진 공격 관련 변수
        self.dash_direction_x = 0  # 돌진 방향 X
        self.dash_direction_y = 0  # 돌진 방향 Y
        self.dash_speed = 0  # 돌진 속도 (기본 속도의 3배)
        self.dash_distance = 900  # 돌진 거리
        self.dash_traveled = 0  # 이동한 거리
        self.swing_effect_spawned = False  # 검격 이펙트 생성 여부

    def enter(self, e):
        self.cat.frame = 0
        self.cat.animation_time = 0
        self.animation_finished = False
        self.attack_phase = 1
        self.swing_effect_spawned = False
        self.dash_traveled = 0

        # 플레이어 위치 가져오기
        if self.cat.world and 'player' in self.cat.world:
            player = self.cat.world['player']
            dx = player.x - self.cat.x
            dy = player.y - self.cat.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                # 플레이어 방향 단위 벡터
                to_player_x = dx / distance
                to_player_y = dy / distance

                # 1단계: 플레이어 방향에서 ±45도 랜덤 선택하여 구르기
                angle_offset = random.choice([math.pi / 4, -math.pi / 4])  # +45도 또는 -45도
                base_angle = math.atan2(to_player_y, to_player_x)
                roll_angle = base_angle + angle_offset

                self.roll_direction_x = math.cos(roll_angle)
                self.roll_direction_y = math.sin(roll_angle)

                # 2단계: 플레이어 방향으로 돌진 (나중에 사용)
                self.dash_direction_x = to_player_x
                self.dash_direction_y = to_player_y
                self.dash_speed = self.cat.speed * 5.0  # 기본 속도의 5배

                print(f"[Attack State] 1단계 시작 - 구르기 방향: ({self.roll_direction_x:.2f}, {self.roll_direction_y:.2f})")
            else:
                # 플레이어와 같은 위치면 기본 방향
                self.roll_direction_x = 1.0
                self.roll_direction_y = 0.0
                self.dash_direction_x = 1.0
                self.dash_direction_y = 0.0
                self.dash_speed = self.cat.speed * 3.0

        # 1단계 애니메이션 속도 설정
        self.cat.animation_speed = 12

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.get_delta_time()

        # ===== 1단계: 회전 구르기 =====
        if self.attack_phase == 1:
            # 애니메이션 업데이트
            self.cat.animation_time += dt
            if self.cat.animation_time >= 1.0 / self.cat.animation_speed:
                self.cat.frame += 1
                self.cat.animation_time = 0

                # Spin 애니메이션이 끝나면 2단계로 전환
                if Attack.spin_images and self.cat.frame >= len(Attack.spin_images):
                    # 1단계 종료 시점에 플레이어 방향 재계산
                    if self.cat.world and 'player' in self.cat.world:
                        player = self.cat.world['player']
                        dx = player.x - self.cat.x
                        dy = player.y - self.cat.y
                        distance = math.sqrt(dx**2 + dy**2)

                        if distance > 0:
                            # 플레이어 방향으로 돌진 방향 업데이트
                            self.dash_direction_x = dx / distance
                            self.dash_direction_y = dy / distance
                            print(f"[Attack State] 돌진 방향 재계산: ({self.dash_direction_x:.2f}, {self.dash_direction_y:.2f})")
                        else:
                            # 플레이어와 같은 위치면 기존 방향 유지
                            print(f"[Attack State] 플레이어와 같은 위치 - 기존 방향 유지")

                    self.attack_phase = 2
                    self.cat.frame = 0
                    self.cat.animation_time = 0
                    self.cat.animation_speed = 10  # 2단계는 조금 느리게
                    self.dash_traveled = 0  # 돌진 거리 초기화
                    print(f"[Attack State] 2단계 시작 - 돌진 공격")

            # 구르기 이동
            self.cat.x += self.roll_direction_x * self.roll_speed * dt
            self.cat.y += self.roll_direction_y * self.roll_speed * dt

        # ===== 2단계: 돌진 공격 =====
        elif self.attack_phase == 2:
            # 애니메이션 업데이트
            self.cat.animation_time += dt
            if self.cat.animation_time >= 1.0 / self.cat.animation_speed:
                self.cat.frame += 1
                self.cat.animation_time = 0

                # Attack 애니메이션이 끝나면 Kiting으로 복귀
                if Attack.character_images and self.cat.frame >= len(Attack.character_images):
                    if not self.animation_finished:
                        self.animation_finished = True
                        print("[Attack State] 공격 애니메이션 완료")
                        # Chase 상태의 can_attack을 False로 설정 (쿨타임 시작)
                        if self.chase_state:
                            self.chase_state.can_attack = False

                        self.cat.state_machine.cur_state.sub_state_machine.handle_state_event(('ATTACK_END', None))
                        return

            # 돌진 거리 체크 - 최대 거리에 도달하면 이동 중지
            if self.dash_traveled < self.dash_distance:
                move_distance = self.dash_speed * dt
                self.cat.x += self.dash_direction_x * move_distance
                self.cat.y += self.dash_direction_y * move_distance
                self.dash_traveled += move_distance

            # 검격 이펙트 생성 (프레임 3에서 생성)
            if self.cat.frame == 3 and not self.swing_effect_spawned:
                self.spawn_swing_effect()
                self.swing_effect_spawned = True

    def spawn_swing_effect(self):
        """검격 이펙트 생성 (Cat_Thief_Swing 이펙트)"""
        if not self.cat.world or 'effects_front' not in self.cat.world:
            print("[Attack State] world 또는 effects_front가 없어서 검격 이펙트 생성 실패")
            return

        try:
            # 검격 이펙트 위치 계산 (몬스터 앞쪽)
            offset_distance = 40  # 몬스터로부터의 거리
            effect_x = self.cat.x + self.dash_direction_x * offset_distance
            effect_y = self.cat.y + self.dash_direction_y * offset_distance

            # 검격 방향 각도 계산 (라디안)
            effect_angle = math.atan2(self.dash_direction_y, self.dash_direction_x)

            # CatThiefSwingEffect 생성
            swing_effect = CatThiefSwingEffect(
                effect_x,
                effect_y,
                effect_angle,
                owner=self.cat,
                scale=3.0
            )

            self.cat.world['effects_front'].append(swing_effect)
            print(f"[Attack State] 검격 이펙트 생성 at ({int(effect_x)}, {int(effect_y)}), 각도: {math.degrees(effect_angle):.1f}도")

        except Exception as e:
            print(f"\033[91m[Attack State] 검격 이펙트 생성 실패: {e}\033[0m")

    def draw(self, draw_x, draw_y):
        # 1단계: Spin 이미지 그리기
        if self.attack_phase == 1:
            if Attack.spin_images and len(Attack.spin_images) > 0:
                frame_idx = min(self.cat.frame, len(Attack.spin_images) - 1)
                Attack.spin_images[frame_idx].draw(
                    draw_x, draw_y,
                    Attack.spin_images[frame_idx].w * self.cat.scale,
                    Attack.spin_images[frame_idx].h * self.cat.scale
                )
        # 2단계: Attack 이미지 그리기
        elif self.attack_phase == 2:
            if Attack.character_images and len(Attack.character_images) > 0:
                frame_idx = min(self.cat.frame, len(Attack.character_images) - 1)
                Attack.character_images[frame_idx].draw(
                    draw_x, draw_y,
                    Attack.character_images[frame_idx].w * self.cat.scale,
                    Attack.character_images[frame_idx].h * self.cat.scale
                )


# ========== Cat Thief Swing Effect (검격 이펙트) ==========
class CatThiefSwingEffect:
    """Cat Thief의 검격 이펙트 (Cat_Thief_Swing 0~3)"""
    images = None

    def __init__(self, x, y, angle, owner=None, scale=3.0, damage=15.0):
        """
        Args:
            x, y: 이펙트 생성 위치 (월드 좌표)
            angle: 검격 방향 (라디안)
            owner: 공격 주체 (CatThief 객체)
            scale: 이펙트 크기 배율
            damage: 이펙트 데미지
        """
        self.x = x
        self.y = y
        self.angle = angle
        self.owner = owner
        self.scale = scale
        self.damage = damage

        # 이미지 로드 (클래스 변수로 한 번만 로드)
        if CatThiefSwingEffect.images is None:
            CatThiefSwingEffect.images = []
            try:
                for i in range(4):  # Cat_Thief_Swing0 ~ Swing3
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest/Cat_Thief/FX/Cat_Thief_Swing{i}.png')
                    CatThiefSwingEffect.images.append(img)
                print(f"[CatThiefSwingEffect] Loaded {len(CatThiefSwingEffect.images)} images")
            except Exception as e:
                print(f"\033[91m[CatThiefSwingEffect] Failed to load images: {e}\033[0m")
                CatThiefSwingEffect.images = []

        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 15  # 빠른 애니메이션 (15 FPS)
        self.finished = False

        # 충돌 체크용 변수
        self.has_hit_player = False  # 플레이어를 이미 맞췄는지 여부

        print(f"[CatThiefSwingEffect] 생성됨 at ({int(x)}, {int(y)}), 각도: {math.degrees(angle):.1f}도")

    def update(self):
        """이펙트 애니메이션 업데이트 (충돌 체크는 play_mode에서 처리)"""
        if self.finished:
            return False

        dt = game_framework.get_delta_time()
        self.animation_time += dt

        # 애니메이션 업데이트
        if self.animation_time >= 1.0 / self.animation_speed:
            self.frame += 1
            self.animation_time = 0

            # 애니메이션이 끝나면 제거
            if CatThiefSwingEffect.images and self.frame >= len(CatThiefSwingEffect.images):
                self.finished = True
                return False

        return True

    def get_collision_box(self):
        """충돌 박스 크기 반환 (play_mode에서 충돌 검사에 사용)

        Returns:
            tuple: (width, height) - 이펙트의 충돌 박스 크기
        """
        if CatThiefSwingEffect.images and len(CatThiefSwingEffect.images) > 0:
            effect_img = CatThiefSwingEffect.images[min(self.frame, len(CatThiefSwingEffect.images) - 1)]
            effect_width = effect_img.w * self.scale * 0.7  # 충돌 범위를 70%로 조정
            effect_height = effect_img.h * self.scale * 0.7
        else:
            effect_width = 100
            effect_height = 100

        return (effect_width, effect_height)


    def draw(self, draw_x, draw_y):
        """
        이펙트 그리기

        Args:
            draw_x: 카메라가 적용된 화면 X 좌표
            draw_y: 카메라가 적용된 화면 Y 좌표
        """
        if not CatThiefSwingEffect.images or len(CatThiefSwingEffect.images) == 0:
            return

        if self.finished:
            return

        frame_idx = min(self.frame, len(CatThiefSwingEffect.images) - 1)
        try:
            # 회전 각도를 degree로 변환 (pico2d는 degree 사용)
            # 기본 이미지가 위쪽 방향이므로 -90도를 기본으로 보정
            angle_deg = math.degrees(self.angle) - 90.0

            # 이미지 그리기 (회전 적용)
            CatThiefSwingEffect.images[frame_idx].composite_draw(
                angle_deg, '',  # 각도, 플립 없음
                draw_x, draw_y,
                CatThiefSwingEffect.images[frame_idx].w * self.scale,
                CatThiefSwingEffect.images[frame_idx].h * self.scale
            )
        except Exception as e:
            print(f"\033[91m[CatThiefSwingEffect] draw 에러: {e}\033[0m")


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

# ========== Hit State ==========
class Hit:
    images = None

    def __init__(self, cat):
        self.cat = cat

        if Hit.images is None:
            Hit.images = []
            try:
                for i in range(3):  # Cat_Thief_Airborne0 ~ Airborne2
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
        self.stats = CatThiefStats()
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
        p2.draw_rectangle(effect_left, effect_bottom, effect_right, effect_top)

        # 충돌 검사
        if (cat_left < effect_right and cat_right > effect_left and
            cat_bottom < effect_top and cat_top > effect_bottom):
            # 충돌 시 피격 처리
            self.on_hit(effect)
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
            # 충돌 시 피격 처리
            self.on_hit(projectile)
            return True

        return False

    def on_hit(self, attacker):
        """피격 시 호출되는 메서드

        Args:
            attacker: 공격한 객체 (투사체, 이펙트 등)
        """
        # 무적 상태라면 무시
        if self.invincible:
            print(f"[CatAssassin] 무적 상태로 피격 무시 (남은 무적시간: {self.invincible_timer:.2f}초)")
            return

        # 사망 상태면 무시
        if isinstance(self.state_machine.cur_state, Death):
            return

        # 무적시간 활성화
        self.invincible = True
        self.invincible_timer = self.invincible_duration

        # 데미지 계산
        damage = 0
        if hasattr(attacker, 'damage'):
            damage = attacker.damage
        elif hasattr(attacker, 'owner') and hasattr(attacker.owner, 'stats'):
            # 공격자의 스탯에서 데미지 가져오기
            damage = attacker.owner.stats.get('attack_damage')
        else:
            damage = 10.0  # 기본 데미지

        # 방어력 적산
        defense = self.stats.get('defense')
        final_damage = max(1.0, damage - defense)

        # 체력 감소
        current_health = self.stats.get('health')
        max_health = self.stats.get('max_health')
        new_health = max(0, current_health - final_damage)
        self.stats.set_base('health', new_health)

        # 데미지 인디케이터 생성 (월드에 추가)
        if self.world and 'effects_front' in self.world:
            try:
                # 몬스터 위치 위쪽에 데미지 인디케이터 생성
                damage_indicator = DamageIndicator(
                    self.x,
                    self.y + 30,  # 몬스터 위치보다 30 픽셀 위에 표시
                    final_damage,
                    duration=1.0,
                    font_size=30
                )
                self.world['effects_front'].append(damage_indicator)
                print(f"[CatAssassin] 데미지 인디케이터 생성: {int(final_damage)} 데미지")
            except Exception as e:
                print(f"[CatAssassin] 데미지 인디케이터 생성 실패: {e}")

        # 피격 정보 출력 (디버그)
        attacker_name = attacker.__class__.__name__
        print(f"\n{'=' * 60}")
        print(f"[CatAssassin 피격] at ({int(self.x)}, {int(self.y)})")
        print(f"  공격자: {attacker_name}")
        print(f"  원본 데미지: {damage:.1f}")
        print(f"  방어력: {defense:.1f}")
        print(f"  최종 데미지: {final_damage:.1f}")
        print(f"  체력 변화: {current_health:.1f} -> {new_health:.1f} (최대: {max_health:.1f})")
        print(f"  체력 비율: {(new_health / max_health) * 100:.1f}%")
        print(f"  무적시간: {self.invincible_duration}초 활성화")

        # 체력이 0 이하면 사망 상태로 전환
        if new_health <= 0:
            print(f"  >>> CatAssassin 체력 0 - 사망 상태로 전환")
            print(f"{'=' * 60}\n")
            self.state_machine.handle_state_event(('DIE', attacker))
        else:
            # 피격 상태로 전환 (공격자 정보를 함께 전달)
            print(f"  >>> 피격 상태로 전환")
            print(f"{'=' * 60}\n")
            self.state_machine.handle_state_event(('TAKE_HIT', attacker))

    def on_death(self):
        """사망 처리 - 이제 상태 머신에서 처리하므로 deprecated"""
        pass
