import pico2d as p2
from ...behavior_tree import BehaviorTree
import game_framework as framework
import random
import math

class AttackPattern2Action:
    """
    패턴2 - 은신 후 다른 곳에서 나타나 플레이어를 향해 강한 돌진 공격 2회
    자세한 설명:
    공격 준비시 멈춘 후.
    1단계: 은신 후 플레이어 주변에서 랜덤한 위치에 나타나 플레이어를 향해 강한 돌진 공격
    2단계: 1단계 이후 다시 은신 후 다른 랜덤 위치에 나타나 플레이어를 향해 강한 돌진 공격

    모션 이미지 경로: resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character

    은신 모션
    PantherAssassin_Die{i:02d}.png 0 ~ 10: 은신 모션 (10프레임 재생 후 마지막 프레임 유지)
    # Die 모션을 은신 모션으로 재활용

    은신 풀린 곳에서 플레이어까지의 1.5배 거리를 0.5초 만에 돌진한다.
    PantherAssassin_BladeAttack{i:02d}.png 0 ~ 7: 돌진 공격 모션
    + 돌진시 0.1초마다 검정색으로 편향된 이미지를 남기며, 0.3초 만에 alpha값이 1에서 0으로 감소한다.
    alpha값이 0이 되면 사라진다.

    돌진 이후 휘두르기 모션
    PantherAssassin_BladeAttack{i:02d}.png 8 ~ 17: 돌진 공격 휘두르기 모션

    이펙트 이비지 경로: resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/FX
    휘두르기 이펙트
    이펙트 이미지: PantherAssassin_BladeAttack_SwingFX{i:02d}.png 0 ~ 7

    주의: 검격 이펙트는 PantherBladeSwingEffect 클래스가 독립적으로 관리하므로
          이 클래스 내부에서는 이펙트 리스트를 관리하지 않습니다.
    """

    # 클래스 레벨 이미지 시퀀스
    stealth_img_seq = []  # Die 모션 (은신용)
    dash_img_seq = []     # BladeAttack 0~7 (돌진)
    swing_img_seq = []    # BladeAttack 8~17 (휘두르기)

    def __init__(self, panther):
        """
        Args:
            panther: PantherAssassin 인스턴스 참조
        """
        self.panther = panther
        self.phase = 0
        self.timer = 0.0

        # 공격 횟수 관련 변수
        self.attack_count = 0  # 현재 돌진 공격 횟수
        self.max_attacks = 2   # 최대 돌진 공격 횟수

        # 은신 관련 변수
        self.stealth_frame = 0
        self.stealth_frame_timer = 0.0
        self.stealth_frame_speed = 15.0  # 초당 프레임 수
        self.stealth_total_frames = 11   # 0~10

        # 텔레포트 관련 변수
        self.teleport_x = 0.0
        self.teleport_y = 0.0
        self.teleport_distance = 300  # 플레이어로부터의 텔레포트 거리

        # 돌진 관련 변수
        self.dash_start_x = 0.0
        self.dash_start_y = 0.0
        self.dash_target_x = 0.0
        self.dash_target_y = 0.0
        self.dash_duration = 0.5  # 돌진 시간 (0.5초)
        self.dash_progress = 0.0  # 돌진 진행도 (0.0 ~ 1.0)
        self.dash_frame = 0
        self.dash_frame_timer = 0.0
        self.dash_frame_speed = 16.0  # 초당 프레임 수 (8프레임을 0.5초에)
        self.dash_total_frames = 8    # 0~7

        # 잔상 관련 변수
        self.afterimages = []  # [(x, y, alpha, timer), ...]
        self.afterimage_spawn_interval = 0.1  # 0.1초마다 생성
        self.afterimage_spawn_timer = 0.0
        self.afterimage_fade_duration = 0.3  # 0.3초에 걸쳐 페이드아웃

        # 휘두르기 관련 변수
        self.swing_frame = 0
        self.swing_frame_timer = 0.0
        self.swing_frame_speed = 20.0  # 초당 프레임 수
        self.swing_total_frames = 10   # 8~17 (총 10프레임)

        # 휘두르기 이펙트 관련 변수 (독립적으로 관리됨)
        self.swing_fx_frame = 0
        self.swing_fx_frame_timer = 0.0
        self.swing_fx_frame_speed = 20.0  # 초당 프레임 수
        self.swing_fx_total_frames = 8    # 0~7 (총 8프레임)

        # 이미지 로드 (클래스 레벨에서 한 번만)
        if not AttackPattern2Action.stealth_img_seq:
            try:
                # 은신 모션 이미지 로드 (Die 0~10)
                for i in range(11):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Die{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern2Action.stealth_img_seq.append(img)
                print(f'[Pattern2] 은신 모션 이미지 로드 완료: {len(AttackPattern2Action.stealth_img_seq)}개')

                # 돌진 모션 이미지 로드 (BladeAttack 0~7)
                for i in range(8):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_BladeAttack{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern2Action.dash_img_seq.append(img)
                print(f'[Pattern2] 돌진 모션 이미지 로드 완료: {len(AttackPattern2Action.dash_img_seq)}개')

                # 휘두르기 모션 이미지 로드 (BladeAttack 8~17)
                for i in range(8, 18):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_BladeAttack{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern2Action.swing_img_seq.append(img)
                print(f'[Pattern2] 휘두르기 모션 이미지 로드 완료: {len(AttackPattern2Action.swing_img_seq)}개')

            except FileNotFoundError as e:
                print(f'\033[91m[Pattern2] 이미지 로드 실패: {e}\033[0m')

    def update(self):
        """패턴 2 로직 실행"""
        dt = framework.get_delta_time()

        if self.phase == 0:
            # 초기화: 1회차 은신 시작
            self.attack_count = 0
            self.stealth_frame = 0
            self.stealth_frame_timer = 0.0
            self.afterimages = []
            self.phase = 1
            print("[Pattern2] 패턴 시작 - 1회차 은신 시작!")

        elif self.phase == 1:
            # 은신 모션 재생
            self.stealth_frame_timer += dt

            if self.stealth_frame_timer >= 1.0 / self.stealth_frame_speed:
                self.stealth_frame += 1
                self.stealth_frame_timer = 0.0

                # 은신 애니메이션 종료 (10번 프레임까지)
                if self.stealth_frame >= self.stealth_total_frames:
                    # 텔레포트 위치 계산
                    self._calculate_teleport_position()
                    self.phase = 2
                    print(f"[Pattern2] 은신 완료 - 텔레포트: ({int(self.teleport_x)}, {int(self.teleport_y)})")

        elif self.phase == 2:
            # 텔레포트 실행 (순간 이동)
            self.panther.x = self.teleport_x
            self.panther.y = self.teleport_y

            # 돌진 준비
            self._prepare_dash()
            self.phase = 3
            print(f"[Pattern2] 돌진 시작: ({int(self.dash_start_x)}, {int(self.dash_start_y)}) -> ({int(self.dash_target_x)}, {int(self.dash_target_y)})")

        elif self.phase == 3:
            # 돌진 공격 실행
            self.timer += dt
            self.dash_progress = min(1.0, self.timer / self.dash_duration)

            # 돌진 애니메이션 프레임 업데이트
            self.dash_frame_timer += dt
            if self.dash_frame_timer >= 1.0 / self.dash_frame_speed:
                self.dash_frame = min(self.dash_frame + 1, self.dash_total_frames - 1)
                self.dash_frame_timer = 0.0

            # 선형 보간으로 위치 업데이트
            self.panther.x = self.dash_start_x + (self.dash_target_x - self.dash_start_x) * self.dash_progress
            self.panther.y = self.dash_start_y + (self.dash_target_y - self.dash_start_y) * self.dash_progress

            # 잔상 생성
            self.afterimage_spawn_timer += dt
            if self.afterimage_spawn_timer >= self.afterimage_spawn_interval:
                self._spawn_afterimage()
                self.afterimage_spawn_timer = 0.0

            # 잔상 업데이트 (페이드아웃)
            self._update_afterimages(dt)

            # 돌진 종료
            if self.dash_progress >= 1.0:
                self.swing_frame = 0
                self.swing_frame_timer = 0.0
                self.timer = 0.0
                self.phase = 4
                print("[Pattern2] 돌진 완료 - 휘두르기 시작!")

        elif self.phase == 4:
            # 휘두르기 모션 재생
            self.swing_frame_timer += dt
            self.swing_fx_frame_timer += dt

            # 휘두르기 캐릭터 모션 프레임 업데이트
            if self.swing_frame_timer >= 1.0 / self.swing_frame_speed:
                self.swing_frame += 1
                self.swing_frame_timer = 0.0

                # 휘두르기 시작 프레임(2번)에서 검격 이펙트 생성
                if self.swing_frame == 2 and not hasattr(self, 'blade_effect_spawned'):
                    self._spawn_blade_swing_effect()
                    self.blade_effect_spawned = True
                    print("[Pattern2] 검격 이펙트 생성 시도!")

            # 잔상 업데이트 (돌진 중 생성된 잔상이 계속 페이드아웃)
            self._update_afterimages(dt)

            # 휘두르기 애니메이션 종료 체크
            if self.swing_frame >= self.swing_total_frames:
                # 공격 횟수 증가
                self.attack_count += 1
                print(f"[Pattern2] {self.attack_count}회 공격 완료!")

                # blade_effect_spawned 플래그 초기화
                if hasattr(self, 'blade_effect_spawned'):
                    delattr(self, 'blade_effect_spawned')

                # 2회 공격 완료 확인
                if self.attack_count >= self.max_attacks:
                    # 패턴 종료
                    self.phase = 0
                    self.panther.attack_timer = self.panther.attack_cooldown
                    print("[Pattern2] 패턴 완료 - 2회 공격 종료!")
                    return BehaviorTree.SUCCESS
                else:
                    # 다음 공격을 위해 은신 단계로 돌아감
                    self.stealth_frame = 0
                    self.stealth_frame_timer = 0.0
                    self.afterimages = []  # 잔상 초기화
                    self.phase = 1
                    print(f"[Pattern2] 2회차 은신 시작!")

        return BehaviorTree.RUNNING

    def _calculate_teleport_position(self):
        """플레이어 주변 랜덤 위치 계산"""
        if not self.panther.target:
            # 타겟이 없으면 현재 위치 유지
            self.teleport_x = self.panther.x
            self.teleport_y = self.panther.y
            return

        # 플레이어 주변 랜덤 각도
        angle = random.uniform(0, 360)
        rad = math.radians(angle)

        # 플레이어로부터 일정 거리 떨어진 위치
        self.teleport_x = self.panther.target.x + math.cos(rad) * self.teleport_distance
        self.teleport_y = self.panther.target.y + math.sin(rad) * self.teleport_distance

    def _prepare_dash(self):
        """돌진 준비: 시작 위치와 목표 위치 계산"""
        self.dash_start_x = self.panther.x
        self.dash_start_y = self.panther.y

        if not self.panther.target:
            # 타겟이 없으면 현재 위치에서 랜덤 방향으로 돌진
            angle = random.uniform(0, 360)
            rad = math.radians(angle)
            distance = 300
            self.dash_target_x = self.panther.x + math.cos(rad) * distance
            self.dash_target_y = self.panther.y + math.sin(rad) * distance
        else:
            # 플레이어까지의 거리의 1.5배 지점으로 돌진
            dx = self.panther.target.x - self.panther.x
            dy = self.panther.target.y - self.panther.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                # 정규화된 방향 벡터
                dir_x = dx / distance
                dir_y = dy / distance

                # 1.5배 거리
                dash_distance = distance * 1.5
                self.dash_target_x = self.panther.x + dir_x * dash_distance
                self.dash_target_y = self.panther.y + dir_y * dash_distance
            else:
                # 플레이어와 같은 위치면 랜덤 방향으로
                angle = random.uniform(0, 360)
                rad = math.radians(angle)
                self.dash_target_x = self.panther.x + math.cos(rad) * 300
                self.dash_target_y = self.panther.y + math.sin(rad) * 300

        # 돌진 변수 초기화
        self.dash_progress = 0.0
        self.dash_frame = 0
        self.dash_frame_timer = 0.0
        self.timer = 0.0
        self.afterimage_spawn_timer = 0.0

    def _spawn_afterimage(self):
        """잔상 생성"""
        # 현재 위치와 프레임으로 잔상 추가
        afterimage = {
            'x': self.panther.x,
            'y': self.panther.y,
            'frame': self.dash_frame,
            'alpha': 1.0,
            'timer': 0.0
        }
        self.afterimages.append(afterimage)

    def _update_afterimages(self, dt):
        """잔상 업데이트 (페이드아웃)"""
        for afterimage in self.afterimages[:]:
            afterimage['timer'] += dt
            # 0.3초에 걸쳐 alpha 1.0 -> 0.0
            afterimage['alpha'] = max(0.0, 1.0 - (afterimage['timer'] / self.afterimage_fade_duration))

            # alpha가 0이 되면 제거
            if afterimage['alpha'] <= 0.0:
                self.afterimages.remove(afterimage)

    def _spawn_blade_swing_effect(self):
        """검격 이펙트 생성 - 휘두르기 공격 시 플레이어에게 피해를 주는 이펙트"""
        if not self.panther.world or 'effects_front' not in self.panther.world:
            print("[Pattern2] world 또는 effects_front가 없어서 검격 이펙트 생성 실패")
            return

        try:
            # 검격 이펙트 위치 계산 (보스 앞쪽)
            # 돌진 방향을 기준으로 검격 생성
            dash_dx = self.dash_target_x - self.dash_start_x
            dash_dy = self.dash_target_y - self.dash_start_y
            dash_distance = math.sqrt(dash_dx**2 + dash_dy**2)

            if dash_distance > 0:
                direction_x = dash_dx / dash_distance
                direction_y = dash_dy / dash_distance
            else:
                # 기본 방향 (오른쪽)
                direction_x = 1.0
                direction_y = 0.0

            # 검격 이펙트 위치 (보스 앞쪽 60픽셀)
            offset_distance = 60
            effect_x = self.panther.x + direction_x * offset_distance
            effect_y = self.panther.y + direction_y * offset_distance

            # 검격 방향 각도 계산 (라디안)
            effect_angle = math.atan2(direction_y, direction_x)

            # PantherBladeSwingEffect 생성
            # from ..panther_assassin import PantherBladeSwingEffect
            blade_effect = PantherBladeSwingEffect(
                effect_x,
                effect_y,
                effect_angle,
                owner=self.panther,
                scale=4.0,
                damage=30.0  # 패턴2 검격 데미지
            )

            self.panther.world['effects_front'].append(blade_effect)
            print(f"[Pattern2] 검격 이펙트 생성 완료: ({int(effect_x)}, {int(effect_y)}), 각도: {math.degrees(effect_angle):.1f}도")

        except Exception as e:
            print(f'\033[91m[Pattern2] 검격 이펙트 생성 실패: {e}\033[0m')

    def draw(self, draw_x, draw_y):
        """
        패턴 2 시각 효과 드로잉

        Args:
            draw_x, draw_y: 보스의 현재 위치 (카메라 좌표계)
        """
        # Phase 1: 은신 모션 재생
        if self.phase == 1:
            if AttackPattern2Action.stealth_img_seq and self.stealth_frame < len(AttackPattern2Action.stealth_img_seq):
                img = AttackPattern2Action.stealth_img_seq[self.stealth_frame]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

        # Phase 2: 텔레포트 직후 (마지막 은신 프레임 유지)
        elif self.phase == 2:
            if AttackPattern2Action.stealth_img_seq and len(AttackPattern2Action.stealth_img_seq) > 0:
                last_frame_idx = min(self.stealth_total_frames - 1, len(AttackPattern2Action.stealth_img_seq) - 1)
                img = AttackPattern2Action.stealth_img_seq[last_frame_idx]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

        # Phase 3: 돌진 공격 모션 + 잔상
        elif self.phase == 3:
            # 잔상 먼저 그리기 (뒤에서부터 앞으로)
            if AttackPattern2Action.dash_img_seq:
                for afterimage in self.afterimages:
                    frame_idx = min(afterimage['frame'], len(AttackPattern2Action.dash_img_seq) - 1)
                    img = AttackPattern2Action.dash_img_seq[frame_idx]
                    if img:
                        # 검정색으로 편향된 이미지 (어두운 색상)
                        # alpha 값을 255 기준으로 변환 (0.0~1.0 -> 0~255)
                        alpha = int(afterimage['alpha'] * 255)

                        # 잔상의 월드 좌표를 화면 좌표로 변환
                        afterimage_draw_x = afterimage['x'] - self.panther.x + draw_x
                        afterimage_draw_y = afterimage['y'] - self.panther.y + draw_y

                        # opacify를 사용하여 alpha 적용 (0.0~1.0 범위)
                        img.opacify(afterimage['alpha'])
                        img.draw(afterimage_draw_x, afterimage_draw_y,
                                img.w * self.panther.scale_factor,
                                img.h * self.panther.scale_factor)
                        img.opacify(1.0)  # 원래대로 복원

            # 현재 돌진 모션 프레임 그리기
            if AttackPattern2Action.dash_img_seq and self.dash_frame < len(AttackPattern2Action.dash_img_seq):
                img = AttackPattern2Action.dash_img_seq[self.dash_frame]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

        # Phase 4: 휘두르기 모션
        elif self.phase == 4:
            # 남은 잔상들 페이드아웃 효과 (돌진 중 생성된 잔상)
            if AttackPattern2Action.dash_img_seq and len(self.afterimages) > 0:
                for afterimage in self.afterimages:
                    frame_idx = min(afterimage['frame'], len(AttackPattern2Action.dash_img_seq) - 1)
                    img = AttackPattern2Action.dash_img_seq[frame_idx]
                    if img:
                        alpha = int(afterimage['alpha'] * 255)

                        afterimage_draw_x = afterimage['x'] - self.panther.x + draw_x
                        afterimage_draw_y = afterimage['y'] - self.panther.y + draw_y

                        img.opacify(afterimage['alpha'])
                        img.draw(afterimage_draw_x, afterimage_draw_y,
                                img.w * self.panther.scale_factor,
                                img.h * self.panther.scale_factor)
                        img.opacify(1.0)

            # 휘두르기 캐릭터 모션 그리기
            if AttackPattern2Action.swing_img_seq and self.swing_frame < len(AttackPattern2Action.swing_img_seq):
                img = AttackPattern2Action.swing_img_seq[self.swing_frame]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

# ==================== PantherBladeSwingEffect 검격 이펙트 클래스 ====================

class PantherBladeSwingEffect:
    """
    Panther Assassin의 검격 이펙트 (PantherAssassin_BladeAttack_SwingFX 0~7)
    패턴2의 휘두르기 공격 시 플레이어에게 피해를 주는 이펙트
    """
    images = None

    def __init__(self, x, y, angle, owner=None, scale=4.0, damage=30.0):
        """
        Args:
            x, y: 이펙트 생성 위치 (월드 좌표)
            angle: 검격 방향 (라디안)
            owner: 공격 주체 (PantherAssassin 객체)
            scale: 이펙트 크기 배율
            damage: 이펙트 데미지
        """
        self.x = x
        self.y = y
        self.angle = angle
        self.owner = owner
        self.scale = scale
        self.damage = damage
        self.from_player = False  # 보스 공격이므로 False

        # 이미지 로드 (클래스 변수로 한 번만 로드)
        if PantherBladeSwingEffect.images is None:
            PantherBladeSwingEffect.images = []
            try:
                for i in range(8):  # PantherAssassin_BladeAttack_SwingFX0 ~ SwingFX7
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/FX/PantherAssassin_BladeAttack_SwingFX{i:02d}.png')
                    PantherBladeSwingEffect.images.append(img)
                print(f"[PantherBladeSwingEffect] 이미지 로드 완료: {len(PantherBladeSwingEffect.images)}개")
            except Exception as e:
                print(f"\033[91m[PantherBladeSwingEffect] 이미지 로드 실패: {e}\033[0m")
                PantherBladeSwingEffect.images = []

        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 20  # 빠른 애니메이션 (20 FPS)
        self.finished = False

        # 충돌 체크용 변수
        self.has_hit_player = False  # 플레이어를 이미 맞췄는지 여부

        print(f"[PantherBladeSwingEffect] 생성됨 at ({int(x)}, {int(y)}), 각도: {math.degrees(angle):.1f}도, 크기: {scale}, 데미지: {damage}")

    def update(self):
        """이펙트 애니메이션 업데이트 (충돌 체크는 play_mode에서 처리)"""
        if self.finished:
            return False

        dt = framework.get_delta_time()
        self.animation_time += dt

        # 애니메이션 업데이트
        if self.animation_time >= 1.0 / self.animation_speed:
            self.frame += 1
            self.animation_time = 0
            print(f"[PantherBladeSwingEffect] 프레임 업데이트: {self.frame}/{len(PantherBladeSwingEffect.images) if PantherBladeSwingEffect.images else 0}")

            # 애니메이션이 끝나면 제거
            if PantherBladeSwingEffect.images and self.frame >= len(PantherBladeSwingEffect.images):
                self.finished = True
                print(f"[PantherBladeSwingEffect] 애니메이션 완료 - 제거")
                return False

        return True

    def get_collision_box(self):
        """충돌 박스 크기 반환 (play_mode에서 충돌 검사에 사용)

        Returns:
            tuple: (width, height) - 이펙트의 충돌 박스 크기
        """
        if PantherBladeSwingEffect.images and len(PantherBladeSwingEffect.images) > 0:
            effect_img = PantherBladeSwingEffect.images[min(self.frame, len(PantherBladeSwingEffect.images) - 1)]
            effect_width = effect_img.w * self.scale * 0.6  # 충돌 범위를 60%로 조정
            effect_height = effect_img.h * self.scale * 0.6
        else:
            # 기본값
            effect_width = 150
            effect_height = 150

        return (effect_width, effect_height)

    def draw(self, draw_x, draw_y):
        """
        이펙트 그리기

        Args:
            draw_x: 카메라가 적용된 화면 X 좌표
            draw_y: 카메라가 적용된 화면 Y 좌표
        """
        if not PantherBladeSwingEffect.images or len(PantherBladeSwingEffect.images) == 0:
            print(f"[PantherBladeSwingEffect] 이미지 없음 - 그리기 실패")
            return

        if self.finished:
            return

        frame_idx = min(self.frame, len(PantherBladeSwingEffect.images) - 1)
        try:
            # 회전 각도를 degree로 변환 (pico2d는 degree 사용)
            # 기본 이미지가 오른쪽 방향이므로 각도 보정
            angle_deg = math.degrees(self.angle)

            # 이미지 그리기 (회전 적용)
            PantherBladeSwingEffect.images[frame_idx].composite_draw(
                angle_deg, '',  # 각도, 플립 없음
                draw_x, draw_y,
                PantherBladeSwingEffect.images[frame_idx].w * self.scale,
                PantherBladeSwingEffect.images[frame_idx].h * self.scale
            )

            # DEBUG: 검격 이펙트 그리기 확인 (첫 프레임만)
            if self.frame == 0:
                print(f"[PantherBladeSwingEffect] 첫 프레임 그리기: 화면좌표({int(draw_x)}, {int(draw_y)}), 월드좌표({int(self.x)}, {int(self.y)}), 각도: {angle_deg:.1f}도")

            # DEBUG: 충돌 박스 그리기 (활성화)
            effect_width, effect_height = self.get_collision_box()
            p2.draw_rectangle(
                draw_x - effect_width / 2,
                draw_y - effect_height / 2,
                draw_x + effect_width / 2,
                draw_y + effect_height / 2,
                r=255, g=0, b=0
            )

        except Exception as e:
            print(f"\033[91m[PantherBladeSwingEffect] draw 에러: {e}\033[0m")

