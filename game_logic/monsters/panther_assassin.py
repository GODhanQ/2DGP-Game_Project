import pico2d as p2
import math
import random
import game_framework as framework
from ..behavior_tree import BehaviorTree, Selector, Sequence, Action, Condition, RandomSelector
from ..projectile import Projectile
from .. import image_asset_manager as iam
from ..damage_indicator import DamageIndicator
from ..ui_overlay import MonsterHealthBar


# ==================== BT Action Wrapper 클래스 ====================

class BTActionWrapper(Action):
    """
    BT Action Wrapper 클래스

    행동 트리의 Action 노드가 패턴 클래스의 update() 메서드를 호출할 수 있도록
    래핑하는 헬퍼 클래스입니다.

    사용 목적:
    - BT 프레임워크는 Action 노드를 인자 없이 호출하는 구조
    - 패턴 클래스는 인스턴스 메서드로 상태를 관리
    - 이 래퍼가 둘 사이의 다리 역할을 수행
    """

    def __init__(self, name, action_instance):
        """
        BTActionWrapper 초기화

        Args:
            name: 노드 이름 (디버깅용)
            action_instance: 실제 패턴 Action 클래스의 인스턴스
                            (예: AttackPattern1Action의 인스턴스)
        """
        self.name = name
        self.action_instance = action_instance
        self.value = BehaviorTree.UNDEF
        self.has_condition = False

    def tag_condition(self):
        """Action 노드는 조건 노드가 아님"""
        self.has_condition = False

    def reset(self):
        """노드 상태 초기화"""
        self.value = BehaviorTree.UNDEF

    def add_child(self, child, probability=1.0):
        """Leaf 노드에는 자식을 추가할 수 없음"""
        print("ERROR: you cannot add child node to leaf node")

    def add_children(self, *children):
        """Leaf 노드에는 자식을 추가할 수 없음"""
        print("ERROR: you cannot add children node to leaf node")

    def run(self):
        """
        Action 실행: 패턴 인스턴스의 update() 메서드 호출

        Returns:
            BehaviorTree.SUCCESS, BehaviorTree.RUNNING, 또는 BehaviorTree.FAIL
        """
        # 현재 실행 중인 패턴 인스턴스를 PantherAssassin에 저장
        # 이를 통해 PantherAssassin.draw()에서 패턴의 draw() 메서드를 호출할 수 있음
        self.action_instance.panther.current_action_instance = self.action_instance

        self.value = self.action_instance.update()
        return self.value


# ==================== 공격 패턴 클래스 ====================

class AttackPattern1Action:
    """
    패턴1 - 120도 방사형으로 플레이어를 향해 2단 표창 투척
    자세한 설명:
    공격 준비시 멈춘 후.
    1단계: 플레이어를 향해 7개의 표창을 120도 범위 내에 방사형으로 투척
    2단계: 1단계 이후 0.5초 이후 플레이어를 향해 7개의 표창을 120도 범위 내에 방사형으로 투척

    투사체는 PantherThrowingStar 클래스를 사용하며, 속도는 600 픽셀/초입니다.
    """

    # 클래스 레벨 이미지 시퀀스
    motion_img_seq = []  # PantherAssassin_Shuriken00~16.png (17개)
    fx_img_seq = []      # PantherAssassin_ShurikenFX00~08.png (9개)

    def __init__(self, panther):
        """
        Args:
            panther: PantherAssassin 인스턴스 참조
        """
        self.panther = panther
        self.phase = 0
        self.timer = 0.0
        # 표창 투척 관련 변수
        self.shot_count = 0  # 현재 투척 단계 (1단, 2단)
        self.max_shots = 2  # 총 투척 단계
        self.shot_interval = 0.25  # 투척 간격
        self.spread_angle = 120  # 방사형 각도
        self.projectiles_per_shot = 7  # 한 번에 발사하는 표창 개수

        # 애니메이션 관련
        self.motion_frame = 0
        self.motion_frame_timer = 0.0
        self.motion_frame_speed = 20.0  # 초당 프레임 수
        self.motion_total_frames = 17  # 0~16
        self.throw_frame = 9  # 9번 프레임에서 표창 발사
        self.has_thrown = False  # 현재 애니메이션에서 이미 던졌는지 체크

        # 이미지 로드 (클래스 레벨에서 한 번만)
        if not AttackPattern1Action.motion_img_seq:
            try:
                # 캐릭터 모션 이미지 로드 (0~16)
                for i in range(17):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Shuriken{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern1Action.motion_img_seq.append(img)
                print(f'[Pattern1] 캐릭터 모션 이미지 로드 완료: {len(AttackPattern1Action.motion_img_seq)}개')

                # 이펙트 이미지 로드 (0~8)
                for i in range(9):
                    fx_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/FX/PantherAssassin_ShurikenFX{i:02d}.png'
                    fx_img = p2.load_image(fx_path)
                    AttackPattern1Action.fx_img_seq.append(fx_img)
                print(f'[Pattern1] 이펙트 이미지 로드 완료: {len(AttackPattern1Action.fx_img_seq)}개')
            except FileNotFoundError as e:
                print(f'\033[91m[Pattern1] 이미지 로드 실패: {e}\033[0m')

    def update(self):
        """패턴 1 로직 실행"""
        dt = framework.get_delta_time()

        if self.phase == 0:
            # 초기화: 1단계 애니메이션 시작
            self.shot_count = 0
            self.timer = 0.0
            self.motion_frame = 0
            self.motion_frame_timer = 0.0
            self.has_thrown = False
            self.phase = 1
            print("[Pattern1] 1단계 애니메이션 시작!")

        elif self.phase == 1:
            # 1단계: 애니메이션 재생 및 9번 프레임에서 표창 발사
            self.motion_frame_timer += dt

            if self.motion_frame_timer >= 1.0 / self.motion_frame_speed:
                self.motion_frame += 1
                self.motion_frame_timer = 0.0

                # 9번 프레임에 도달하면 표창 발사
                if self.motion_frame == self.throw_frame and not self.has_thrown:
                    self._shoot_shurikens()
                    self.has_thrown = True
                    self.shot_count = 1
                    print("[Pattern1] 1단계 표창 발사!")

                # 애니메이션 종료 (16번 프레임까지)
                if self.motion_frame >= self.motion_total_frames:
                    self.timer = 0.0
                    self.phase = 2
                    print("[Pattern1] 1단계 완료, 2단계 대기")

        elif self.phase == 2:
            # 2단계 표창 발사 대기
            self.timer += dt

            if self.timer >= self.shot_interval:
                # 2단계 애니메이션 시작
                self.motion_frame = 0
                self.motion_frame_timer = 0.0
                self.has_thrown = False
                self.phase = 3
                print("[Pattern1] 2단계 애니메이션 시작!")

        elif self.phase == 3:
            # 2단계: 애니메이션 재생 및 9번 프레임에서 표창 발사
            self.motion_frame_timer += dt

            if self.motion_frame_timer >= 1.0 / self.motion_frame_speed:
                self.motion_frame += 1
                self.motion_frame_timer = 0.0

                # 9번 프레임에 도달하면 표창 발사
                if self.motion_frame == self.throw_frame and not self.has_thrown:
                    self._shoot_shurikens()
                    self.has_thrown = True
                    self.shot_count = 2
                    print("[Pattern1] 2단계 표창 발사!")

                # 애니메이션 종료 (16번 프레임까지)
                if self.motion_frame >= self.motion_total_frames:
                    self.phase = 4
                    print("[Pattern1] 2단계 완료")

        elif self.phase == 4:
            # 패턴 완료
            self.phase = 0
            self.panther.attack_timer = self.panther.attack_cooldown
            print("[Pattern1] 패턴 완료!")
            return BehaviorTree.SUCCESS

        return BehaviorTree.RUNNING

    def _shoot_shurikens(self):
        """플레이어를 향해 180도 범위 내에 9개의 표창을 방사형으로 발사"""
        if not self.panther.target:
            return

        # 플레이어를 향한 기본 각도 계산
        dx = self.panther.target.x - self.panther.x
        dy = self.panther.target.y - self.panther.y
        base_angle = math.atan2(dy, dx)

        # 방사형으로 표창 발사
        for i in range(self.projectiles_per_shot):
            # 180도를 9개로 나누어 각도 계산 (중앙을 기준으로 -90도 ~ +90도)
            offset_angle = (i - (self.projectiles_per_shot - 1) / 2) * (math.radians(self.spread_angle) / (self.projectiles_per_shot - 1))
            angle = base_angle + offset_angle

            # 표창의 목표 지점 계산 (멀리 날아가도록)
            distance = 1000  # 충분히 먼 거리
            target_x = self.panther.x + math.cos(angle) * distance
            target_y = self.panther.y + math.sin(angle) * distance

            # 표창 생성
            shuriken = PantherThrowingStar(
                self.panther.x,
                self.panther.y,
                target_x,
                target_y,
                speed=350,
                from_player=False,
                damage=20,
                scale=2.5
            )

            # world의 effects_front 레이어에 추가
            if self.panther.world and 'effects_front' in self.panther.world:
                self.panther.world['effects_front'].append(shuriken)
                print(f"[Pattern1] 표창 world 레이어에 추가: ({int(self.panther.x)}, {int(self.panther.y)}) -> ({int(target_x)}, {int(target_y)})")

    def draw(self, draw_x, draw_y):
        """
        패턴 1 시각 효과 드로잉

        Args:
            draw_x, draw_y: 보스의 현재 위치 (카메라 좌표계)
        """
        # 애니메이션 재생 중일 때 (phase 1 또는 3) - 공격 모션
        if self.phase in [1, 3]:
            # 캐릭터 모션 이미지 출력
            if AttackPattern1Action.motion_img_seq and self.motion_frame < len(AttackPattern1Action.motion_img_seq):
                img = AttackPattern1Action.motion_img_seq[self.motion_frame]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

            # 0~8번 프레임일 때 이펙트 출력
            if self.motion_frame <= 8 and AttackPattern1Action.fx_img_seq:
                if self.motion_frame < len(AttackPattern1Action.fx_img_seq):
                    fx_img = AttackPattern1Action.fx_img_seq[self.motion_frame]
                    if fx_img:
                        # 이펙트는 캐릭터와 같은 위치에 출력
                        fx_img.draw(draw_x, draw_y, fx_img.w * self.panther.scale_factor, fx_img.h * self.panther.scale_factor)

        # 2단계 대기 중일 때 (phase 2) - 마지막 프레임 유지하여 캐릭터 표시
        elif self.phase == 2:
            # 마지막 프레임(16번) 유지
            if AttackPattern1Action.motion_img_seq and len(AttackPattern1Action.motion_img_seq) > 0:
                last_frame_idx = min(self.motion_total_frames - 1, len(AttackPattern1Action.motion_img_seq) - 1)
                img = AttackPattern1Action.motion_img_seq[last_frame_idx]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)


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


class AttackPattern3Action:
    """
    패턴3 - 3단 콤보 공격
    자세한 설명:
    콤보 1: 1단 콤보 공격 준비 후 플레이어까지 거리의 1배 거리 만큼 0.5초만에 돌진하며 참격 (이미지상 위쪽으로 종 베기 참격 모션)
    콤보 2: 2단 콤보 공격 준비 후 플레이어까지 거리의 1.5배 거리 만큼 0.3초만에 돌진하며 참격 (돌진 횡 베기 참격 모션)
    콤보 3: 3단 콤보 공격 준비 후 제자리에서 원형으로 수리검 8방향 발사 (휠윈드 하며 수리검 발사 모션: Panther)

    모션 경로 = resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character
    콤보 1 공격 준비 모션 이미지 : PantherAssassin_Combo1_Ready{i:02d}.png 0 ~ 8
    콤보 1 돌진 모션 이미지 : PantherAssassin_Combo1_Attack{i:02d}.png 0 ~ 6
    콤보 2 공격 준비 모션 이미지 : PantherAssassin_Combo2_Ready{i:02d}.png 0 ~ 6
    콤보 2 돌진 모션 이미지 :    Start : PantherAssassin_Combo2_Attack_Start{i:02d}.png 0 ~ 3
                            Cycle   : PantherAssassin_Combo2_Attack_Cycle{i:02d}.png 0 ~ 3
    콤보 3 공격 준비 모션 이미지 : PantherAssassin_Combo3_Ready{i:02d}.png 0 ~ 3
    콤보 3 수리검 발사 모션 이미지 : PantherAssassin_Combo3_Attack{i:02d}.png 0 ~ 9

    이펙트 이미지 경로: resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/FX
    콤보 1 참격 이펙트 이미지 : PantherAssassin_Combo1_Attack_SwingFX{i:02d}.png 0 ~ 3 ( 대미지 있음 )
    콤보 2 참격 이펙트 이미지 : PantherAssassin_Combo2_Attack_SwingFX{i:02d}.png 0 ~ 3 ( 대미지 있음 )
    콥보 3 수리검 발사 이펙트 이미지 : PantherAssassin_Combo3_Attack_SwingFX{i:02d}.png 0 ~ 3 ( 대미지 없음 보여주기 용 )

    주의 : - 참격 이펙트는 PantherBladeSwingEffect 클래스가 독립적으로 관리하므로
            이 클래스 내부에서는 이펙트 리스트를 관리하지 않습니다. 하지만 수리검 발사 이펙트는 대미지가 없으므로
            이 클래스 내부에서 관리합니다.

         - 3단 콤보 공격이 모두 끝나면 패턴 종료

         - 왼쪽에서 오른쪽, 오른쪽에서 왼쪽 등 돌진 방향에 따라 이미지가 좌우 반전되어야 함


    """

    def __init__(self, panther):
        """
        Args:
            panther: PantherAssassin 인스턴스 참조
        """
        self.panther = panther
        self.phase = 0
        self.timer = 0.0
        # 은신 및 텔레포트 관련 변수
        self.stealth_duration = 0.0  # 은신 시간
        self.teleport_offset = 0  # 텔레포트 거리
        # 돌진 관련 변수
        self.dash_dx = 0.0
        self.dash_dy = 0.0
        self.dash_speed = 0.0
        self.dash_duration = 0.0
        # 수리검 투척 관련 변수
        self.projectile_directions = 8  # 8방향
        self.projectile_speed = 0.0

    def update(self):
        """패턴 3 로직 실행"""
        dt = framework.get_delta_time()

        if self.phase == 0:
            # 초기화
            self.timer = 0.0
            self.charge_time = 0.8  # 차징 시간
            self.phase = 1
            print("[Pattern3] 원형 투사체 차징 시작!")

        elif self.phase == 1:
            # 차징 중
            self.timer += dt

            if self.timer >= self.charge_time:
                # 차징 완료 - 8방향 발사
                if self.panther.world:
                    directions = 8
                    for i in range(directions):
                        angle = (360 / directions) * i
                        rad = math.radians(angle)

                        target_x = self.panther.x + math.cos(rad) * 1000
                        target_y = self.panther.y + math.sin(rad) * 1000

                        projectile = Projectile(
                            self.panther.x, self.panther.y,
                            target_x, target_y,
                            speed=400,
                            from_player=False
                        )
                        self.panther.world.get('projectiles', []).append(projectile)

                    print("[Pattern3] 원형 투사체 발사!")

                self.phase = 0
                self.panther.attack_timer = self.panther.attack_cooldown
                return BehaviorTree.SUCCESS

        return BehaviorTree.RUNNING

    def draw(self, draw_x, draw_y):
        """
        패턴 3 시각 효과 드로잉

        Args:
            draw_x, draw_y: 보스의 현재 위치 (카메라 좌표계)
        """
        # Pattern 3 Draw Logic: 원형 투사체 발사 시각 효과
        if self.phase == 1:  # 차징 중일 때
            # 차징 진행도에 따른 원형 링 표시
            progress = self.timer / self.charge_time
            charge_radius = 50 + progress * 100

            # 8방향 예측선 표시 (차징 중)
            directions = 8
            for i in range(directions):
                angle = (360 / directions) * i
                rad = math.radians(angle)
                end_x = draw_x + math.cos(rad) * charge_radius
                end_y = draw_y + math.sin(rad) * charge_radius
                p2.draw_line(draw_x, draw_y, end_x, end_y)

            # 차징 중심 원
            p2.draw_circle(draw_x, draw_y, int(charge_radius))


class AttackPattern4Action:
    """
    패턴4 - 은신과 분신 2체를 랜덤 위치에 소환 후 플레이어를 향해 수리검 10회 연속 투척 이후 본체 은신 풀림
    """

    def __init__(self, panther):
        """
        Args:
            panther: PantherAssassin 인스턴스 참조
        """
        self.panther = panther
        self.phase = 0
        self.timer = 0.0
        # 은신 관련 변수
        self.stealth_duration = 0.0  # 은신 시간
        self.is_stealthed = False  # 은신 상태
        # 분신 소환 관련 변수
        self.clone_count = 2  # 분신 개수
        self.clone_positions = []  # 분신 위치 리스트
        self.summon_time = 0.0  # 소환 시간
        # 수리검 투척 관련 변수
        self.shot_count = 0  # 현재 투척 횟수
        self.max_shots = 10  # 최대 투척 횟수 (10회)
        self.shot_interval = 0.0  # 투척 간격
        self.projectile_speed = 0.0

    def update(self):
        """패턴 4 로직 실행"""
        dt = framework.get_delta_time()

        if self.phase == 0:
            # 초기화
            self.timer = 0.0
            self.stealth_duration = 1.0  # 은신 지속 시간
            self.phase = 1
            print("[Pattern4] 은신 시작!")

        elif self.phase == 1:
            # 은신 중
            self.timer += dt

            if self.timer >= self.stealth_duration:
                # 은신 종료
                self.is_stealthed = False
                self.timer = 0.0
                self.phase = 2
                print("[Pattern4] 은신 종료!")

        elif self.phase == 2:
            # 분신 소환
            if len(self.clone_positions) < self.clone_count:
                angle = random.uniform(0, 360)
                rad = math.radians(angle)
                offset = 100 + random.uniform(-50, 50)

                clone_x = self.panther.x + math.cos(rad) * offset
                clone_y = self.panther.y + math.sin(rad) * offset
                self.clone_positions.append((clone_x, clone_y))

                print(f"[Pattern4] 분신 소환: ({clone_x:.0f}, {clone_y:.0f})")
                return BehaviorTree.RUNNING

            # 모든 분신 소환 완료 후 수리검 투척
            if self.timer == 0.0:
                self.shot_count = 0
                self.timer = 0.0
                self.phase = 3
                print("[Pattern4] 수리검 투척 시작!")

        elif self.phase == 3:
            # 수리검 투척
            self.timer += dt

            if self.timer >= self.shot_interval:
                # 수리검 발사
                if self.panther.target and self.panther.world:
                    projectile = Projectile(
                        self.panther.x, self.panther.y,
                        self.panther.target.x, self.panther.target.y,
                        speed=500,
                        from_player=False
                    )
                    self.panther.world.get('projectiles', []).append(projectile)
                    print(f"[Pattern4] 수리검 발사 {self.shot_count + 1}/{self.max_shots}")

                self.shot_count += 1
                self.timer = 0.0

                if self.shot_count >= self.max_shots:
                    # 모든 수리검 발사 완료
                    self.phase = 0
                    self.panther.attack_timer = self.panther.attack_cooldown
                    print("[Pattern4] 수리검 투척 완료!")
                    return BehaviorTree.SUCCESS

        return BehaviorTree.RUNNING

    def draw(self, draw_x, draw_y):
        """
        패턴 4 시각 효과 드로잉

        Args:
            draw_x, draw_y: 보스의 현재 위치 (카메라 좌표계)
        """
        # Pattern 4 Draw Logic: 은신 및 분신 소환 시각 효과
        if self.phase == 1:  # 은신 중일 때
            # 은신 이펙트 원 (점점 투명해지는 원)
            progress = self.timer / self.stealth_duration
            effect_radius = 50 + progress * 50
            p2.draw_circle(draw_x, draw_y, int(effect_radius), alpha=255 - int(progress * 255))

        elif self.phase == 2:  # 분신 소환 중
            # 소환 위치에 원 표시
            for clone_x, clone_y in self.clone_positions:
                p2.draw_circle(clone_x, clone_y, 10)

        elif self.phase == 3:  # 수리검 투척 중
            # 타겟 방향 조준선 표시
            if self.panther.target:
                p2.draw_line(draw_x, draw_y, self.panther.target.x, self.panther.target.y)

            # 발사 카운트 표시 (원형 인디케이터)
            progress = self.shot_count / self.max_shots
            indicator_radius = 20 + progress * 30
            p2.draw_circle(draw_x, draw_y + 60, int(indicator_radius))


class AttackPattern5Action:
    """
    패턴5 - 분신 1체 랜덤 위치에 소환후 모든 방향 방사형으로 수리검 투척 2회 ( 두 번째 투척 수리검의 속도는 첫 번째 투척 속도의 반 )
    """

    def __init__(self, panther):
        """
        Args:
            panther: PantherAssassin 인스턴스 참조
        """
        self.panther = panther
        self.phase = 0
        self.timer = 0.0
        # 분신 소환 관련 변수
        self.clone_count = 1  # 분신 개수 (1체)
        self.clone_position = None  # 분신 위치
        self.summon_time = 0.0  # 소환 시간
        # 수리검 투척 관련 변수
        self.shot_count = 0  # 현재 투척 횟수 (1회, 2회)
        self.max_shots = 2  # 최대 투척 횟수 (2회)
        self.projectile_directions = 0  # 모든 방향 (360도)
        self.first_speed = 0.0  # 첫 번째 투척 속도
        self.second_speed = 0.0  # 두 번째 투척 속도 (첫 번째의 반)

    def update(self):
        """패턴 5 로직 실행"""
        dt = framework.get_delta_time()

        if self.phase == 0:
            # 초기화
            self.timer = 0.0
            self.summon_time = 0.5  # 소환 시간
            self.phase = 1
            print("[Pattern5] 분신 소환 시작!")

        elif self.phase == 1:
            # 소환 중
            self.timer += dt

            if self.timer >= self.summon_time:
                # 분신 소환 완료
                if self.panther.world and self.panther.target:
                    # 분신 위치 계산
                    offset = 200
                    clone_positions = [
                        (self.panther.x - offset, self.panther.y),
                        (self.panther.x + offset, self.panther.y)
                    ]

                    # 분신에서 타겟으로 투사체 발사
                    for clone_x, clone_y in clone_positions:
                        projectile = Projectile(
                            clone_x, clone_y,
                            self.panther.target.x, self.panther.target.y,
                            speed=450,
                            from_player=False
                        )
                        self.panther.world.get('projectiles', []).append(projectile)

                    print("[Pattern5] 분신 공격 발사!")

                self.timer = 0.0
                self.phase = 2

        elif self.phase == 2:
            # 분신 유지
            self.timer += dt

            if self.timer >= self.duration:
                # 분신 소멸
                self.phase = 0
                self.panther.attack_timer = self.panther.attack_cooldown
                print("[Pattern5] 분신 소멸!")
                return BehaviorTree.SUCCESS

        return BehaviorTree.RUNNING

    def draw(self, draw_x, draw_y):
        """
        패턴 5 시각 효과 드로잉

        Args:
            draw_x, draw_y: 보스의 현재 위치 (카메라 좌표계)
        """
        # Pattern 5 Draw Logic: 광역 충격파 시각 효과
        if self.phase == 1:  # 차징 중
            # 차징 이펙트 (맥동하는 원)
            pulse = (self.timer / self.charge_time) * 50
            p2.draw_circle(draw_x, draw_y, int(50 + pulse))
            p2.draw_circle(draw_x, draw_y, int(30 + pulse))

        elif self.phase == 2:  # 충격파 확산 중
            # 확산되는 충격파 원 그리기
            p2.draw_circle(draw_x, draw_y, int(self.shockwave_radius))

            # 내부 충격파 (투명도 효과를 위한 다중 원)
            if self.shockwave_radius > 20:
                p2.draw_circle(draw_x, draw_y, int(self.shockwave_radius - 20))


class AttackPattern6Action:
    """
    패턴6 - 분신 2체 램덤 위치에 소환후 본체, 분신 2체 번갈아 가며 플레이어를 향해 수리검 5개 방사형으로 3회씩 투척
    """
    img_seq = []
    def __init__(self, panther):
        """
        Args:
            panther: PantherAssassin 인스턴스 참조
        """
        self.panther = panther
        self.phase = 0
        self.timer = 0.0
        # 분신 소환 관련 변수
        self.clone_count = 2  # 분신 개수 (2체)
        self.clone_positions = []  # 분신 위치 리스트
        self.summon_time = 0.0  # 소환 시간
        # 수리검 투척 관련 변수
        self.current_shooter = 0  # 현재 투척하는 개체 (0: 본체, 1: 분신1, 2: 분신2)
        self.shot_count_per_shooter = 0  # 각 개체당 투척 횟수
        self.max_shots_per_shooter = 3  # 각 개체당 최대 투척 횟수 (3회씩)
        self.projectiles_per_shot = 5  # 한 번에 발사하는 수리검 개수 (5개)
        self.spread_angle = 0.0  # 방사형 각도
        self.shot_interval = 0.0  # 투척 간격
        # 분신 이미지 시퀀스 로드
        self.img_count = 8
        # if not AttackPattern6Action.img_seq:
        #     try:
        #         for i in range(self.img_count):
        #             img = p2.load_image(f'')
        #             AttackPattern6Action.img_seq.append(img)
        #     except FileNotFoundError as e:
        #         print(f'\033[91m[Pattern6] 이미지 로드 실패: {e}\033[0m')

    def update(self):
        """패턴 6 로직 실행"""
        dt = framework.get_delta_time()

        if self.phase == 0:
            # 초기화
            self.timer = 0.0
            self.summon_time = 0.5  # 소환 시간
            self.phase = 1
            print("[Pattern6] 분신 소환 시작!")

        elif self.phase == 1:
            # 소환 중
            self.timer += dt

            if self.timer >= self.summon_time:
                # 분신 소환 완료
                if self.panther.world and self.panther.target:
                    # 분신 위치 계산
                    offset = 200
                    clone_positions = [
                        (self.panther.x - offset, self.panther.y),
                        (self.panther.x + offset, self.panther.y)
                    ]

                    # 분신에서 타겟으로 투사체 발사
                    for clone_x, clone_y in clone_positions:
                        projectile = Projectile(
                            clone_x, clone_y,
                            self.panther.target.x, self.panther.target.y,
                            speed=450,
                            from_player=False
                        )
                        self.panther.world.get('projectiles', []).append(projectile)

                    print("[Pattern6] 분신 공격 발사!")

                self.timer = 0.0
                self.duration = 1.0  # 분신 유지 시간
                self.phase = 2

        elif self.phase == 2:
            # 분신 유지
            self.timer += dt

            if self.timer >= self.duration:
                # 분신 소멸
                self.phase = 0
                self.panther.attack_timer = self.panther.attack_cooldown
                print("[Pattern6] 분신 소멸!")
                return BehaviorTree.SUCCESS

        return BehaviorTree.RUNNING

    def draw(self, draw_x, draw_y):
        """
        패턴 6 시각 효과 드로잉

        Args:
            draw_x, draw_y: 보스의 현재 위치 (카메라 좌표계)
        """
        # 공격 패턴 전용 이미지가 있다면 사용, 없다면 기본 드로잉 사용


        # Pattern 6 Draw Logic: 그림자 분신 소환 시각 효과
        if self.phase == 1:  # 소환 중
            # 소환 진행도 표시
            progress = self.timer / self.summon_time
            summon_radius = 40 + progress * 60

            # 분신 소환 위치에 원 표시
            offset = 200
            clone_positions = [
                (draw_x - offset, draw_y),
                (draw_x + offset, draw_y)
            ]

            for clone_x, clone_y in clone_positions:
                p2.draw_circle(clone_x, clone_y, summon_radius)
                p2.draw_line(draw_x, draw_y, clone_x, clone_y)

        elif self.phase == 2:  # 분신 유지 중
            # 분신 위치 표시 (반투명 효과를 위한 다중 원)
            offset = 200
            clone_positions = [
                (draw_x - offset, draw_y),
                (draw_x + offset, draw_y)
            ]

            for clone_x, clone_y in clone_positions:
                p2.draw_circle(clone_x, clone_y, 70)
                p2.draw_circle(clone_x, clone_y, 50)


# ==================== PantherAssassin 보스 클래스 ====================

class PantherAssassin:
    """
    팬서 암살자 보스 몬스터

    특징:
    - 6가지 공격 패턴을 랜덤하게 사용
    - 행동 트리 기반 AI
    - 높은 체력과 공격력
    """

    def __init__(self, x, y):
        """
        PantherAssassin 초기화

        Args:
            x, y: 스폰 위치
        """
        # 위치 및 기본 속성
        self.x = x
        self.y = y
        self.spawn_x = x  # 스폰 위치 기억
        self.spawn_y = y

        # 스탯
        from ..stats import PantherAssassinStats
        self.stats = PantherAssassinStats()

        # 애니메이션
        self.frame = 0
        self.frame_timer = 0.0
        self.frame_speed = 15.0  # 초당 프레임 수
        self.scale_factor = 4.0
        self.animation_frames = 11 # 애니메이션 프레임 수

        # 충돌 박스
        self.collision_width = 24 * self.scale_factor
        self.collision_height = 26 * self.scale_factor
        self.collision_box_offset_x = 0
        self.collision_box_offset_y = -10 * self.scale_factor

        # 타겟 (플레이어)
        self.target = None

        # 월드 참조 (투사체 생성을 위해)
        from ..play_mode import world
        self.world = world

        # 투사체 관리 (보스 전용 투사체 리스트)
        self.projectiles = []

        # 공격 관련
        self.recognition_distance = 400 # 플레이어 인식 거리
        self.unrecognition_distance = 800 # 플레이어 미인식 거리
        self.attack_range = 800  # 공격 범위 (추가)
        self.attack_cooldown = 2.0  # 공격 쿨타임 (초)
        self.attack_timer = 0.0  # 현재 쿨타임 타이머

        # 무적시간 관련 변수 (피격 판정 중복 방지)
        self.invincible = False
        self.invincible_timer = 0.0
        self.invincible_duration = 0.3  # 무적 지속 시간 (초)

        # 제거 플래그
        self.mark_for_removal = False

        # 체력바 UI
        self.health_bar = MonsterHealthBar(self)

        # 현재 실행 중인 공격 패턴 인스턴스 (드로잉 책임 위임용)
        self.current_action_instance = None

        # 6가지 공격 패턴 클래스 인스턴스 생성
        self.pattern1_action = AttackPattern1Action(self)
        self.pattern2_action = AttackPattern2Action(self)
        self.pattern3_action = AttackPattern3Action(self)
        self.pattern4_action = AttackPattern4Action(self)
        self.pattern5_action = AttackPattern5Action(self)
        self.pattern6_action = AttackPattern6Action(self)

        # 임시 스프라이트 (실제 게임에서는 이미지 로드)
        # 일반적으로 Idle 애니메이션 스프라이트 시트 사용
        # 사망시 Death 애니메이션 스프라이트 시트 사용
        self.images = None
        self.clone_images = None

        # 사망 애니메이션 관련 변수
        self.is_dead = False
        self.death_images = None
        self.death_frame = 0
        self.death_frame_timer = 0.0
        self.death_frame_speed = 5.0  # 초당 프레임 수
        self.death_animation_frames = 16  # 0~15 총 16개 프레임

        try:
            # Idle 애니메이션 로드
            for i in range(self.animation_frames):
                try:
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Idle{i:02d}.png'
                    img = p2.load_image(img_path)
                    if self.images is None:
                        self.images = []
                    self.images.append(img)

                    # 경로 등록 후 어두운 버전 생성
                    iam.register_image_path(img, img_path)
                    clone_img = iam.make_dark(img, darkness=0.25)
                    if self.clone_images is None:
                        self.clone_images = []
                    self.clone_images.append(clone_img)

                    # DEBUG: 이미지 로드 확인
                    print(f'[PantherAssassin] 이미지 로드 성공: PantherAssassin_Idle{i:02d}.png')

                except FileNotFoundError as e:
                    print(f'\033[91m[PantherAssassin] 이미지 로드 실패: {e}\033[0m')

            # Death 애니메이션 로드 (0~15)
            self.death_images = []

            for i in range(3):
                try:
                    Airborne_img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Airborne{i:02d}.png'
                    Airborne_img = p2.load_image(Airborne_img_path)
                    self.death_images.append(Airborne_img)
                    print(f'[PantherAssassin] 사망 애니메이션 로드 성공: PantherAssassin_Knockback{i:02d}.png')
                except FileNotFoundError as e:
                    print(f'\033[91m[PantherAssassin] 사망 애니메이션 로드 실패: {e}\033[0m')

            for i in range(self.death_animation_frames):
                try:
                    death_img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_TrueDie{i:02d}.png'
                    death_img = p2.load_image(death_img_path)
                    self.death_images.append(death_img)
                    print(f'[PantherAssassin] 사망 애니메이션 로드 성공: PantherAssassin_TrueDie{i:02d}.png')
                except FileNotFoundError as e:
                    print(f'\033[91m[PantherAssassin] 사망 애니메이션 로드 실패: {e}\033[0m')

        except Exception as e:
            print(f'\033[91m[PantherAssassin] 이미지 로드 중 오류 발생: {e}\033[0m')

        # 행동 트리 빌드
        self.build_behavior_tree()

        print(f"[PantherAssassin] 생성됨 at ({x}, {y})")

    def build_behavior_tree(self):
        """
        행동 트리 구축

        구조:
        Root Selector
        ├── Attack Sequence (공격 시도)
        │   ├── Condition: 쿨타임 준비됨
        │   ├── Condition: 공격 범위 내
        │   └── RandomSelector: 6가지 패턴 중 랜덤 선택
        │       ├── BTActionWrapper: 패턴1 - 120도 방사형으로 플레이어를 향해 2단 표창 투척
        │       ├── BTActionWrapper: 패턴2 - 은신 후 다른 곳에서 나타나 플레이어를 향해 강한 돌진 공격 2회
        │       ├── BTActionWrapper: 패턴3 - 3단 콤보 공격
        │       │   # 그림자 분신과 함게하는 패턴 4, 5, 6
        │       ├── BTActionWrapper: 패턴4 - 은신과 분신 2체를 랜덤 위치에 소환 후 플레이어를 향해 수리검 10회 연속 투척 이후 본체 은신 풀림
        │       ├── BTActionWrapper: 패턴5 - 분신 1체 랜덤 위치에 소환후 모든 방향 방사형으로 수리검 투척 2회 ( 두 번째 투척 수리검의 속도는 첫 번째 투척 속도의 반 )
        │       └── BTActionWrapper: 패턴6 - 분신 2체 램덤 위치에 소환후 본체, 분신 2체 번갈아 가며 플레이어를 향해 수리검 5개 방사형으로 3회씩 투척
        └── Action: 대기 ( Idle )

        ★ 핵심: BTActionWrapper를 사용하여 패턴 클래스 인스턴스를 BT에 연결
        """

        # 6가지 공격 패턴을 RandomSelector로 구성
        # BTActionWrapper를 사용하여 패턴 클래스 인스턴스를 감쌈
        attack_pattern_selector = RandomSelector(
            "Random Attack Pattern",
            BTActionWrapper("Pattern1: ThrowingStars", self.pattern1_action),
            BTActionWrapper("Pattern2: DashAttack", self.pattern2_action),
            # BTActionWrapper("Pattern3: Circular", self.pattern3_action),
            # BTActionWrapper("Pattern4: Teleport", self.pattern4_action),
            # BTActionWrapper("Pattern5: Shockwave", self.pattern5_action),
            # BTActionWrapper("Pattern6: Shadow Clone", self.pattern6_action)
        )

        # 공격 시퀀스: 쿨타임 체크 -> 범위 체크 -> 패턴 실행
        attack_sequence = Sequence(
            "Try Attack",
            Condition("Attack Ready", self.is_attack_ready),
            Condition("In Attack Range", self.is_in_attack_range),
            attack_pattern_selector
        )

        # 루트 셀렉터: 공격 가능하면 공격, 아니면 대기/순찰
        root = Selector(
            "Root",
            attack_sequence,
            Action("Idle or Patrol", self.handle_idle_action)
        )

        # 행동 트리 생성
        self.behavior_tree = BehaviorTree(root)
        print("[PantherAssassin] 행동 트리 빌드 완료 (BTActionWrapper 적용 완료)")

    # ==================== 조건 체크 메서드 ====================

    def is_attack_ready(self):
        """공격 쿨타임이 준비되었는지 확인"""
        return self.attack_timer <= 0.0

    def is_in_attack_range(self):
        """타겟이 공격 범위 내에 있는지 확인"""
        if self.target is None:
            return False

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        return distance <= self.attack_range

    # ==================== 행동 액션 메서드 ====================

    def handle_idle_action(self):
        """
        대기 행동

        PantherAssassin은 패턴 기반 보스이므로 플레이어를 추적하지 않고
        제자리에서 대기합니다.
        """
        # 플레이어 추적 로직 제거 - 패턴으로만 위치 이동
        return BehaviorTree.SUCCESS

    # ==================== 업데이트 & 렌더링 ====================

    def update(self):
        """매 프레임 업데이트"""
        dt = framework.get_delta_time()

        # 사망 상태일 경우 사망 애니메이션만 재생
        if self.is_dead:
            self.death_frame_timer += dt
            if self.death_frame_timer >= 1.0 / self.death_frame_speed:
                self.death_frame += 1
                self.death_frame_timer = 0.0

                # 사망 애니메이션이 끝나면 (0~15 프레임 완료)
                if self.death_frame >= self.death_animation_frames:
                    print("[PantherAssassin] 사망 애니메이션 완료 - 제거")
                    self.mark_for_removal = True
            return  # 사망 애니메이션 진행 중 - 아무것도 반환하지 않음

        # 무적시간 업데이트
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
                self.invincible_timer = 0.0

        # 쿨타임 업데이트
        if self.attack_timer > 0:
            self.attack_timer -= dt

        # 애니메이션 프레임 업데이트
        self.frame_timer += dt
        if self.frame_timer >= 1.0 / self.frame_speed:
            # 이미지가 로드되었을 때만 프레임 업데이트
            if self.images and len(self.images) > 0:
                self.frame = (self.frame + 1) % len(self.images)
            else:
                self.frame = 0
            self.frame_timer = 0.0

        # 플레이어 인식 거리 체크 (target이 None일 때 예외 처리)
        if self.target is not None:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            distance = math.sqrt(dx**2 + dy**2)

            # 인식 거리를 벗어나면 타겟 해제
            if distance >= self.unrecognition_distance:
                self.set_target(None)
                print(f'[PantherAssassin] 타겟 상실 (거리: {distance:.1f})')
        else:
            # 타겟이 없을 때 플레이어 탐색
            if self.world and 'player' in self.world:
                player = self.world['player']
                dx = player.x - self.x
                dy = player.y - self.y
                distance = math.sqrt(dx**2 + dy**2)

                # 인식 거리 내에 들어오면 타겟 설정
                if distance <= self.recognition_distance:
                    self.set_target(player)
                    print(f'[PantherAssassin] 타겟 인식: 플레이어 at ({player.x}, {player.y}), 거리: {distance:.1f}')

        # 투사체 업데이트 (보스 전용 투사체 관리)
        self.projectiles = [proj for proj in self.projectiles if proj.update()]

        # 행동 트리 실행
        if self.behavior_tree:
            self.behavior_tree.run()



    def draw(self, draw_x, draw_y):
        """
        몬스터 렌더링

        렌더링 우선순위:
        1. 사망 상태일 경우 사망 애니메이션 출력
        2. 패턴 공격 중이면 패턴 전용 모션 출력 (IDLE 모션 숨김)
        3. 패턴 공격이 아니면 IDLE 모션 출력

        일반적 Hit 일땐 대미지만 적용, (hit 판정의 이미지 시퀀스 x )
        Death 상태 일땐 현재 이미지 시퀀스를 Death 이미지로 교체 후 재생
        1. Hit 판정시 이미지 시퀀스 교체 없이 대미지만 적용
        2. Death 판정시 이미지 시퀀스를 Death 이미지로 교체
        3. Death 이미지 시퀀스 재생 완료 후 몬스터 제거

        TODO: 1. 몬스터 사망 후 아이템 드랍 구현
        """
        # 사망 상태일 경우 사망 애니메이션 출력
        if self.is_dead:
            if self.death_images and len(self.death_images) > 0:
                # 사망 프레임 인덱스가 범위를 벗어나지 않도록 보정
                death_frame_idx = min(self.death_frame, len(self.death_images) - 1)
                death_img = self.death_images[death_frame_idx]
                if death_img:
                    death_img.draw(draw_x, draw_y, death_img.w * self.scale_factor, death_img.h * self.scale_factor)
            return  # 사망 애니메이션 출력 후 나머지는 렌더링하지 않음

        # 현재 실행 중인 패턴이 있는지 확인
        has_active_pattern = (self.current_action_instance is not None and
                             hasattr(self.current_action_instance, 'phase') and
                             self.current_action_instance.phase > 0)

        # 패턴 공격 중이 아닐 때만 IDLE 모션 드로잉
        if not has_active_pattern:
            if self.images and len(self.images) > 0:
                # 프레임 인덱스가 범위를 벗어나지 않도록 보정
                if self.frame >= len(self.images):
                    self.frame = 0

                img = self.images[self.frame]
                img.draw(draw_x, draw_y, img.w * self.scale_factor, img.h * self.scale_factor)
            else:
                # 디버그 렌더링 (이미지 없을 때)
                p2.draw_rectangle(
                    self.x - self.collision_width / 2,
                    self.y - self.collision_height / 2,
                    self.x + self.collision_width / 2,
                    self.y + self.collision_height / 2
                )

        # 현재 실행 중인 패턴 인스턴스의 이펙트 드로잉 (드로잉 책임 위임)
        # 패턴이 활성화되어 있으면 패턴의 draw 메서드가 캐릭터 모션과 이펙트를 모두 그림
        if self.current_action_instance is not None:
            # 패턴 인스턴스가 draw 메서드를 가지고 있는지 확인 후 호출
            if hasattr(self.current_action_instance, 'draw'):
                self.current_action_instance.draw(draw_x, draw_y)

        # 보스 전용 투사체 드로잉 (카메라 좌표 변환 적용)
        for projectile in self.projectiles:
            # 투사체의 월드 좌표를 카메라 좌표로 변환
            proj_draw_x = projectile.x - self.x + draw_x
            proj_draw_y = projectile.y - self.y + draw_y
            projectile.draw(proj_draw_x, proj_draw_y)

        # 체력바 렌더링 (카메라 좌표 적용)
        self.health_bar.draw(draw_x, draw_y - 70)

        # DEBUG : 충돌 박스 및 플레이어 인식 범위 그리기
        # 충돌 박스 : 카메라 좌표계로 변환 후 그리기
        Left, Bottom, Right, Top = self.get_bb()
        Left -= self.x - draw_x
        Right -= self.x - draw_x
        Bottom -= self.y - draw_y
        Top -= self.y - draw_y
        p2.draw_rectangle(Left, Bottom, Right, Top, r=255, g=0, b=0)

        # 공격 범위
        radius = self.recognition_distance
        p2.draw_circle(draw_x, draw_y, int(radius), r=255, g=255, b=0)

        # 타겟 놓치는 거리
        radius = self.unrecognition_distance
        p2.draw_circle(draw_x, draw_y, int(radius), r=0, g=255, b=255)

        # 분신 드로잉 (디버그용)
        if self.clone_images:
            offset = 200
            self.clone_images[self.frame].draw(draw_x - offset, draw_y,
                                               self.clone_images[self.frame].w * self.scale_factor,
                                               self.clone_images[self.frame].h * self.scale_factor)


    def get_bb(self):
        """충돌 박스 반환 (left, bottom, right, top)"""
        half_w = self.collision_width / 2
        half_h = self.collision_height / 2
        return (
            self.x - half_w + self.collision_box_offset_x,
            self.y - half_h + self.collision_box_offset_y,
            self.x + half_w + self.collision_box_offset_x,
            self.y + half_h + self.collision_box_offset_y
        )

    def take_damage(self, damage):
        """피해를 받음"""
        # 이미 사망 상태면 무시
        if self.is_dead:
            return False

        current_health = self.stats.get('health')
        self.stats.set_base('health', max(0, current_health - damage))
        print(f"[PantherAssassin] 피해 {damage}, 남은 HP: {self.stats.get('health')}/{self.stats.get('max_health')}")

        if self.stats.get('health') <= 0:
            print("[PantherAssassin] 사망 - 애니메이션 시작!")
            # 사망 애니메이션 플래그 설정
            self.is_dead = True
            self.death_frame = 0
            self.death_frame_timer = 0.0
            # 즉시 제거하지 않고 애니메이션이 끝날 때까지 기다림
        return False  # 사망 상태라도 애니메이션이 끝날 때까지 False 반환

    def set_target(self, target):
        """타겟 설정 (주로 플레이어)"""
        self.target = target

    # ==================== 피격 판정 메서드 ====================

    def check_collision_with_effect(self, effect):
        """
        플레이어 공격 이펙트와의 충돌 감지

        Args:
            effect: VFX_Tier1_Sword_Swing 등의 공격 이펙트 객체

        Returns:
            bool: 충돌 여부
        """
        # 사망 상태이거나 무적 상태이면 충돌 무시
        if self.is_dead or self.invincible:
            return False

        # 이펙트의 크기 계산
        if hasattr(effect, 'frames') and len(effect.frames) > 0:
            effect_img = effect.frames[min(effect.frame, len(effect.frames) - 1)]
            effect_width = effect_img.w * effect.scale_factor
            effect_height = effect_img.h * effect.scale_factor
        else:
            # 기본값
            effect_width = 200
            effect_height = 200

        # AABB 충돌 감지
        panther_left = self.x - self.collision_width / 2
        panther_right = self.x + self.collision_width / 2
        panther_bottom = self.y - self.collision_height / 2
        panther_top = self.y + self.collision_height / 2

        effect_left = effect.x - effect_width / 2
        effect_right = effect.x + effect_width / 2
        effect_bottom = effect.y - effect_height / 2
        effect_top = effect.y + effect_height / 2

        # 충돌 검사
        if (panther_left < effect_right and panther_right > effect_left and
            panther_bottom < effect_top and panther_top > effect_bottom):
            # 충돌 시 피격 처리
            self.on_hit(effect)
            return True

        return False

    def check_collision_with_projectile(self, projectile):
        """
        플레이어 투사체와의 충돌 감지

        Args:
            projectile: Projectile을 상속받은 발사체 객체

        Returns:
            bool: 충돌 여부
        """
        # 무적 상태이면 충돌 무시
        if self.invincible:
            return False

        # 발사체 크기
        if hasattr(projectile, 'get_collision_box'):
            projectile_width, projectile_height = projectile.get_collision_box()
        else:
            projectile_width = 30
            projectile_height = 30

        # AABB 충돌 감지
        panther_left = self.x - self.collision_width / 2
        panther_right = self.x + self.collision_width / 2
        panther_bottom = self.y - self.collision_height / 2
        panther_top = self.y + self.collision_height / 2

        proj_left = projectile.x - projectile_width / 2
        proj_right = projectile.x + projectile_width / 2
        proj_bottom = projectile.y - projectile_height / 2
        proj_top = projectile.y + projectile_height / 2

        # 충돌 검사
        if (panther_left < proj_right and panther_right > proj_left and
            panther_bottom < proj_top and panther_top > proj_bottom):
            # 충돌 시 피격 처리
            self.on_hit(projectile)
            return True

        return False

    def on_hit(self, attacker):
        """
        피격 시 호출되는 메서드

        Args:
            attacker: 공격한 객체 (투사체, 이펙트 등)
        """
        # 무적 상태라면 무시
        if self.invincible:
            print(f"[PantherAssassin] 무적 상태로 피격 무시 (남은 무적시간: {self.invincible_timer:.2f}초)")
            return

        # 무적시간 활성화
        self.invincible = True
        self.invincible_timer = self.invincible_duration

        # 데미지 계산
        damage = 0
        if hasattr(attacker, 'damage'):
            damage = attacker.damage
        elif hasattr(attacker, 'owner') and hasattr(attacker.owner, 'statss'):
            # 공격자의 스탯에서 데미지 가져오기
            damage = attacker.owner.statss.get('attack_damage')
        else:
            damage = 10.0  # 기본 데미지

        # 방어력 적용
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
                # 보스 위치 위쪽에 데미지 인디케이터 생성
                damage_indicator = DamageIndicator(
                    self.x,
                    self.y + 50,  # 보스 위치보다 50 픽셀 위에 표시
                    final_damage,
                    duration=1.0,
                    font_size=40  # 보스는 큰 폰트 사용
                )
                self.world['effects_front'].append(damage_indicator)
                print(f"[PantherAssassin] 데미지 인디케이터 생성: {int(final_damage)} 데미지")
            except Exception as e:
                print(f"[PantherAssassin] 데미지 인디케이터 생성 실패: {e}")

        # 피격 정보 출력 (디버그)
        attacker_name = attacker.__class__.__name__
        print(f"\n{'=' * 60}")
        print(f"[PantherAssassin 피격] at ({int(self.x)}, {int(self.y)})")
        print(f"  공격자: {attacker_name}")
        print(f"  원본 데미지: {damage:.1f}")
        print(f"  방어력: {defense:.1f}")
        print(f"  최종 데미지: {final_damage:.1f}")
        print(f"  체력 변화: {current_health:.1f} -> {new_health:.1f} (최대: {max_health:.1f})")
        print(f"  체력 비율: {(new_health / max_health) * 100:.1f}%")
        print(f"  무적시간: {self.invincible_duration}초 활성화")

        # 체력이 0 이하면 사망 처리
        if new_health <= 0:
            print(f"  >>> PantherAssassin 체력 0 - 사망 애니메이션 시작!")
            print(f"{'=' * 60}\n")
            # 사망 애니메이션 플래그 설정
            self.is_dead = True
            self.death_frame = 0
            self.death_frame_timer = 0.0
            # 즉시 제거하지 않고 애니메이션이 끝날 때까지 기다림
        else:
            print(f"{'=' * 60}\n")


# ==================== PantherThrowingStar 투사체 클래스 ====================

class PantherThrowingStar(Projectile):
    """
    팬서 암살자 보스의 표창 투사체
    회전하는 애니메이션과 함께 날아가는 표창입니다.
    """
    image_seq = []

    def __init__(self, x, y, target_x, target_y, speed=400, from_player=False, damage=15, scale=1.2):
        """
        PantherThrowingStar 초기화

        Args:
            x, y: 시작 위치
            target_x, target_y: 목표 위치
            speed: 투사체 속도
            from_player: 플레이어가 발사했는지 여부
            damage: 투사체 피해량
            scale: 이미지 크기 배율
        """
        super().__init__(x, y, target_x, target_y, speed, from_player)

        # 투사체 속성
        self.damage = damage
        self.scale = scale
        self.collision_width = int(13 * scale)
        self.collision_height = int(20 * scale)

        # 애니메이션 관련 변수
        self.animation_timer = 0.0
        self.animation_frame = 0
        self.animation_frame_duration = 0.1  # 각 프레임당 0.1초

        # 이미지 로드 (클래스 레벨에서 한 번만)
        if not PantherThrowingStar.image_seq:
            try:
                for i in range(4):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/FX/PantherAssassin_ShurikenBullet{i:02d}.png'
                    PantherThrowingStar.image_seq.append(p2.load_image(img_path))
                print(f'[PantherThrowingStar] 이미지 로드 완료: {len(PantherThrowingStar.image_seq)}개 애니메이션 프레임')
            except FileNotFoundError as e:
                print(f'\033[91m[PantherThrowingStar] 이미지 로드 실패: {e}\033[0m')

    def update(self):
        """표창 업데이트"""
        dt = framework.get_delta_time()

        # 애니메이션 업데이트
        self.animation_timer += dt
        if self.animation_timer >= self.animation_frame_duration:
            self.animation_timer -= self.animation_frame_duration
            self.animation_frame = (self.animation_frame + 1) % len(PantherThrowingStar.image_seq)

        # 일반 이동 로직
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt

        # 화면 밖으로 나가면 제거
        if (self.x < -1000 or self.x > 5000 or
            self.y < -1000 or self.y > 5000):
            return False

        return True

    def draw(self, draw_x, draw_y):
        """표창 드로잉"""
        if PantherThrowingStar.image_seq and self.animation_frame < len(PantherThrowingStar.image_seq):
            # 애니메이션 프레임 렌더링 (회전 없이)
            img = PantherThrowingStar.image_seq[self.animation_frame]
            if img:
                img.draw(draw_x, draw_y, img.w * self.scale, img.h * self.scale)
        else:
            # 디버그 렌더링 (이미지 없을 때)
            size = int(10 * self.scale)
            p2.draw_rectangle(
                draw_x - size, draw_y - size,
                draw_x + size, draw_y + size
            )

        # DEBUG: 충돌 박스 그리기
        # Left = draw_x - self.collision_width / 2
        # Right = draw_x + self.collision_width / 2
        # Bottom = draw_y - self.collision_height / 2
        # Top = draw_y + self.collision_height / 2
        # p2.draw_rectangle(Left, Bottom, Right, Top, r=0, g=255, b=0)

    def on_hit(self):
        """투사체가 타겟에 명중했을 때 호출"""
        pass

    def get_collision_box(self):
        """충돌 박스 반환"""
        return (self.collision_width, self.collision_height)

# ==================== PantherShuriken 투사체 클래스 ====================
class PantherShuriken(Projectile):
    """
    팬서 암살자 보스의 단검 투사체
    날아가는 동안은 ThrowingDagger0.png를 표시하고,
    소멸 시에는 ThrowingDagger1~4 애니메이션을 재생합니다.
    """
    flying_image = None
    dissolve_images = []

    def __init__(self, x, y, target_x, target_y, speed=400, from_player=False, damage=15, scale=1.2):
        """
        PantherShuriken 초기화

        Args:
            x, y: 시작 위치
            target_x, target_y: 목표 위치
            speed: 투사체 속도
            from_player: 플레이어가 발사했는지 여부
            damage: 투사체 피해량
            scale: 이미지 크기 배율
        """
        super().__init__(x, y, target_x, target_y, speed, from_player)

        # 투사체 속성
        self.damage = damage
        self.scale = scale
        self.collision_width = int(13 * scale)
        self.collision_height = int(41 * scale)

        # 상태 관리 변수
        self.is_dissolving = False  # 소멸 애니메이션 재생 중인지
        self.dissolve_frame = 0  # 현재 소멸 애니메이션 프레임
        self.dissolve_timer = 0.0  # 소멸 애니메이션 타이머
        self.dissolve_frame_duration = 0.08  # 각 소멸 프레임당 0.08초

        # 이미지 로드 (클래스 레벨에서 한 번만)
        if PantherShuriken.flying_image is None or not PantherShuriken.dissolve_images:
            try:
                # 비행 중 이미지 (ThrowingDagger0.png)
                flying_img_path = 'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/FX/ThrowingDagger0.png'
                PantherShuriken.flying_image = p2.load_image(flying_img_path)
                print(f'[PantherShuriken] 비행 이미지 로드 완료: {flying_img_path}')

                # 소멸 애니메이션 이미지 (ThrowingDagger1.png ~ ThrowingDagger4.png)
                PantherShuriken.dissolve_images = []
                for i in range(1, 5):  # 1, 2, 3, 4
                    dissolve_img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/FX/ThrowingDagger{i}.png'
                    PantherShuriken.dissolve_images.append(p2.load_image(dissolve_img_path))
                print(f'[PantherShuriken] 소멸 애니메이션 이미지 로드 완료: {len(PantherShuriken.dissolve_images)}개 프레임')
            except FileNotFoundError as e:
                print(f'\033[91m[PantherShuriken] 이미지 로드 실패: {e}\033[0m')

    def update(self):
        """단검 업데이트"""
        dt = framework.get_delta_time()

        # 소멸 애니메이션 중이면 애니메이션만 업데이트
        if self.is_dissolving:
            self.dissolve_timer += dt
            if self.dissolve_timer >= self.dissolve_frame_duration:
                self.dissolve_timer -= self.dissolve_frame_duration
                self.dissolve_frame += 1

                # 모든 소멸 프레임을 다 재생했으면 제거
                if self.dissolve_frame >= len(PantherShuriken.dissolve_images):
                    return False

            return True

        # 일반 비행 로직
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt

        # 화면 밖으로 나가면 소멸 애니메이션 시작
        if (self.x < -1000 or self.x > 5000 or
            self.y < -1000 or self.y > 5000):
            self.start_dissolve()

        return True

    def draw(self, draw_x, draw_y):
        """단검 드로잉"""
        # 소멸 애니메이션 중이면 소멸 이미지 그리기
        if self.is_dissolving:
            if (PantherShuriken.dissolve_images and
                self.dissolve_frame < len(PantherShuriken.dissolve_images)):
                img = PantherShuriken.dissolve_images[self.dissolve_frame]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.scale, img.h * self.scale)
        else:
            # 비행 중이면 비행 이미지 그리기
            if PantherShuriken.flying_image:
                img = PantherShuriken.flying_image
                img.draw(draw_x, draw_y, img.w * self.scale, img.h * self.scale)
            else:
                # 디버그 렌더링 (이미지 없을 때)
                size = int(10 * self.scale)
                p2.draw_rectangle(
                    draw_x - size, draw_y - size,
                    draw_x + size, draw_y + size
                )

        # DEBUG: 충돌 박스 그리기 (필요 시 주석 해제)
        # Left = draw_x - self.collision_width / 2
        # Right = draw_x + self.collision_width / 2
        # Bottom = draw_y - self.collision_height / 2
        # Top = draw_y + self.collision_height / 2
        # p2.draw_rectangle(Left, Bottom, Right, Top, r=0, g=255, b=0)

    def on_hit(self):
        """투사체가 타겟에 명중했을 때 호출 - 소멸 애니메이션 시작"""
        self.start_dissolve()

    def start_dissolve(self):
        """소멸 애니메이션 시작"""
        if not self.is_dissolving:
            self.is_dissolving = True
            self.dissolve_frame = 0
            self.dissolve_timer = 0.0

    def get_collision_box(self):
        """충돌 박스 반환"""
        # 소멸 중일 때는 충돌 판정 없음
        if self.is_dissolving:
            return (0, 0)
        return (self.collision_width, self.collision_height)

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
            