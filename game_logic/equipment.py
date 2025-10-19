import ctypes
import math
import os
from pico2d import load_image, get_canvas_height
from sdl2 import SDL_GetMouseState
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
        """방패는 회전하지 않음"""
        pass

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
        self.offset_y = 8  # 검은 약간 위쪽

    def draw(self):
        """검을 회전시켜서 그리기 (좌우 반전 문제 해결)"""
        # 무기 위치 계산 (플레이어 위치 + 오프셋)
        weapon_x = self.player.x + self.offset_x * math.cos(self.angle)
        weapon_y = self.player.y + self.offset_y + self.offset_x * math.sin(self.angle)

        # 마우스가 왼쪽에 있을 때 (각도가 90도 ~ 270도 범위)
        # 검을 상하 반전시켜서 자연스럽게 보이도록 함
        angle_deg = math.degrees(self.angle) % 360

        if 90 < angle_deg < 270:  # 왼쪽 영역
            flip = 'v'  # 수직 반전
            display_angle = self.angle  # 각도는 그대로
        else:  # 오른쪽 영역
            flip = ''
            display_angle = self.angle

        # 회전된 무기 그리기
        self.image.clip_composite_draw(
            0, 0, self.image.w, self.image.h,
            display_angle, flip,
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

    def draw_back(self):
        """캐릭터 뒤에 그려질 장비들"""
        for equipment in self.back_equipment:
            equipment.draw()

    def draw_front(self):
        """캐릭터 앞에 그려질 장비들"""
        for equipment in self.front_equipment:
            equipment.draw()
