import ctypes
import os
import random
from math import radians

from pico2d import load_image, get_time, get_canvas_height, get_canvas_width
from sdl2 import (SDL_KEYDOWN, SDLK_SPACE, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDL_GetMouseState,
                  SDLK_a, SDLK_d, SDLK_w, SDLK_s)

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
        # 상태 변환에 대한 매핑
        self.state_machine = StateMachine(
            self.IDLE,
        {
                self.IDLE: {move_event: self.RUN},
                self.RUN: {stop_event: self.IDLE},
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
        # 장비 이벤트 먼저 처리 (공격 등)
        self.equipment_manager.handle_event(event)

        # 키보드 입력 처리
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

        # 상태 전환 이벤트 생성
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


class VFX_Tier1_Sword_Swing:
    """검 공격 이펙트 VFX"""
    def __init__(self, x, y, angle, flip, scale=4.5, range_factor=60):
        import math

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
