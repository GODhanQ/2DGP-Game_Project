import ctypes
import math
import os
from pico2d import load_image, get_canvas_height, get_canvas_width
from sdl2 import SDL_GetMouseState, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT
import game_framework as framework


def get_mouse_world_position(player):
    """
    마우스 화면 좌표를 월드 좌표로 변환하는 헬퍼 함수
    카메라 스크롤을 고려하여 정확한 월드 좌표를 반환

    Args:
        player: 플레이어 객체 (world 참조를 통해 camera 접근)

    Returns:
        tuple: (world_x, world_y) 월드 좌표계에서의 마우스 위치
    """
    # 마우스 화면 좌표 가져오기
    mx = ctypes.c_int(0)
    my = ctypes.c_int(0)
    SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))

    # pico2d 좌표계로 변환 (Y축 반전)
    canvas_h = get_canvas_height()
    canvas_w = get_canvas_width()
    mouse_screen_x = mx.value
    mouse_screen_y = canvas_h - my.value

    # 카메라 오프셋 적용하여 월드 좌표로 변환
    # play_mode와 lobby_mode 모두에서 카메라 가져오기
    camera = None
    try:
        # 먼저 play_mode에서 카메라 가져오기 시도
        import game_logic.play_mode as play
        camera = getattr(play, 'camera', None)

        # play_mode 카메라가 없으면 lobby_mode에서 시도
        if camera is None:
            import game_logic.lobby_mode as lobby
            camera = getattr(lobby, 'camera', None)
    except Exception as ex:
        # 카메라 가져오기 실패 시 None 유지
        pass

    if camera is not None:
        # 화면 좌표 -> 월드 좌표 변환
        # camera.apply()의 역연산: world_pos = screen_pos - (screen_center - camera_pos)
        half_w = canvas_w // 2
        half_h = canvas_h // 2
        world_x = mouse_screen_x - half_w + camera.x
        world_y = mouse_screen_y - half_h + camera.y
    else:
        # 카메라가 없으면 화면 좌표 그대로 사용
        world_x = mouse_screen_x
        world_y = mouse_screen_y

    return world_x, world_y


# 방패 범위 이펙트 클래스
class ShieldRangeEffect:
    """
    방패 범위 표시 이펙트 - world['effects_front']에서 관리
    우클릭으로 방패를 전개할 때 표시되는 범위 이펙트

    주의: 이 클래스는 x, y 속성을 가지지 않습니다.
    lobby_mode.py의 draw 루프에서 특별 처리가 필요합니다.
    """
    _range_image = None  # 클래스 변수로 이미지 공유

    def __init__(self, player, shield):
        # 이미지 최초 1회만 로드 (클래스 변수 사용)
        if ShieldRangeEffect._range_image is None:
            range_path = os.path.join('resources', 'Texture_organize', 'Weapon', 'shieldRange.png')
            try:
                ShieldRangeEffect._range_image = load_image(range_path)
            except Exception as ex:
                print(f"\033[91mFailed to load shield range image: {ex}\033[0m")
                ShieldRangeEffect._range_image = None

        self.player = player
        self.shield = shield
        self.range_scale = 4.0  # 방패 범위 이펙트 크기 조정

        # x, y 속성 제거: 카메라 적용을 위해 플레이어 참조만 유지
        # draw()에서 player의 카메라 적용된 좌표를 직접 받아서 사용

    def update(self):
        """
        매 프레임마다 호출되어 이펙트 상태 업데이트
        방패가 blocking 상태가 아니면 False를 반환하여 제거됨
        """
        # 방패의 blocking 상태가 해제되면 이펙트도 제거
        if not self.shield.blocking:
            return False
        # x, y 동기화 제거: player 참조만 유지
        return True

    def draw(self, draw_x, draw_y):
        """
        방패 범위 이펙트 그리기

        Args:
            draw_x: 카메라가 적용된 플레이어의 화면 X 좌표
            draw_y: 카메라가 적용된 플레이어의 화면 Y 좌표
        """
        if ShieldRangeEffect._range_image is None:
            return

        # 방패 범위 각도 계산 (마우스 방향 기준, -90도 오프셋 적용)
        base_offset = -math.pi / 2
        theta = self.shield.range_angle + base_offset

        # 카메라가 적용된 draw_x, draw_y를 기준으로 방패 범위 이펙트 그리기
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
        """마우스 위치를 기준으로 무기 각도 계산 (카메라 보정 적용)"""
        # 마우스 월드 좌표 계산 (카메라 오프셋 고려)
        world_mouse_x, world_mouse_y = get_mouse_world_position(self.player)

        # 플레이어(월드 좌표)에서 마우스(월드 좌표)로 향하는 벡터 계산
        dx = world_mouse_x - self.player.x
        dy = world_mouse_y - self.player.y

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

    def draw(self, draw_x, draw_y):
        """무기를 회전시켜서 그리기"""
        # draw_x, draw_y는 카메라가 적용된 화면 좌표
        # 무기 위치 계산 (카메라 적용된 플레이어 위치 기준)
        weapon_x = draw_x + self.offset_x * math.cos(self.angle)
        weapon_y = draw_y + self.offset_y + self.offset_x * math.sin(self.angle)

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
        """방패: 우클릭 유지 시 각도를 커서 방향으로 갱신 (카메라 보정 적용)"""
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

        # 마나가 10이상으로 회복 되면 쉴드 복구
        if self.player.stats.get('mana') > 10 and getattr(self.player, 'shield_broken', False):
            self.player.shield_broken = False

            # 증폭된 마나 회복 원래대로 복구
            original_mana_regen = self.player.stats.get('mana_regen')
            self.player.stats.set_base('mana_regen', original_mana_regen / 4.0)

            print(f'\033[92m[Shield] 마나 회복으로 방패가 복구되었습니다!\033[0m')


        # 방패가 깨진 상태이면 blocking 불가 및 이펙트 제거
        if getattr(self.player, 'shield_broken', False):
            # 방패 전개 강제 해제
            self.blocking = False

            # 쉴드가 깨진 상태라면 마나 회복 속도 증가
            current_mana_regen = self.player.stats.get('mana_regen')
            boosted_mana_regen = max(current_mana_regen, 2.0)
            self.player.stats.set_base('mana_regen', boosted_mana_regen)

            # 쉴드 이펙트가 존재하면 월드에서 제거
            if self.range_effect is not None:
                if hasattr(self.player, 'world') and self.player.world and 'effects_front' in self.player.world:
                    try:
                        if self.range_effect in self.player.world['effects_front']:
                            self.player.world['effects_front'].remove(self.range_effect)
                            print(f"[Shield] 방패 깨짐으로 인해 ShieldRangeEffect 제거됨")
                    except Exception as ex:
                        print(f'\033[91m[Shield] ShieldRangeEffect 제거 실패: {ex}\033[0m')
                self.range_effect = None

            # 공격 타이머 업데이트만 처리
            if self.is_attacking:
                dt = framework.get_delta_time()
                self.attack_timer += dt
                if self.attack_timer >= self.attack_duration:
                    self.is_attacking = False
                    self.attack_timer = 0.0
            return

        # 마우스 월드 좌표 계산 (카메라 오프셋 고려)
        world_mouse_x, world_mouse_y = get_mouse_world_position(self.player)

        # 플레이어(월드 좌표)에서 마우스(월드 좌표)로 향하는 벡터 계산
        dx = world_mouse_x - self.player.x
        dy = world_mouse_y - self.player.y

        # 방패 범위 각도 계산 (라디안)
        self.range_angle = math.atan2(dy, dx)

        # 이전 blocking 상태 저장
        was_blocking = self.blocking

        # 프레임별 우클릭 유지 여부를 직접 폴링하여 blocking 동기화 (이벤트 누락 대비)
        mx = ctypes.c_int(0)
        my = ctypes.c_int(0)
        state = SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))
        try:
            right_mask = 1 << (SDL_BUTTON_RIGHT - 1)
            self.blocking = bool(state & right_mask)
        except Exception:
            pass

        # blocking 상태가 변경되었을 때 이펙트 생성/제거
        # if self.blocking and not was_blocking:
        #     # blocking 시작: 이펙트 생성
        #     if hasattr(self.player, 'world') and self.player.world and 'effects_front' in self.player.world:
        #         self.range_effect = ShieldRangeEffect(self.player, self)
        #         self.player.world['effects_front'].append(self.range_effect)
        # elif not self.blocking and was_blocking:
        #     # blocking 종료: 이펙트는 자동으로 제거됨 (update에서 False 반환)
        #     self.range_effect = None

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

    def draw(self, draw_x, draw_y):
        """방패 본체 그리기 (범위 이미지는 world['effects_front']에서 관리)"""
        # 방패 본체는 회전 없이 플레이어 앞에 고정
        flip = 'h' if self.player.face_dir == -1 else ''
        # 전개 중일 때만 앞으로 이동, 아니면 기존의 작은 좌우 오프셋 유지
        if self.blocking:
            local_offset_x = self.forward_offset if self.player.face_dir == 1 else -self.forward_offset
        else:
            local_offset_x = 10 if self.player.face_dir == -1 else -10

        # 바라보는 방향에 따른 방패 로컬 오프셋 적용
        weapon_x = draw_x + local_offset_x
        weapon_y = draw_y + self.offset_y

        self.image.clip_composite_draw(
            0, 0, self.image.w, self.image.h,
            0, flip,
            weapon_x, weapon_y,
            self.image.w * self.scale_factor,
            self.image.h * self.scale_factor
        )

    def check_projectile_block(self, projectile):
        """투사체가 방패에 막혔는지 확인

        Args:
            projectile: 투사체 객체

        Returns:
            bool: 방패에 막혔으면 True, 아니면 False
        """
        # 방패를 전개하지 않았으면 막을 수 없음
        if not self.blocking:
            return False

        # print(f"[Shield] 방패 전개 중, 투사체 충돌 체크 시작")

        # 방패 중심 위치 계산
        if self.blocking:
            local_offset_x = self.forward_offset if self.player.face_dir == 1 else -self.forward_offset
        else:
            local_offset_x = 10 if self.player.face_dir == -1 else -10
        shield_x = self.player.x + local_offset_x
        shield_y = self.player.y + self.offset_y

        # 방패 크기 (이미지 크기 * scale) - 충돌 범위를 매우 넓게
        shield_width = self.image.w * self.scale_factor * 2.5  # 3배로 확대
        shield_height = self.image.h * self.scale_factor * 2.5

        # 투사체 크기
        if hasattr(projectile, 'get_collision_box'):
            proj_width, proj_height = projectile.get_collision_box()
        else:
            proj_width = 30
            proj_height = 30

        # AABB 충돌 감지
        shield_left = shield_x - shield_width / 2
        shield_right = shield_x + shield_width / 2
        shield_bottom = shield_y - shield_height / 2
        shield_top = shield_y + shield_height / 2

        proj_left = projectile.x - proj_width / 2
        proj_right = projectile.x + proj_width / 2
        proj_bottom = projectile.y - proj_height / 2
        proj_top = projectile.y + proj_height / 2

        # 충돌 검사
        if (shield_left < proj_right and shield_right > proj_left and
            shield_bottom < proj_top and shield_top > proj_bottom):

            print(f"[Shield] AABB 충돌 감지!")

            # 투사체가 플레이어 방향으로 날아오는지 확인
            # 투사체에서 플레이어로 향하는 벡터 (투사체의 이동 방향과 유사)
            proj_to_player_x = self.player.x - projectile.x
            proj_to_player_y = self.player.y - projectile.y

            # 투사체의 속도 벡터 확인 (투사체가 플레이어 쪽으로 오고 있는지)
            if hasattr(projectile, 'dx') and hasattr(projectile, 'dy'):
                # 투사체의 이동 방향과 플레이어 방향이 같은지 확인
                dot_product = projectile.dx * proj_to_player_x + projectile.dy * proj_to_player_y
                if dot_product < 0:
                    # 투사체가 플레이어에게서 멀어지고 있음 (이미 지나침)
                    print(f"[Shield] 투사체가 플레이어에게서 멀어지고 있음 - 방어 실패")
                    return False

            # 방어 이펙트 생성 (투사체 위치에 생성)
            if hasattr(self.player, 'world') and self.player.world and 'effects_front' in self.player.world:
                try:
                    from .vfx import GuardFX
                    # 투사체(공격자) 위치에 이펙트 생성
                    guard_fx = GuardFX(projectile.x, projectile.y, scale=self.scale_factor)
                    self.player.world['effects_front'].append(guard_fx)
                    print(f"[Shield] 방어 이펙트 생성 완료 at ({int(projectile.x)}, {int(projectile.y)})")
                except Exception as ex:
                    print(f"[Shield] 방어 이펙트 생성 실패: {ex}")

            # 플레이어 넉백 (부드럽게)
            knockback_strength = 100  # 픽셀 (초기 속도 기반)
            distance = math.sqrt(proj_to_player_x**2 + proj_to_player_y**2)
            if distance > 0:
                # 넉백 방향 계산 (투사체에서 멀어지는 방향)
                self.player.knockback_dx = proj_to_player_x / distance
                self.player.knockback_dy = proj_to_player_y / distance
                # 넉백 속도 및 지속시간 설정
                self.player.knockback_speed = knockback_strength
                self.player.knockback_duration = 0.2  # 0.2초 동안 넉백
                self.player.knockback_timer = 0.0  # 타이머 초기화
                print(f"[Shield] 방어 이펙트에 의한 넉백 발생: 방향=({self.player.knockback_dx:.2f}, {self.player.knockback_dy:.2f}), 속도={knockback_strength}")

            # 막히면 투사체 데미지의 30%만큼의 수치를 마나로 소비 (투사체 막기 비용)
            if hasattr(projectile, 'damage'):
                mana_cost = projectile.damage * 0.15
                shield_broken = False
                if hasattr(self.player, 'stats'):
                    current_mana = self.player.stats.get('mana')
                    new_mana = max(0, current_mana - mana_cost)
                    self.player.stats.set_base('mana', new_mana)

                    print(f"[Shield] 투사체 방어 마나 소비: {mana_cost:.1f} (현재 마나: {new_mana:.1f}/{self.player.stats.get('max_mana'):.1f})")

                    # 마나가 0 이하면 방패가 깨짐
                    if new_mana <= 0:
                        # 방패 사용 불가 상태로 전환
                        self.player.shield_broken = True

                        # 방패 깨짐 이펙트 생성 (플레이어 위치에 생성)
                        if hasattr(self.player, 'world') and self.player.world and 'effects_front' in self.player.world:
                            try:
                                from .vfx import ShieldCrashEffect
                                crash_fx = ShieldCrashEffect(self.player.x, self.player.y, scale=1.0)
                                self.player.world['effects_front'].append(crash_fx)
                                print(f"[Shield] 방패 깨짐 이펙트 생성 at ({int(self.player.x)}, {int(self.player.y)})")
                            except Exception as ex:
                                print(f'\033[91m[Shield] 방패 깨짐 이펙트 생성 실패: {ex}\033[0m')

                        # 방패 깨짐 상태에서는 방어 실패 (데미지를 받음)
                        print(f"[Shield] 마나 부족으로 방패가 깨짐! 방어 실패")
                        return False

            return True

        # print(f"[Shield] 충돌 감지 안됨")
        return False

    def check_effect_block(self, effect):
        """몬스터 공격 이펙트가 방패에 막혔는지 확인

        Args:
            effect: 몬스터 공격 이펙트 객체 (CatThiefSwingEffect 등)

        Returns:
            bool: 방패에 막혔으면 True, 아니면 False
        """
        # 방패를 전개하지 않았으면 막을 수 없음
        if not self.blocking:
            return False

        # 방패 중심 위치 계산
        if self.blocking:
            local_offset_x = self.forward_offset if self.player.face_dir == 1 else -self.forward_offset
        else:
            local_offset_x = 10 if self.player.face_dir == -1 else -10
        shield_x = self.player.x + local_offset_x
        shield_y = self.player.y + self.offset_y

        # 방패 크기 (이미지 크기 * scale) - 충돌 범위를 매우 넓게
        shield_width = self.image.w * self.scale_factor * 2.5  # 2.5배로 확대
        shield_height = self.image.h * self.scale_factor * 2.5

        # 이펙트 크기
        if hasattr(effect, 'get_collision_box'):
            effect_width, effect_height = effect.get_collision_box()
        else:
            effect_width = 100
            effect_height = 100

        # AABB 충돌 감지
        shield_left = shield_x - shield_width / 2
        shield_right = shield_x + shield_width / 2
        shield_bottom = shield_y - shield_height / 2
        shield_top = shield_y + shield_height / 2

        effect_left = effect.x - effect_width / 2
        effect_right = effect.x + effect_width / 2
        effect_bottom = effect.y - effect_height / 2
        effect_top = effect.y + effect_height / 2

        # 충돌 검사
        if (shield_left < effect_right and shield_right > effect_left and
            shield_bottom < effect_top and shield_top > effect_bottom):

            print(f"[Shield] 이펙트 AABB 충돌 감지! ({effect.__class__.__name__})")

            # 이펙트가 플레이어 방향으로 날아오는지 확인 (선택적)
            effect_to_player_x = self.player.x - effect.x
            effect_to_player_y = self.player.y - effect.y

            # 방어 이펙트 생성 (이펙트 위치에 생성)
            if hasattr(self.player, 'world') and self.player.world and 'effects_front' in self.player.world:
                try:
                    from .vfx import GuardFX
                    # 이펙트 위치에 방어 이펙트 생성
                    guard_fx = GuardFX(effect.x, effect.y, scale=self.scale_factor)
                    self.player.world['effects_front'].append(guard_fx)
                    print(f"[Shield] 방어 이펙트 생성 완료 at ({int(effect.x)}, {int(effect.y)})")
                except Exception as ex:
                    print(f'\033[91m[Shield] 방어 이펙트 생성 실패: {ex}\033[0m')

            # 플레이어 넉백 (부드럽게)
            knockback_strength = 100  # 픽셀 (초기 속도 기반)
            distance = math.sqrt(effect_to_player_x**2 + effect_to_player_y**2)
            if distance > 0:
                # 넉백 방향 계산 (이펙트에서 멀어지는 방향)
                self.player.knockback_dx = effect_to_player_x / distance
                self.player.knockback_dy = effect_to_player_y / distance
                # 넉백 속도 및 지속시간 설정
                self.player.knockback_speed = knockback_strength
                self.player.knockback_duration = 0.2  # 0.2초 동안 넉백
                self.player.knockback_timer = 0.0  # 타이머 초기화
                print(f"[Shield] 방어 이펙트에 의한 넉백 발생: 방향=({self.player.knockback_dx:.2f}, {self.player.knockback_dy:.2f}), 속도={knockback_strength}")

            # 막히면 데미지의 30%만큼의 수치를 마나 소비 (예: 몬스터 공격 이펙트 막기)
            if hasattr(effect, 'damage'):
                mana_cost = effect.damage * 0.3
                shield_broken = False
                if hasattr(self.player, 'stats'):
                    current_mana = self.player.stats.get('mana')
                    new_mana = max(0, current_mana - mana_cost)
                    self.player.stats.set_base('mana', new_mana)

                    print(f"[Shield] 방어 마나 소비: {mana_cost:.1f} (현재 마나: {new_mana:.1f}/{self.player.stats.get('max_mana'):.1f})")

                    # 마나가 0 이하면 방패가 깨짐
                    if new_mana <= 0:
                        shield_broken = True
                        # 방패 사용 불가 상태로 전환
                        self.player.shield_broken = True

                        # 방패 깨짐 이펙트 생성 (플레이어 위치에 생성)
                        if hasattr(self.player, 'world') and self.player.world and 'effects_front' in self.player.world:
                            try:
                                from .vfx import ShieldCrashEffect
                                crash_fx = ShieldCrashEffect(self.player.x, self.player.y, scale=1.0)
                                self.player.world['effects_front'].append(crash_fx)
                                print(f"[Shield] 방패 깨짐 이펙트 생성 at ({int(self.player.x)}, {int(self.player.y)})")
                            except Exception as ex:
                                print(f'\033[91m[Shield] 방패 깨짐 이펙트 생성 실패: {ex}\033[0m')

                        # 강제로 방패 전개 해제
                        self.blocking = False
                        if self.range_effect:
                            self.range_effect = None

                if shield_broken:
                    print(f"\033[93m[Shield] 마나 부족으로 방패가 깨졌습니다! 마나 회복 후 다시 사용 가능합니다.\033[0m")

            return True

        return False


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
        """마우스 위치를 기준으로 무기 각도 계산 (카메라 보정 적용)"""
        # 마우스 월드 좌표 계산 (카메라 오프셋 고려)
        world_mouse_x, world_mouse_y = get_mouse_world_position(self.player)

        # 플레이어(월드 좌표)에서 마우스(월드 좌표)로 향하는 벡터 계산
        dx = world_mouse_x - self.player.x
        dy = world_mouse_y - self.player.y

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
        - 공격 중(후딜레이 영역)에 클릭하면 즉시 2스테이지(콤보) 공격으로 전환
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

    def draw(self, draw_x, draw_y):
        """
        검을 회전시켜서 그리기 - 검 자체를 중심으로 회전 + 캐릭터 중심으로 공전

        Args:
            draw_x: 카메라가 적용된 플레이어의 화면 X 좌표
            draw_y: 카메라가 적용된 플레이어의 화면 Y 좌표
        """
        # ========== 공격 모션에 따른 각도 및 오프셋 계산 ==========
        sword_rotation = 0.0          # 검 자체의 회전 각도 (자전)
        orbit_angle_offset = 0.0      # 캐릭터 중심 기준 공전 각도 오프셋
        y_offset_modifier = 0.0       # Y축 위치 오프셋 (공격 시 아래로 내려감)

        if self.is_attacking:
            if self.attack_timer < self.attack_duration:
                # 공격 모션 중 (0 ~ attack_duration)
                sword_rotation = self.rotation_angle_range * self.attack_progress  # 자전 각도
                orbit_angle_offset = self.orbit_angle_range * self.attack_progress  # 공전 각도
                # Y축 오프셋: 공격 시 검을 아래로 내림
                y_offset_modifier = -3 * self.offset_y * self.attack_progress
            else:
                # 후딜레이 중 (attack_duration ~ total_attack_time)
                sword_rotation = self.rotation_angle_range      # 자전 최대 각도 유지
                orbit_angle_offset = self.orbit_angle_range    # 공전 최대 각도 유지
                # Y축 오프셋: 후딜레이 동안 최대 아래 위치 유지
                y_offset_modifier = -3 * self.offset_y

        # ========== 2스테이지(콤보) 시 자전 방향 반전 ==========
        # 콤보 공격 시 검이 반대 방향으로 회전하여 자연스러운 연계 공격 연출
        invert_rotation = (getattr(self, 'stage', 1) == 2 and self.attack_timer < self.attack_duration)
        if invert_rotation:
            sword_rotation = -sword_rotation

        # ========== 검의 기본 각도 오프셋 ==========
        base_offset = self.base_angle_offset

        # ========== 마우스 위치에 따른 검의 방향 결정 ==========
        angle_deg = math.degrees(self.angle) % 360

        # 마우스가 왼쪽/오른쪽에 있는지에 따라 검의 위치와 반전 방향 결정
        if 90 < angle_deg < 270:  # 왼쪽 영역
            flip = 'v'  # 수직 반전
            # 왼쪽: 공전 각도를 빼서 위치 계산
            position_angle = self.angle - orbit_angle_offset
            # 왼쪽: 자전 각도를 빼서 최종 각도 계산
            final_angle = position_angle - sword_rotation
        else:  # 오른쪽 영역
            flip = ''
            # 오른쪽: 공전 각도를 더해서 위치 계산
            position_angle = self.angle + orbit_angle_offset
            # 오른쪽: 자전 각도를 더해서 최종 각도 계산
            final_angle = position_angle + sword_rotation

        # ========== 검의 실제 화면 위치 계산 (카메라 적용 좌표 기준) ==========
        # draw_x, draw_y는 이미 카메라가 적용된 화면 좌표이므로, 이를 기준으로 offset 적용
        weapon_x = draw_x + self.offset_x * math.cos(position_angle)
        weapon_y = draw_y + self.offset_y + self.offset_x * math.sin(position_angle) + y_offset_modifier

        # ========== 검 이미지 그리기 ==========
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
        """장비 이벤트 처리 (좌클릭: 공격, 우클릭: 방패 전개 표시)

        방어와 공격은 상호 배타적으로 작동:
        - 방어 중일 때는 공격 불가
        - 공격 중일 때는 방어 불가
        """
        # 인벤토리가 열려있으면 장비 클릭 이벤트 무시
        if getattr(self.player, 'inventory_open', False):
            return

        # 현재 방어 중인지 확인
        is_blocking = False
        for equipment in self.front_equipment:
            if isinstance(equipment, Shield) and equipment.blocking:
                is_blocking = True
                break

        # 현재 공격 중인지 확인
        is_attacking = False
        for equipment in self.back_equipment:
            if isinstance(equipment, Sword) and equipment.is_attacking:
                is_attacking = True
                break

        # 마우스 좌클릭 시 공격(검) - 방어 중이 아닐 때만 가능
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            if is_blocking:
                # 방어 중일 때는 공격 불가
                print('[Equipment] 방어 중에는 공격할 수 없습니다!')
            else:
                # 방어 중이 아니면 공격 실행
                for equipment in self.back_equipment:
                    equipment.attack()

        # 마우스 우클릭: 방패 범위 표시 시작 - 공격 중이 아닐 때만 가능
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_RIGHT:
            if is_attacking:
                # 공격 중일 때는 방어 불가
                print('[Equipment] 공격 중에는 방어할 수 없습니다!')
            else:
                # 공격 중이 아니면 방어 시작
                try:
                    print('[Shield] RIGHT DOWN')
                except Exception:
                    pass
                for equipment in self.front_equipment:
                    if isinstance(equipment, Shield):
                        equipment.start_block()
        elif event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_RIGHT:
            # 우클릭 해제는 항상 처리 (방어 종료)
            try:
                print('[Shield] RIGHT UP')
            except Exception:
                pass
            for equipment in self.front_equipment:
                if isinstance(equipment, Shield):
                    equipment.end_block()

    def draw_back(self, draw_x, draw_y):
        """캐릭터 뒤에 그려질 장비들"""
        for equipment in self.back_equipment:
            equipment.draw(draw_x, draw_y)

    def draw_front(self, draw_x, draw_y):
        """캐릭터 앞에 그려질 장비들"""
        for equipment in self.front_equipment:
            equipment.draw(draw_x, draw_y)
