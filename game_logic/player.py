# 패키지 내부 모듈을 직접 실행할 경우 친절한 안내 후 종료
if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    import sys
    print("이 모듈은 game_logic 패키지 내부 모듈입니다. 프로젝트 루트에서 main.py를 실행하세요.")
    sys.exit(1)

import ctypes
import os
import random

from pico2d import load_image, get_canvas_height, get_canvas_width
from sdl2 import (SDL_KEYDOWN, SDL_KEYUP, SDLK_a, SDLK_d, SDLK_w, SDLK_s, SDLK_TAB, SDL_GetMouseState)

from .equipment import EquipmentManager, Sword, Shield
from .state_machine import StateMachine
from . import framework

def Akey_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_a
def Akey_up(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_a
def Dkey_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_d
def Dkey_up(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_d
def Wkey_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_w
def Wkey_up(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_w
def Skey_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_s
def Skey_up(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_s


# 커스텀 이벤트 정의
def move_event(e):
    return e[0] == 'MOVE'

def stop_event(e):
    return e[0] == 'STOP'

# Tab 키 입력 검사용 predicate (StateMachine 매핑용)
def Tab_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_TAB

class Run:
    def __init__(self, player):
        self.player = player
        folder = os.path.join('resources', 'Texture_organize', 'Player_character', 'Adventurer')

        def load_seq(prefix, path):
            files = sorted([f for f in os.listdir(path)
                           if isinstance(f, str) and f.startswith(prefix) and f.lower().endswith('.png')])
            return [load_image(os.path.join(path, f)) for f in files]

        self.lower_frames = load_seq('Player_Adventurer_Move_Lower', folder)
        self.upper_frames = load_seq('Player_Adventurer_Move_Upper', folder)

        # 파티클 리소스 로드
        particle_folder = os.path.join('resources', 'Texture_organize', 'VFX', 'Run_Dust')
        self.particle_frames = load_seq('RunDust_Ver2_', particle_folder)
        self.particle_spawn_timer = 0.0
        self.particle_spawn_interval = 0.15 # 파티클 생성 간격

        if not self.lower_frames or not self.upper_frames:
            raise RuntimeError(f'Move frames not found in {folder}')

        self.frame = 0
        self.frame_time_acc = 0.0
        self.frame_duration = 0.06
        self.moving_speed = 300 # 초당 픽셀

    def enter(self, e):
        # 파티클 타이머만 초기화
        self.particle_spawn_timer = 0.0

    def exit(self, e):
        # 파티클을 제거하지 않고 그대로 둠
        pass

    def do(self):
        dt = framework.get_delta_time()

        # 플레이어 애니메이션 및 위치 업데이트
        self.frame_time_acc += dt
        if self.frame_time_acc >= self.frame_duration:
            self.frame_time_acc -= self.frame_duration
            self.frame = (self.frame + 1) % len(self.lower_frames)

        dir_magnitude = (self.player.dir[0] ** 2 + self.player.dir[1] ** 2) ** 0.5
        if dir_magnitude > 0:
            norm_dir_x = self.player.dir[0] / dir_magnitude
            norm_dir_y = self.player.dir[1] / dir_magnitude
            if self.player.x + norm_dir_x * self.moving_speed * dt > get_canvas_width():
                self.player.x = get_canvas_width()
            elif self.player.x + norm_dir_x * self.moving_speed * dt < 0:
                self.player.x = 0
            else: self.player.x += norm_dir_x * self.moving_speed * dt
            if self.player.y + norm_dir_y * self.moving_speed * dt > get_canvas_height():
                self.player.y = get_canvas_height()
            elif self.player.y + norm_dir_y * self.moving_speed * dt < 0:
                self.player.y = 0
            else: self.player.y += norm_dir_y * self.moving_speed * dt


        # 파티클 생성
        self.particle_spawn_timer += dt
        if self.particle_spawn_timer >= self.particle_spawn_interval:
            self.particle_spawn_timer -= self.particle_spawn_interval
            # 플레이어 발밑에 파티클 생성 (y좌표 오프셋 조절)
            particle_x = self.player.x + random.uniform(-10, 10)
            particle_y = self.player.y - 40 + random.uniform(-5, 5)
            new_particle = VFX_Run_Particle(particle_x, particle_y, self.particle_frames, 0.05, 2.0)
            self.player.particles.append(new_particle)


    def draw(self):
        # 파티클은 Player에서 그림

        # 마우스 위치 읽기
        mx = ctypes.c_int(0)
        my = ctypes.c_int(0)
        SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))

        # 마우스 x좌표에 따라 face_dir 설정
        if mx.value < self.player.x:
            self.player.face_dir = -1
        else:
            self.player.face_dir = 1

        flip = '' if self.player.face_dir == 1 else 'h'
        lower = self.lower_frames[self.frame]
        upper = self.upper_frames[self.frame]

        lw, lh = lower.w, lower.h
        uw, uh = upper.w, upper.h

        # 마우스 위치 읽어 pico2d 좌표계로 변환
        canvas_h = get_canvas_height()
        mouse_game_y = canvas_h - my.value

        # 마우스가 플레이어보다 위에 있으면 upper를 위에 그림
        if mouse_game_y > self.player.y:
            lower.clip_composite_draw(0, 0, lw, lh, 0, flip,self.player.x, self.player.y,
                                      lw * self.player.scale_factor, lh * self.player.scale_factor)
            upper.clip_composite_draw(0, 0, uw, uh, 0, flip,self.player.x, self.player.y,
                                      uw * self.player.scale_factor, uh * self.player.scale_factor)
        else:
            upper.clip_composite_draw(0, 0, uw, uh, 0, flip,self.player.x, self.player.y,
                                      uw * self.player.scale_factor, uh * self.player.scale_factor)
            lower.clip_composite_draw(0, 0, lw, lh, 0, flip,self.player.x, self.player.y,
                                      lw * self.player.scale_factor, lh * self.player.scale_factor)

class Idle:
    def __init__(self, player):
        self.player = player
        folder = os.path.join('resources', 'Texture_organize', 'Player_character', 'Adventurer')

        def load_seq(prefix):
            files = sorted([f for f in os.listdir(folder)
                           if isinstance(f, str) and f.startswith(prefix) and f.lower().endswith('.png')])
            return [load_image(os.path.join(folder, f)) for f in files]

        self.lower_frames = load_seq('Player_Adventurer_Idle_Lower')
        self.upper_frames = load_seq('Player_Adventurer_Idle_Upper')

        if not self.lower_frames or not self.upper_frames:
            raise RuntimeError(f'Idle frames not found in {folder}')

        self.frame = 0
        self.frame_time_acc = 0.0
        self.frame_duration = 0.12

    def enter(self, e):
        self.player.dir = [0, 0]

    def exit(self, e):
        pass

    def do(self):
        dt = framework.get_delta_time()

        self.frame_time_acc += dt
        while self.frame_time_acc >= self.frame_duration:
            self.frame_time_acc -= self.frame_duration
            self.frame = (self.frame + 1) % len(self.lower_frames)

    def draw(self):
        # 마우스 위치 읽기
        mx = ctypes.c_int(0)
        my = ctypes.c_int(0)
        SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))

        # 마우스 x좌표에 따라 face_dir 설정
        if mx.value < self.player.x:
            self.player.face_dir = -1
        else:
            self.player.face_dir = 1

        flip = '' if self.player.face_dir == 1 else 'h'
        lower = self.lower_frames[self.frame]
        upper = self.upper_frames[self.frame]

        lw, lh = lower.w, lower.h
        uw, uh = upper.w, upper.h

        # 마우스 위치 읽어 pico2d 좌표계로 변환
        canvas_h = get_canvas_height()
        mouse_game_y = canvas_h - my.value

        # 마우스가 플레이어보다 위에 있으면 upper를 위에 그림
        if mouse_game_y > self.player.y:
            lower.clip_composite_draw(0, 0, lw, lh, 0, flip,self.player.x, self.player.y,
                                      lw * self.player.scale_factor, lh * self.player.scale_factor)
            upper.clip_composite_draw(0, 0, uw, uh, 0, flip,self.player.x, self.player.y,
                                      uw * self.player.scale_factor, uh * self.player.scale_factor)
        else:
            upper.clip_composite_draw(0, 0, uw, uh, 0, flip,self.player.x, self.player.y,
                                      uw * self.player.scale_factor, uh * self.player.scale_factor)
            lower.clip_composite_draw(0, 0, lw, lh, 0, flip,self.player.x, self.player.y,
                                      lw * self.player.scale_factor, lh * self.player.scale_factor)


class Inventory:
    """인벤토리 상태: enter에서 이미지 로드, draw에서 중앙 오른쪽에 표시 (시뮬레이션 정지 없음)"""
    def __init__(self, player):
        self.player = player
        self.image = None
        self.scale = 1.0
        self.prev_state = None  # 이전 상태 저장용

    def enter(self, e):
        # 현재 상태를 이전 상태로 저장 (복귀용)
        self.prev_state = self.player.state_machine.cur_state

        # 이미지 지연 로드(오버레이에서도 사용 가능하도록 유지하되, 여기서는 그리지 않음)
        if self.image is None:
            img_path = os.path.join('resources', 'Texture_organize', 'UI', 'Inventory', 'InventoryBase_New1.png')
            try:
                self.image = load_image(img_path)
            except Exception as ex:
                print('Failed to load inventory image:', img_path, ex)
                self.image = None

        # 인벤토리 표시 플래그만 설정 (이동은 유지)
        self.player.inventory_open = True

    def exit(self, e):
        # 표시 플래그만 해제
        self.player.inventory_open = False

    def do(self):
        # 현재 키 상태에 따라 Idle/Run의 do를 동적으로 실행
        active_state = self.player.RUN if any(self.player.keys_down.values()) else self.player.IDLE
        active_state.do()

    def draw(self):
        # 현재 키 상태에 따라 Idle/Run의 draw를 먼저 실행
        active_state = self.player.RUN if any(self.player.keys_down.values()) else self.player.IDLE
        active_state.draw()
        # 인벤토리 이미지는 별도의 UI 레이어(InventoryOverlay)에서 최상단으로 그림


class Player:
    def __init__(self):
        self.x = get_canvas_width() // 2
        self.y = get_canvas_height() // 2
        self.frame = 0
        self.dir = [0, 0]  # x, y 방향 벡터
        self.face_dir = 1
        self.scale_factor = 3.0
        self.keys_down = {'w': False, 'a': False, 's': False, 'd': False}
        self.moving = False # 이동 상태 플래그
        self.particles = [] # 파티클 리스트를 Player로 이동
        self.attack_effects = [] # 공격 이펙트 리스트

        # 장비 매니저 초기화
        self.equipment_manager = EquipmentManager(self)

        # 기본 무기 장착 (Tier1 검과 방패)
        sword_path = os.path.join('resources', 'Texture_organize', 'Weapon', 'SwordANDShield', 'Tier1', 'Sword_Tier1.png')
        shield_path = os.path.join('resources', 'Texture_organize', 'Weapon', 'SwordANDShield', 'Tier1', 'Shield_Tier1.png')

        self.sword = Sword(self, sword_path, scale=3.0)
        self.shield = Shield(self, shield_path, scale=3.0)

        self.equipment_manager.equip(self.sword)
        self.equipment_manager.equip(self.shield)

        # 상태 정의
        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.INVENTORY = Inventory(self)

        # 전투 플래그(전투중일 때 인벤토리 열지 않음)
        self.in_combat = False
        self.inventory_open = False

        # 상태 변환에 대한 매핑
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {move_event: self.RUN, Tab_down: self.INVENTORY},
                self.RUN: {stop_event: self.IDLE, Tab_down: self.INVENTORY},
                self.INVENTORY: {Tab_down: None},  # Tab_down은 특수 처리 필요
            }
        )

    def update(self):
        self.state_machine.update()

        # 파티클 업데이트 (상태와 무관하게 항상 실행)
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        # 공격 이펙트 업데이트
        for effect in self.attack_effects:
            effect.update()
        self.attack_effects = [e for e in self.attack_effects if e.life > 0]

        # 장비 업데이트
        self.equipment_manager.update()

    def draw(self):
        # 파티클 먼저 그리기 (캐릭터 뒤에 나타나도록)
        for p in self.particles:
            p.draw()

        # 공격 이펙트 그리기 (검 뒤에)
        for effect in self.attack_effects:
            effect.draw()

        # 뒤에 그려질 장비 (검)
        self.equipment_manager.draw_back()

        # 그 다음 캐릭터 그리기
        self.state_machine.draw()

        # 앞에 그려질 장비 (방패)
        self.equipment_manager.draw_front()

    def handle_event(self, event):
        self.equipment_manager.handle_event(event)

        # Tab 키 입력 처리 (인벤토리 열기/닫기)
        if event.type == SDL_KEYDOWN and event.key == SDLK_TAB:
            # 인벤토리 닫기 직전, 현재 키 상태에 맞춰 복귀 상태 설정
            if self.inventory_open:
                self.INVENTORY.prev_state = self.RUN if any(self.keys_down.values()) else self.IDLE
            self.state_machine.handle_state_event(('INPUT', event))
            return

        # 인벤토리 열려 있으면: WASD 입력으로 dir을 정상 업데이트(이동 허용),
        # 다만 상태 이벤트(MOVE/STOP)는 발생시키지 않음
        if self.inventory_open:
            if event.type == SDL_KEYDOWN:
                if event.key == SDLK_w: self.keys_down['w'] = True; self.dir[1] += 1
                elif event.key == SDLK_a: self.keys_down['a'] = True; self.dir[0] -= 1
                elif event.key == SDLK_s: self.keys_down['s'] = True; self.dir[1] -= 1
                elif event.key == SDLK_d: self.keys_down['d'] = True; self.dir[0] += 1
            elif event.type == SDL_KEYUP:
                if event.key == SDLK_w: self.keys_down['w'] = False; self.dir[1] -= 1
                elif event.key == SDLK_a: self.keys_down['a'] = False; self.dir[0] += 1
                elif event.key == SDLK_s: self.keys_down['s'] = False; self.dir[1] += 1
                elif event.key == SDLK_d: self.keys_down['d'] = False; self.dir[0] -= 1
            return

        # 키보드 입력 처리(일반 상태)
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_w: self.keys_down['w'] = True; self.dir[1] += 1
            elif event.key == SDLK_a: self.keys_down['a'] = True; self.dir[0] -= 1
            elif event.key == SDLK_s: self.keys_down['s'] = True; self.dir[1] -= 1
            elif event.key == SDLK_d: self.keys_down['d'] = True; self.dir[0] += 1
        elif event.type == SDL_KEYUP:
            if event.key == SDLK_w: self.keys_down['w'] = False; self.dir[1] -= 1
            elif event.key == SDLK_a: self.keys_down['a'] = False; self.dir[0] += 1
            elif event.key == SDLK_s: self.keys_down['s'] = False; self.dir[1] += 1
            elif event.key == SDLK_d: self.keys_down['d'] = False; self.dir[0] -= 1

        # 상태 전환 이벤트 생성 (일반 상태에서만)
        is_moving = any(self.keys_down.values())
        if is_moving and not self.moving:
            self.state_machine.handle_state_event(('MOVE', event))
            self.moving = True
        elif not is_moving and self.moving:
            self.state_machine.handle_state_event(('STOP', event))
            self.moving = False

class VFX_Run_Particle:
    def __init__(self, x, y, frames, frame_duration, scale):
        self.x, self.y = x, y
        self.frames = frames
        self.frame = 0
        self.frame_time_acc = 0.0
        self.frame_duration = frame_duration
        self.scale_factor = scale
        self.life = len(frames) * frame_duration

    def update(self):
        dt = framework.get_delta_time()
        self.life -= dt
        if self.life < 0:
            return False  # 수명이 다하면 False 반환

        self.frame_time_acc += dt
        if self.frame_time_acc >= self.frame_duration:
            self.frame_time_acc -= self.frame_duration
            self.frame = (self.frame + 1)
        return True

    def draw(self):
        if self.frame < len(self.frames):
            image = self.frames[self.frame]
            image.draw(self.x, self.y + 20, image.w * self.scale_factor, image.h * self.scale_factor)


# VFX 전역 배율 설정: 전체 이펙트 크기와 거리(범위)를 일괄 조정
VFX_GLOBAL_SCALE_MULT = 0.7   # 이펙트 크기 0.7배
VFX_GLOBAL_RANGE_MULT = 0.8   # 이펙트 거리 0.8배

class VFX_Tier1_Sword_Swing:
    """검 공격 이펙트 VFX"""
    def __init__(self, x, y, angle, flip, scale=4.5, range_factor=60, variant=1):
        import math

        # 전역 배율을 적용한 range_factor/scale 사용
        range_factor = range_factor * VFX_GLOBAL_RANGE_MULT
        scale = scale * VFX_GLOBAL_SCALE_MULT

        # 받은 위치에서 angle 방향으로 range_factor만큼 떨어진 위치 계산
        temp_x = range_factor * math.cos(angle)
        temp_y = range_factor * math.sin(angle)

        self.x = x + temp_x
        self.y = y + temp_y
        
        # 각도 조정: 마우스가 오른쪽(0도~90도, 270도~360도)일 때 -90도, 왼쪽일 때 +90도
        angle_deg = math.degrees(angle) % 360
        if 90 < angle_deg < 270:  # 왼쪽
            self.angle = angle + math.radians(90)
        else:  # 오른쪽
            self.angle = angle - math.radians(90)
        
        self.flip = flip
        self.scale_factor = scale

        # 이펙트 이미지 로드
        fx_folder = os.path.join('resources', 'Texture_organize', 'Weapon', 'SwordANDShield', 'Swing_FX')
        if variant == 1:
            self.frames = [
                load_image(os.path.join(fx_folder, 'Sword0_Swing0.png')),
                load_image(os.path.join(fx_folder, 'Sword0_Swing1.png'))
            ]
        elif variant == 2:
            # 콤보 전용 스프라이트
            self.frames = [
                load_image(os.path.join(fx_folder, 'Sword0_Swing2_0.png')),
                load_image(os.path.join(fx_folder, 'Sword0_Swing2_1.png'))
            ]
        elif variant == 3:
            # Heavy swing (3스테이지) - 여러 프레임
            self.frames = [
                load_image(os.path.join(fx_folder, 'Sword0_HeavySwingN_0.png')),
                load_image(os.path.join(fx_folder, 'Sword0_HeavySwingN_1.png')),
                load_image(os.path.join(fx_folder, 'Sword0_HeavySwingN_2.png')),
                load_image(os.path.join(fx_folder, 'Sword0_HeavySwingN_3.png'))
            ]
        else:
            # 안전망: 기본으로 variant 1 사용
            self.frames = [
                load_image(os.path.join(fx_folder, 'Sword0_Swing0.png')),
                load_image(os.path.join(fx_folder, 'Sword0_Swing1.png'))
            ]

        self.frame = 0
        self.frame_time_acc = 0.0
        self.frame_duration = 0.05  # 각 프레임당 0.05초
        self.life = len(self.frames) * self.frame_duration  # 총 수명

    def update(self):
        dt = framework.get_delta_time()
        self.life -= dt
        if self.life <= 0:
            return False  # 수명이 다하면 False 반환

        self.frame_time_acc += dt
        if self.frame_time_acc >= self.frame_duration:
            self.frame_time_acc -= self.frame_duration
            self.frame += 1
            if self.frame >= len(self.frames):
                self.frame = len(self.frames) - 1  # 마지막 프레임 유지
        return True

    def draw(self):
        if self.frame < len(self.frames):
            image = self.frames[self.frame]
            image.clip_composite_draw(
                0, 0, image.w, image.h,
                self.angle, self.flip,
                self.x, self.y,
                image.w * self.scale_factor,
                image.h * self.scale_factor
            )
