import ctypes
import math
import os
from pico2d import load_image, get_canvas_height
from sdl2 import SDL_GetMouseState, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT
from . import framework


class Weapon:
    """기본 무기 클래스"""
    def __init__(self, player, weapon_type, image_path, render_layer='back', scale=3.0):
        self.player = player
        self.weapon_type = weapon_type  # 'sword', 'shield', 'wand' 등
        self.render_layer = render_layer  # 'back' 또는 'front'
        self.scale_factor = scale

        # 이미지 로드
        self.image = load_image(image_path)

        # 무기 위치 오프셋 (플레이어 중심 기준)
        self.offset_x = 20  # 기본 오프셋
        self.offset_y = 0

        # 회전 각도
        self.angle = 0  # 라디안

        # 공격 상태
        self.is_attacking = False
        self.attack_timer = 0.0
        self.attack_duration = 0.3  # 실제 공격 애니메이션 시간
        self.attack_recovery = 0.15  # 공격 후 딜레이 (후딜레이)
        self.total_attack_time = self.attack_duration + self.attack_recovery  # 총 공격 시간

    def update(self):
        """마우스 위치를 기준으로 무기 각도 계산"""
        mx = ctypes.c_int(0)
        my = ctypes.c_int(0)
        SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))

        canvas_h = get_canvas_height()
        mouse_game_y = canvas_h - my.value

        # 플레이어에서 마우스로 향하는 벡터
        dx = mx.value - self.player.x
        dy = mouse_game_y - self.player.y

        # 각도 계산 (라디안)
        self.angle = math.atan2(dy, dx)

        # 공격 타이머 업데이트
        if self.is_attacking:
            dt = framework.get_delta_time()
            self.attack_timer += dt
            if self.attack_timer >= self.total_attack_time:
                self.is_attacking = False
                self.attack_timer = 0.0

    def attack(self):
        """공격 시작"""
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 0.0
            print(f"{self.weapon_type} 공격!")
            return True
        return False

    def draw(self):
        """무기를 회전시켜서 그리기"""
        # 무기 위치 계산 (플레이어 위치 + 오프셋)
        weapon_x = self.player.x + self.offset_x * math.cos(self.angle)
        weapon_y = self.player.y + self.offset_y + self.offset_x * math.sin(self.angle)

        # 좌우 반전 결정
        flip = 'h' if self.player.face_dir == -1 else ''

        # 회전된 무기 그리기
        self.image.clip_composite_draw(
            0, 0, self.image.w, self.image.h,
            self.angle, flip,
            weapon_x, weapon_y,
            self.image.w * self.scale_factor,
            self.image.h * self.scale_factor
        )


class Shield(Weapon):
    """방패 클래스 (항상 캐릭터 앞에 그려짐)"""
    def __init__(self, player, image_path, scale=3.0):
        super().__init__(player, 'shield', image_path, render_layer='front', scale=scale)
        self.offset_x = -10  # 방패는 좀 더 가까이
        self.offset_y = -10 # 방패는 약간 아래쪽

    def update(self):
        """방패는 회전하지 않음 (공격 타이머만 업데이트)"""
        if self.is_attacking:
            dt = framework.get_delta_time()
            self.attack_timer += dt
            if self.attack_timer >= self.attack_duration:
                self.is_attacking = False
                self.attack_timer = 0.0

    def attack(self):
        """방패는 막기 동작"""
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 0.0
            print(f"방패로 막기!")

    def draw(self):
        """방패는 회전 없이 플레이어 앞에 고정"""
        # 방패 위치는 플레이어 중심에 고정
        weapon_x = self.player.x + self.offset_x
        weapon_y = self.player.y + self.offset_y

        # 좌우 반전만 적용 (회전 없음)
        flip = 'h' if self.player.face_dir == -1 else ''
        self.offset_x = 10 if self.player.face_dir == -1 else 0 -10

        # 회전 없이 방패 그리기 (각도는 0)
        self.image.clip_composite_draw(
            0, 0, self.image.w, self.image.h,
            0, flip,  # 회전 각도를 0으로 고정
            weapon_x, weapon_y,
            self.image.w * self.scale_factor,
            self.image.h * self.scale_factor
        )


class Sword(Weapon):
    """검 클래스 (항상 캐릭터 뒤에 그려짐)"""
    def __init__(self, player, image_path, scale=3.0):
        super().__init__(player, 'sword', image_path, render_layer='back', scale=scale)
        self.offset_x = 15  # 검은 좀 더 멀리
        self.offset_y = 8 # 검의 기본 Y 오프셋
        self.attack_duration = 0.1  # 공격 모션 시간
        self.attack_recovery = 0.3  # 공격 후 후딜레이
        self.total_attack_time = self.attack_duration + self.attack_recovery  # 총 공격 시간
        self.base_angle_offset = math.radians(25)  # 기본 각도 오프셋

        # 공격 모션 관련 변수
        self.attack_progress = 0.0  # 0.0 ~ 1.0
        self.attack_angle_range = -math.radians(205)  # 0도 ~ 270도 회전 (검 자체 회전)
        self.y_offset_down = -50  # progress 0.5까지 내려갈 y 오프셋

        # 자전 및 공전 각도 범위 추가
        self.rotation_angle_range = -math.radians(270)  # 자전: 0도 ~ 270도
        self.orbit_angle_range = -math.radians(205)  # 공전: 0도 ~ 205도

    def update(self):
        """마우스 위치를 기준으로 무기 각도 계산"""
        mx = ctypes.c_int(0)
        my = ctypes.c_int(0)
        SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))

        canvas_h = get_canvas_height()
        mouse_game_y = canvas_h - my.value

        # 플레이어에서 마우스로 향하는 벡터
        dx = mx.value - self.player.x
        dy = mouse_game_y - self.player.y

        # 각도 계산 (라디안)
        self.angle = math.atan2(dy, dx)

        # 공격 타이머 업데이트
        if self.is_attacking:
            dt = framework.get_delta_time()
            self.attack_timer += dt

            # 공격 progress 계산 (0.0 ~ 1.0)
            if self.attack_timer < self.attack_duration:
                self.attack_progress = self.attack_timer / self.attack_duration
            else:
                self.attack_progress = 1.0

            if self.attack_timer >= self.total_attack_time:
                self.is_attacking = False
                self.attack_timer = 0.0
                self.attack_progress = 0.0

    def attack(self):
        """공격 시작"""
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 0.0
            self.attack_progress = 0.0
            print(f"{self.weapon_type} 공격!")

            # 공격 이펙트 생성
            from .player import VFX_Tier1_Sword_Swing

            # 마우스 방향 각도 계산
            angle_deg = math.degrees(self.angle) % 360
            if 90 < angle_deg < 270:  # 왼쪽 영역
                flip = 'vh'
            else:
                flip = 'h'

            # 공격 이펙트 생성 - VFX 내부에서 각도 조정 및 거리 계산
            attack_vfx = VFX_Tier1_Sword_Swing(
                self.player.x,
                self.player.y,
                self.angle,  # 원본 각도 전달, VFX 내부에서 ±90도 조정
                flip,
                scale=4.5,
                range_factor=60  # 캐릭터로부터 60픽셀 떨어진 위치에 이펙트 생성
            )
            self.player.attack_effects.append(attack_vfx)

            return True
        return False

    def draw(self):
        """검을 회전시켜서 그리기 - 검 자체를 중심으로 회전 + 캐릭터 중심으로 공전"""
        # 검 자체 회전 각도 계산
        sword_rotation = 0.0
        orbit_angle_offset = 0.0  # 캐릭터 중심 공전을 위한 각도 오프셋
        y_offset_modifier = 0.0

        if self.is_attacking:
            if self.attack_timer < self.attack_duration:
                # 공격 모션 중 (0 ~ attack_duration)
                sword_rotation = self.rotation_angle_range * self.attack_progress  # 자전 각도
                orbit_angle_offset = self.orbit_angle_range * self.attack_progress  # 공전 각도

                # Y축 오프셋: 공격 기간 동안 2 * self.offset_y만큼 내려감 (0 ~ 1)
                y_offset_modifier = -3 * self.offset_y * self.attack_progress
            else:
                # 후딜레이 중 (attack_duration ~ total_attack_time)
                sword_rotation = self.rotation_angle_range  # 자전 최대 각도 유지
                orbit_angle_offset = self.orbit_angle_range  # 공전 최대 각도 유지

                # Y축 오프셋: 후딜레이 동안 최대 아래 위치 유지 (후딜레이 끝나면 자동으로 0으로)
                y_offset_modifier = -3 * self.offset_y

        # 마우스가 왼쪽에 있을 때 (각도가 90도 ~ 270도 범위)
        angle_deg = math.degrees(self.angle) % 360

        if 90 < angle_deg < 270:  # 왼쪽 영역
            flip = 'v'  # 수직 반전
            # 왼쪽일 때는 검 회전을 반대로
            final_angle = self.angle - sword_rotation
            position_angle = self.angle - orbit_angle_offset  # 왼쪽일 때는 - 방향으로 공전
        else:  # 오른쪽 영역
            flip = ''
            final_angle = self.angle + sword_rotation
            position_angle = self.angle + orbit_angle_offset  # 오른쪽일 때는 + 방향으로 공전

        # 검의 위치 계산 (캐릭터 중심으로 공전하도록 position_angle 사용)
        weapon_x = self.player.x + self.offset_x * math.cos(position_angle)
        weapon_y = self.player.y + self.offset_y + self.offset_y * math.sin(position_angle) + y_offset_modifier

        # 회전된 무기 그리기 (검 자체 중심으로 회전)
        self.image.clip_composite_draw(
            0, 0, self.image.w, self.image.h,
            final_angle + self.base_angle_offset, flip,
            weapon_x, weapon_y,
            self.image.w * self.scale_factor,
            self.image.h * self.scale_factor
        )


class EquipmentManager:
    """장비를 관리하는 매니저 클래스"""
    def __init__(self, player):
        self.player = player
        self.back_equipment = []   # 캐릭터 뒤에 그려질 장비 (검 등)
        self.front_equipment = []  # 캐릭터 앞에 그려질 장비 (방패 등)

    def equip(self, equipment):
        """장비 장착"""
        if equipment.render_layer == 'back':
            self.back_equipment.append(equipment)
        elif equipment.render_layer == 'front':
            self.front_equipment.append(equipment)

    def unequip(self, equipment):
        """장비 해제"""
        if equipment in self.back_equipment:
            self.back_equipment.remove(equipment)
        if equipment in self.front_equipment:
            self.front_equipment.remove(equipment)

    def unequip_all(self):
        """모든 장비 해제"""
        self.back_equipment.clear()
        self.front_equipment.clear()

    def update(self):
        """모든 장비 업데이트"""
        for equipment in self.back_equipment + self.front_equipment:
            equipment.update()

    def handle_event(self, event):
        """장비 이벤트 처리 (주로 공격)"""
        # 마우스 좌클릭 시 공격
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            # 현재 장착된 모든 무기가 공격
            for equipment in self.back_equipment:
                equipment.attack()
            # 방패는 공격하지 않음 (필요시 막기 등 다른 동작 가능)
            # for equipment in self.front_equipment:
            #     equipment.attack()

    def draw_back(self):
        """캐릭터 뒤에 그려질 장비들"""
        for equipment in self.back_equipment:
            equipment.draw()

    def draw_front(self):
        """캐릭터 앞에 그려질 장비들"""
        for equipment in self.front_equipment:
            equipment.draw()
