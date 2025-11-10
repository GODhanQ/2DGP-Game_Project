# 패키지 내부 모듈을 직접 실행할 경우 친절한 안내 후 종료
if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    import sys
    print("이 모듈은 game_logic 패키지 내부 모듈입니다. 프로젝트 루트에서 main.py를 실행하세요.")
    sys.exit(1)

import ctypes
import os
import random
import time

from pico2d import load_image, get_canvas_height, get_canvas_width
from sdl2 import (SDL_KEYDOWN, SDL_KEYUP, SDLK_a, SDLK_d, SDLK_w, SDLK_s, SDLK_TAB, SDL_GetMouseState,
                   SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT)

from .equipment import EquipmentManager, Sword, Shield
from .state_machine import StateMachine
from . import framework
# 인벤토리 데이터 모델 import
from .inventory import InventoryData, seed_debug_inventory
from .stats import PlayerStats, StatModifier

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

        # 현재 스탯 기반 이동 속도 사용
        moving_speed = self.player.stats.get('move_speed') if hasattr(self.player, 'stats') else self.moving_speed
        dir_magnitude = (self.player.dir[0] ** 2 + self.player.dir[1] ** 2) ** 0.5
        if dir_magnitude > 0:
            norm_dir_x = self.player.dir[0] / dir_magnitude
            norm_dir_y = self.player.dir[1] / dir_magnitude
            if self.player.x + norm_dir_x * moving_speed * dt > get_canvas_width():
                self.player.x = get_canvas_width()
            elif self.player.x + norm_dir_x * moving_speed * dt < 0:
                self.player.x = 0
            else: self.player.x += norm_dir_x * moving_speed * dt
            if self.player.y + norm_dir_y * moving_speed * dt > get_canvas_height():
                self.player.y = get_canvas_height()
            elif self.player.y + norm_dir_y * moving_speed * dt < 0:
                self.player.y = 0
            else: self.player.y += norm_dir_y * moving_speed * dt


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

        # 인벤토리 데이터 생성 및 디버그 아이템 채우기
        self.inventory = InventoryData(cols=6, rows=5)
        try:
            seed_debug_inventory(self.inventory)
        except Exception as ex:
            print('[Player] 디버그 인벤토리 시드 실패:', ex)

        # 스탯 시스템
        self.stats = PlayerStats()
        # 인벤토리 패시브 적용
        try:
            self.rebuild_inventory_passives()
        except Exception as ex:
            print('[Player] 패시브 재구성 실패:', ex)

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

        # 전투 플래그(전투중엔 인벤토리 안 염)
        self.in_combat = False
        self.inventory_open = False

        # 상태 전환에 대한 매핑
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {move_event: self.RUN, Tab_down: self.INVENTORY},
                self.RUN: {stop_event: self.IDLE, Tab_down: self.INVENTORY},
                self.INVENTORY: {Tab_down: None},
            }
        )

    def update(self):
        self.state_machine.update()

        # 스탯 버프 업데이트(소비형 지속시간 관리)
        if hasattr(self, 'stats'):
            self.stats.update()

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

    # 인벤토리 패시브 재적용
    def rebuild_inventory_passives(self):
        prefix = 'passive:'
        self.stats.clear_by_prefix(prefix)
        # 모든 슬롯 순회
        try:
            for r in range(self.inventory.rows):
                for c in range(self.inventory.cols):
                    slot = self.inventory.get_slot(r, c)
                    if slot.is_empty():
                        continue
                    item = slot.item
                    if getattr(item, 'passive', None):
                        # 수량만큼 배수 적용(스택형 패시브 고려)
                        qty = max(1, slot.quantity)
                        values = {k: v * qty for k, v in item.passive.items()}
                        mod_id = f'{prefix}{item.id}:{r},{c}'
                        self.stats.add_modifier(StatModifier(mod_id, values, duration=None))
        except Exception as ex:
            print('[Player] 패시브 적용 중 오류:', ex)

    # 소비형 아이템 사용 처리
    def consume_item_at(self, r: int, c: int):
        try:
            slot = self.inventory.get_slot(r, c)
        except Exception as ex:
            print('[Player] 소비 실패: 잘못된 슬롯', ex)
            return False
        if slot.is_empty() or not getattr(slot.item, 'consumable', None):
            return False
        item = slot.item
        values = dict(item.consumable)
        duration = item.consume_duration
        mod_id = f'consumable:{item.id}:{r},{c}:{int(time.time()*1000)%100000}'
        self.stats.add_modifier(StatModifier(mod_id, values, duration=duration))
        # 1개 소모
        self.inventory.remove_from(r, c, 1)
        # 아이템의 이펙트 재생(있다면)
        vfx_fn = (getattr(item, 'on_consume_vfx', None)
                  or getattr(item, '_play_consume_vfx', None)
                  or getattr(item, 'consume_effect', None))
        if callable(vfx_fn):
            try:
                # prefer self.world (assigned by play_mode) so VFX are appended to the correct world dict
                vfx_world = getattr(self, 'world', None)
                # debug log
                try:
                    print(f"[Player] triggering vfx for {getattr(item, 'name', item.id if hasattr(item,'id') else 'Unknown')} world={'set' if vfx_world is not None else 'None'})")
                except Exception:
                    pass
                vfx_fn(self, world=vfx_world, x=getattr(self, 'x', None), y=getattr(self, 'y', None))
            except Exception as ex:
                print(f'[Player] 아이템 소비 이펙트 오류 ({item.name}):', ex)
        # 패시브 재적용(수량 변화로 인한 패시브 변경 가능성 고려)
        self.rebuild_inventory_passives()
        print(f"[Player] 소비: {item.name} -> {values} ({duration}s)")
        return True

    # 신규: 입력 처리 - 상태머신과 장비 매니저로 이벤트 전달, 이동 벡터 관리
    def handle_event(self, event):
        try:
            from sdl2 import SDL_KEYDOWN, SDL_KEYUP, SDLK_w, SDLK_a, SDLK_s, SDLK_d
        except Exception:
            SDL_KEYDOWN = SDL_KEYUP = None
            SDLK_w = SDLK_a = SDLK_s = SDLK_d = None

        # 1) 장비 매니저에 항상 전달(매니저 내부에서 인벤토리 오픈시 무시 처리)
        try:
            if hasattr(self, 'equipment_manager') and hasattr(self.equipment_manager, 'handle_event'):
                self.equipment_manager.handle_event(event)
        except Exception as ex:
            print('[Player] equipment_manager.handle_event 오류:', ex)

        # 2) 상태머신으로 원본 입력 이벤트 전달(Tab 매핑 등 predicates가 처리)
        try:
            if hasattr(self, 'state_machine') and hasattr(self.state_machine, 'handle_state_event'):
                self.state_machine.handle_state_event(('INPUT', event))
        except Exception as ex:
            print('[Player] state_machine 입력 이벤트 처리 오류:', ex)

        # 3) WASD 이동 상태 관리 -> MOVE/STOP 이벤트 생성
        moved_before = any(self.keys_down.values())
        try:
            if SDL_KEYDOWN is not None and event.type == SDL_KEYDOWN:
                if event.key == SDLK_w:
                    self.keys_down['w'] = True
                    self.dir[1] = 1
                elif event.key == SDLK_s:
                    self.keys_down['s'] = True
                    self.dir[1] = -1
                elif event.key == SDLK_a:
                    self.keys_down['a'] = True
                    self.dir[0] = -1
                elif event.key == SDLK_d:
                    self.keys_down['d'] = True
                    self.dir[0] = 1
            elif SDL_KEYUP is not None and event.type == SDL_KEYUP:
                if event.key == SDLK_w:
                    self.keys_down['w'] = False
                    self.dir[1] = 1 if self.keys_down['w'] else ( -1 if self.keys_down['s'] else 0)
                elif event.key == SDLK_s:
                    self.keys_down['s'] = False
                    self.dir[1] = -1 if self.keys_down['s'] else ( 1 if self.keys_down['w'] else 0)
                elif event.key == SDLK_a:
                    self.keys_down['a'] = False
                    self.dir[0] = -1 if self.keys_down['a'] else ( 1 if self.keys_down['d'] else 0)
                elif event.key == SDLK_d:
                    self.keys_down['d'] = False
                    self.dir[0] = 1 if self.keys_down['d'] else ( -1 if self.keys_down['a'] else 0)
        except Exception:
            pass

        moved_after = any(self.keys_down.values())
        try:
            if not moved_before and moved_after:
                # 시작 이동
                if hasattr(self, 'state_machine'):
                    self.state_machine.handle_state_event(('MOVE', None))
            elif moved_before and not moved_after:
                # 이동 종료
                if hasattr(self, 'state_machine'):
                    self.state_machine.handle_state_event(('STOP', None))
        except Exception as ex:
            print('[Player] MOVE/STOP 이벤트 처리 오류:', ex)

    # 신규: 렌더링 - 장비/플레이어/이펙트 순서대로 그리기
    def draw(self):
        # 1) 캐릭터 뒤 장비
        try:
            if hasattr(self, 'equipment_manager'):
                self.equipment_manager.draw_back()
        except Exception:
            pass

        # 2) 현재 상태 스프라이트(Idle/Run/Inventory)
        try:
            if hasattr(self, 'state_machine'):
                self.state_machine.draw()
        except Exception:
            pass

        # 3) 캐릭터 앞 장비(방패 등)
        try:
            if hasattr(self, 'equipment_manager'):
                self.equipment_manager.draw_front()
        except Exception:
            pass

        # 4) 파티클/공격 이펙트
        try:
            for p in getattr(self, 'particles', []):
                if hasattr(p, 'draw'):
                    p.draw()
            for e in getattr(self, 'attack_effects', []):
                if hasattr(e, 'draw'):
                    e.draw()
        except Exception:
            pass

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
