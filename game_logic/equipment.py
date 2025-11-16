import ctypes
import math
import os
from pico2d import load_image, get_canvas_height
from sdl2 import SDL_GetMouseState, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT
from . import framework


# 방패 범위 이펙트 클래스
class ShieldRangeEffect:
    """방패 범위 표시 이펙트 - world['effects_front']에서 관리"""
    _range_image = None  # 클래스 변수로 이미지 공유

    def __init__(self, player, shield):
        if ShieldRangeEffect._range_image is None:
            range_path = os.path.join('resources', 'Texture_organize', 'Weapon', 'shieldRange.png')
            try:
                ShieldRangeEffect._range_image = load_image(range_path)
            except Exception as ex:
                print('Failed to load shield range image:', ex)
                ShieldRangeEffect._range_image = None

        self.player = player
        self.shield = shield
        self.range_scale = 4.0

    def update(self):
        # 방패가 blocking 상태가 아니면 제거
        if not self.shield.blocking:
            return False
        return True

    def draw(self):
        if ShieldRangeEffect._range_image is None:
            return

        base_offset = -math.pi / 2
        theta = self.shield.range_angle + base_offset
        half_h_scaled = (ShieldRangeEffect._range_image.h * self.range_scale) * 0.5
        draw_x = self.player.x - half_h_scaled * math.sin(theta)
        draw_y = self.player.y + half_h_scaled * math.cos(theta)

        ShieldRangeEffect._range_image.clip_composite_draw(
            0, 0, ShieldRangeEffect._range_image.w, ShieldRangeEffect._range_image.h,
            theta, '',
            draw_x, draw_y,
            ShieldRangeEffect._range_image.w * self.range_scale,
            ShieldRangeEffect._range_image.h * self.range_scale
        )


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
        self.offset_x = -10  # 기본 X 오프셋(사용 안 함)
        self.offset_y = -10  # Y 오프셋 유지

        # 우클릭 방패 전개 상태
        self.blocking = False
        self.range_angle = 0.0

        # 방패 범위 이펙트 참조 (world['effects_front']에서 관리)
        self.range_effect = None

        # 바라보는 방향으로 방패를 살짝 앞으로 이동시키는 오프셋(픽셀)
        self.forward_offset = 18

    def start_block(self):
        self.blocking = True

    def end_block(self):
        self.blocking = False

    def update(self):
        """방패: 우클릭 유지 시 각도를 커서 방향으로 갱신"""
        # 인벤토리가 열려 있으면 방패 입력/전개 무시
        if getattr(self.player, 'inventory_open', False):
            self.blocking = False
            if self.is_attacking:
                dt = framework.get_delta_time()
                self.attack_timer += dt
                if self.attack_timer >= self.attack_duration:
                    self.is_attacking = False
                    self.attack_timer = 0.0
            return

        # 각도는 항상 계산해둠 (범위 이미지를 위한 값)
        mx = ctypes.c_int(0)
        my = ctypes.c_int(0)
        state = SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))
        canvas_h = get_canvas_height()
        mouse_game_y = canvas_h - my.value
        dx = mx.value - self.player.x
        dy = mouse_game_y - self.player.y
        self.range_angle = math.atan2(dy, dx)

        # 이전 blocking 상태 저장
        was_blocking = self.blocking

        # 프레임별 우클릭 유지 여부를 직접 폴링하여 blocking 동기화 (이벤트 누락 대비)
        try:
            right_mask = 1 << (SDL_BUTTON_RIGHT - 1)
            self.blocking = bool(state & right_mask)
        except Exception:
            pass

        # blocking 상태가 변경되었을 때 이펙트 생성/제거
        if self.blocking and not was_blocking:
            # blocking 시작: 이펙트 생성
            if hasattr(self.player, 'world') and self.player.world and 'effects_front' in self.player.world:
                self.range_effect = ShieldRangeEffect(self.player, self)
                self.player.world['effects_front'].append(self.range_effect)
        elif not self.blocking and was_blocking:
            # blocking 종료: 이펙트는 자동으로 제거됨 (update에서 False 반환)
            self.range_effect = None

        # 기존 공격 타이머 로직 유지(필요 시)
        if self.is_attacking:
            dt = framework.get_delta_time()
            self.attack_timer += dt
            if self.attack_timer >= self.attack_duration:
                self.is_attacking = False
                self.attack_timer = 0.0

    def attack(self):
        """방패는 막기 동작 (현재는 사용하지 않음)"""
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 0.0
            print(f"방패로 막기!")

    def draw(self):
        """방패 본체 그리기 (범위 이미지는 world['effects_front']에서 관리)"""
        # 방패 본체는 회전 없이 플레이어 앞에 고정
        flip = 'h' if self.player.face_dir == -1 else ''
        # 전개 중일 때만 앞으로 이동, 아니면 기존의 작은 좌우 오프셋 유지
        if self.blocking:
            local_offset_x = self.forward_offset if self.player.face_dir == 1 else -self.forward_offset
        else:
            local_offset_x = 10 if self.player.face_dir == -1 else -10
        weapon_x = self.player.x + local_offset_x
        weapon_y = self.player.y + self.offset_y

        self.image.clip_composite_draw(
            0, 0, self.image.w, self.image.h,
            0, flip,
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

        # 스테이지별(콤보) 시간 설정 (스테이지1 = 기본, 스테이지2 = 콤보)
        self.stage = 1
        # 기본(보정 전) 시간값 저장
        self.stage1_attack_duration_base = 0.2  # 공격 모션 시간 (1스테이지)
        self.stage1_attack_recovery_base = 0.3  # 후딜 (1스테이지)
        self.stage2_attack_duration_base = 0.18  # 공격 모션 시간 (콤보)
        self.stage2_attack_recovery_base = 0.35  # 후딜 (콤보)
        self.stage3_attack_duration_base = 0.28  # 3스테이지 모션 시간
        self.stage3_attack_recovery_base = 0.4   # 3스테이지 후딜

        # 현재 활성화된 공격 시간 값 (초기값은 1스테이지 보정 적용)
        self.attack_duration = self.stage1_attack_duration_base
        self.attack_recovery = self.stage1_attack_recovery_base
        self.total_attack_time = self.attack_duration + self.attack_recovery

        self.base_angle_offset = math.radians(25)  # 기본 각도 오프셋

        # 공격 모션 관련 변수
        self.attack_progress = 0.0  # 0.0 ~ 1.0
        self.attack_angle_range = -math.radians(205)  # 0도 ~ 270도 회전 (검 자체 회전)
        self.y_offset_down = -50  # progress 0.5까지 내려갈 y 오프셋

        # 자전 및 공전 각도 범위 추가
        self.rotation_angle_range = -math.radians(270)  # 자전: 0도 ~ 270도
        self.orbit_angle_range = -math.radians(205)  # 공전: 0도 ~ 205도

        # 콤보 관련 플래그
        self.combo_queued = False  # 후딜 중에 콤보 입력이 들어왔는지

    def _apply_speed(self, stage: int):
        """플레이어 stats.attack_speed로 해당 스테이지 시간값을 보정한다."""
        speed = 1.0
        try:
            if hasattr(self.player, 'stats'):
                speed = max(0.1, float(self.player.stats.get('attack_speed')))
        except Exception:
            speed = 1.0
        if stage == 1:
            self.attack_duration = self.stage1_attack_duration_base / speed
            self.attack_recovery = self.stage1_attack_recovery_base / speed
        elif stage == 2:
            self.attack_duration = self.stage2_attack_duration_base / speed
            self.attack_recovery = self.stage2_attack_recovery_base / speed
        elif stage == 3:
            self.attack_duration = self.stage3_attack_duration_base / speed
            self.attack_recovery = self.stage3_attack_recovery_base / speed
        else:
            pass
        self.total_attack_time = self.attack_duration + self.attack_recovery

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

            # 스테이지별 종료 처리
            if self.attack_timer >= self.total_attack_time:
                # 3스테이지 종료 처리
                if self.stage == 3:
                    self.is_attacking = False
                    self.attack_timer = 0.0
                    self.attack_progress = 0.0
                    self.stage = 1
                    # 기본 스테이지 시간 복원
                    self.attack_duration = self.stage1_attack_duration_base
                    self.attack_recovery = self.stage1_attack_recovery_base
                    self.total_attack_time = self.attack_duration + self.attack_recovery
                    self.combo_queued = False
                # 2스테이지 종료 처리
                elif self.stage == 2:
                    self.is_attacking = False
                    self.attack_timer = 0.0
                    self.attack_progress = 0.0
                    self.stage = 1
                    self.attack_duration = self.stage1_attack_duration_base
                    self.attack_recovery = self.stage1_attack_recovery_base
                    self.total_attack_time = self.attack_duration + self.attack_recovery
                    self.combo_queued = False
                else:
                    # 1스테이지 종료
                    self.is_attacking = False
                    self.attack_timer = 0.0
                    self.attack_progress = 0.0
                    self.combo_queued = False

    def attack(self):
        """공격 시작

        동작 요약:
        - 비공격 중이면 1스테이지 공격 시작
        - 공격 중(후딜 영역)에 클릭하면 즉시 2스테이지(콤보) 공격으로 전환
        """
        # 비공격 상태에서 시작
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 0.0
            self.attack_progress = 0.0
            self.stage = 1
            # 스탯 보정 적용
            self._apply_speed(1)
            print(f"{self.weapon_type} 공격! (stage 1)")

            # 공격 이펙트 생성
            from .player import VFX_Tier1_Sword_Swing

            angle_deg = math.degrees(self.angle) % 360
            if 90 < angle_deg < 270:  # 왼쪽 영역
                flip = 'vh'
            else:
                flip = 'h'

            attack_vfx = VFX_Tier1_Sword_Swing(
                self.player.x,
                self.player.y,
                self.angle,
                flip,
                scale=4.5,
                range_factor=60,
                variant=1,
                owner=self.player
            )
            # world['effects_front']에 추가 (없으면 player에 추가)
            if hasattr(self.player, 'world') and self.player.world and 'effects_front' in self.player.world:
                self.player.world['effects_front'].append(attack_vfx)
            else:
                self.player.attack_effects.append(attack_vfx)

            return True

        # 공격 중일 때: 후딜 중에 콤보 입력을 받아 단계별 전환
        else:
            # 1스테이지 후딜에서 클릭 -> 2스테이지
            if self.attack_timer >= self.attack_duration and self.stage == 1:
                # 즉시 콤보(2스테이지)로 전환
                self.stage = 2
                self.attack_timer = 0.0
                self.attack_progress = 0.0
                # 스탯 보정 적용
                self._apply_speed(2)
                self.combo_queued = True
                print(f"{self.weapon_type} 콤보! (stage 2)")

                # 콤보용 이펙트 생성
                from .player import VFX_Tier1_Sword_Swing

                angle_deg = math.degrees(self.angle) % 360
                flip = 'vh' if 90 < angle_deg < 270 else 'h'

                attack_vfx = VFX_Tier1_Sword_Swing(
                    self.player.x,
                    self.player.y,
                    self.angle,
                    flip,
                    scale=5.5,
                    range_factor=70,
                    variant=2
                )
                # world['effects_front']에 추가 (없으면 player에 추가)
                if hasattr(self.player, 'world') and self.player.world and 'effects_front' in self.player.world:
                    self.player.world['effects_front'].append(attack_vfx)
                else:
                    self.player.attack_effects.append(attack_vfx)

                return True

            # 2스테이지 후딜에서 클릭 -> 3스테이지 (헤비 스윙)
            if self.attack_timer >= self.attack_duration and self.stage == 2:
                self.stage = 3
                self.attack_timer = 0.0
                self.attack_progress = 0.0
                # 스탯 보정 적용
                self._apply_speed(3)
                self.combo_queued = True
                print(f"{self.weapon_type} 헤비 스윙! (stage 3)")

                # 3스테이지 전용 이펙트 생성 (variant=3)
                from .player import VFX_Tier1_Sword_Swing

                angle_deg = math.degrees(self.angle) % 360
                flip = 'vh' if 90 < angle_deg < 270 else 'h'

                attack_vfx = VFX_Tier1_Sword_Swing(
                    self.player.x,
                    self.player.y,
                    self.angle,
                    flip,
                    scale=6.0,
                    range_factor=90,
                    variant=3,
                    owner=self.player
                )
                # world['effects_front']에 추가 (없으면 player에 추가)
                if hasattr(self.player, 'world') and self.player.world and 'effects_front' in self.player.world:
                    self.player.world['effects_front'].append(attack_vfx)
                else:
                    self.player.attack_effects.append(attack_vfx)

                return True

            # 그 외(공격 중이지만 아직 공격 모션 중이거나 이미 최고 단계면 무시)
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

        # 2스테이지(콤보)일 때는 회전 각도를 반대 방향으로 돌림
        # 반전 적용 조건: 현재 스테이지가 2이고 (공격 모션 구간)일 때만 자전 반전 적용
        invert_rotation = (getattr(self, 'stage', 1) == 2 and self.attack_timer < self.attack_duration)
        if invert_rotation:
            # 자전만 반전하면 검의 회전 방향만 역전되어 자연스러운 콤보 느낌을 줍니다.
            sword_rotation = -sword_rotation

        # base_angle_offset은 항상 동일하게 사용하여 위치 변화 발생을 막음
        base_offset = self.base_angle_offset

        # 마우스가 왼쪽에 있을 때 (각도가 90도 ~ 270도 범위)
        angle_deg = math.degrees(self.angle) % 360

        # position_angle(orbit) 먼저 계산
        if 90 < angle_deg < 270:  # 왼쪽 영역
            flip = 'v'  # 수직 반전
            # position은 orbit 기반으로 계산 (self.angle - orbit_angle_offset)
            position_angle = self.angle - orbit_angle_offset
        else:  # 오른쪽 영역
            flip = ''
            # position은 orbit 기반으로 계산 (self.angle + orbit_angle_offset)
            position_angle = self.angle + orbit_angle_offset

        # final_angle은 position_angle을 기준으로 검 자체의 자전(sword_rotation)을 더/빼서 계산
        # direction에 따라 검의 자전 방향을 더하거나 뺍니다.
        if 90 < angle_deg < 270:
            # 왼쪽
            final_angle = position_angle - sword_rotation
        else:
            # 오른쪽
            final_angle = position_angle + sword_rotation

        # 검의 위치 계산 (캐릭터 중심으로 공전하도록 position_angle 사용)
        # 공전 반경은 offset_x(거리)를 사용하고, position_angle(orbit 기반)을 사용합니다.
        weapon_x = self.player.x + self.offset_x * math.cos(position_angle)
        weapon_y = self.player.y + self.offset_y + self.offset_x * math.sin(position_angle) + y_offset_modifier

        # 회전된 무기 그리기 (검 자체 중심으로 회전)
        self.image.clip_composite_draw(
            0, 0, self.image.w, self.image.h,
            final_angle + base_offset, flip,
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
        """장비 이벤트 처리 (좌클릭: 공격, 우클릭: 방패 전개 표시)"""
        # 마우스 좌클릭 시 공격(검)
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            for equipment in self.back_equipment:
                equipment.attack()

        # 마우스 우클릭: 방패 범위 표시 시작/종료
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_RIGHT:
            # 디버그: 우클릭 다운 수신
            try:
                print('[Shield] RIGHT DOWN')
            except Exception:
                pass
            for equipment in self.front_equipment:
                if isinstance(equipment, Shield):
                    equipment.start_block()
        elif event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_RIGHT:
            # 디버그: 우클릭 업 수신
            try:
                print('[Shield] RIGHT UP')
            except Exception:
                pass
            for equipment in self.front_equipment:
                if isinstance(equipment, Shield):
                    equipment.end_block()

    def draw_back(self):
        """캐릭터 뒤에 그려질 장비들"""
        for equipment in self.back_equipment:
            equipment.draw()

    def draw_front(self):
        """캐릭터 앞에 그려질 장비들"""
        for equipment in self.front_equipment:
            equipment.draw()
