import pico2d as p2
import math
import random
import game_framework as framework
from ..behavior_tree import BehaviorTree, Selector, Sequence, Action, Condition, RandomSelector
from ..projectile import Projectile
from .. import image_asset_manager as iam
from ..damage_indicator import DamageIndicator
from ..ui_overlay import MonsterHealthBar

# ==================== 공격 패턴 클래스 참조 ====================
from .Boss_Logic.panther_assassin_1pattern import AttackPattern1Action
from .Boss_Logic.panther_assassin_2pattern import AttackPattern2Action
from .Boss_Logic.panther_assassin_3pattern import AttackPattern3Action
from .Boss_Logic.panther_assassin_4pattern import AttackPattern4Action
from .Boss_Logic.panther_assassin_5pattern import AttackPattern5Action
from .Boss_Logic.panther_assassin_6pattern import AttackPattern6Action

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
                    # print(f'[PantherAssassin] 이미지 로드 성공: PantherAssassin_Idle{i:02d}.png')

                except FileNotFoundError as e:
                    print(f'\033[91m[PantherAssassin] 이미지 로드 실패: {e}\033[0m')

            # Death 애니메이션 로드 (0~15)
            self.death_images = []

            for i in range(3):
                try:
                    Airborne_img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Airborne{i:02d}.png'
                    Airborne_img = p2.load_image(Airborne_img_path)
                    self.death_images.append(Airborne_img)
                    # print(f'[PantherAssassin] 사망 애니메이션 로드 성공: PantherAssassin_Knockback{i:02d}.png')
                except FileNotFoundError as e:
                    print(f'\033[91m[PantherAssassin] 사망 애니메이션 로드 실패: {e}\033[0m')

            for i in range(self.death_animation_frames):
                try:
                    death_img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_TrueDie{i:02d}.png'
                    death_img = p2.load_image(death_img_path)
                    self.death_images.append(death_img)
                    # print(f'[PantherAssassin] 사망 애니메이션 로드 성공: PantherAssassin_TrueDie{i:02d}.png')
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
            BTActionWrapper("Pattern3: ComboAttack", self.pattern3_action),
            BTActionWrapper("Pattern4: Teleport", self.pattern4_action),
            BTActionWrapper("Pattern5: Whirlwind", self.pattern5_action),
            BTActionWrapper("Pattern6: Shadow", self.pattern6_action)
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

        # 패턴 5 실행 중일 때 특별 처리: Phase 1(분신 이동), Phase 6(분신 소멸)에서는 IDLE 모션 표시
        should_show_idle = False
        if (has_active_pattern and
            self.current_action_instance == self.pattern5_action and
            hasattr(self.current_action_instance, 'phase')):
            # Phase 1: 분신 이동 중 - IDLE 모션 표시
            # Phase 6: 분신 소멸 중 - IDLE 모션 표시
            if self.current_action_instance.phase in [1, 6]:
                should_show_idle = True

        # 패턴 6 실행 중일 때 특별 처리: Phase 1(분신 이동), Phase 4(분신 소멸)에서는 IDLE 모션 표시
        if (has_active_pattern and
            self.current_action_instance == self.pattern6_action and
            hasattr(self.current_action_instance, 'phase')):
            # Phase 1: 분신 이동 중 - IDLE 모션 표시
            # Phase 4: 분신 소멸 중 - IDLE 모션 표시
            if self.current_action_instance.phase in [1, 4]:
                should_show_idle = True

        # 패턴 4 실행 중일 때는 패턴의 draw() 메서드로 본체 그리기
        if (has_active_pattern and
            self.current_action_instance == self.pattern4_action and
            hasattr(self.current_action_instance, 'draw')):
            # 패턴 4의 draw() 메서드 호출 (은신/해제 애니메이션 처리)
            self.current_action_instance.draw(draw_x, draw_y)

        # 패턴 5의 특정 phase 또는 패턴 공격 중이 아닐 때 IDLE 모션 드로잉
        elif not has_active_pattern or should_show_idle:
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
        # 단, 패턴 5의 Phase 1, 6은 제외 (IDLE 모션만 표시)
        if self.current_action_instance is not None and not should_show_idle:
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
        self.health_bar.draw(draw_x + 15, draw_y - 70)

        # DEBUG : 충돌 박스 및 플레이어 인식 범위 그리기
        # 충돌 박스 : 카메라 좌표계로 변환 후 그리기
        # Left, Bottom, Right, Top = self.get_bb()
        # Left -= self.x - draw_x
        # Right -= self.x - draw_x
        # Bottom -= self.y - draw_y
        # Top -= self.y - draw_y
        # p2.draw_rectangle(Left, Bottom, Right, Top, r=255, g=0, b=0)
        #
        # # 공격 범위
        # radius = self.recognition_distance
        # p2.draw_circle(draw_x, draw_y, int(radius), r=255, g=255, b=0)
        #
        # # 타겟 놓치는 거리
        # radius = self.unrecognition_distance
        # p2.draw_circle(draw_x, draw_y, int(radius), r=0, g=255, b=255)
        #
        # 분신 드로잉 (디버그용)
        # if self.clone_images:
        #     offset = 200
        #     self.clone_images[self.frame].draw(draw_x - offset, draw_y,
        #                                        self.clone_images[self.frame].w * self.scale_factor,
        #                                        self.clone_images[self.frame].h * self.scale_factor)


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

            # 아이템 드롭 처리
            try:
                from ..items import drop_item, Crown
                if self.world:
                    drop_item(self.world, Crown, 1, self.x, self.y, drop_chance=1.0)
            except Exception as e:
                print(f"\033[91m[PantherAssassin Death] 아이템 드롭 중 오류: {e}\033[0m")

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
        self.collision_height = int(41 * scale) // 2

        # 회전 각도 계산 (원본 이미지가 위쪽을 바라봄, +y 방향 기준)
        # math.atan2를 사용하여 방향 벡터로부터 각도 계산
        import math
        self.rotation_angle = math.atan2(self.dy, self.dx) + math.radians(-90) # 라디안 단위

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
        """단검 드로잉 (회전 적용)"""
        # 소멸 애니메이션 중이면 소멸 이미지 그리기 (회전 적용)
        if self.is_dissolving:
            if (PantherShuriken.dissolve_images and
                self.dissolve_frame < len(PantherShuriken.dissolve_images)):
                img = PantherShuriken.dissolve_images[self.dissolve_frame]
                if img:
                    # 회전을 적용하여 그리기
                    img.rotate_draw(self.rotation_angle, draw_x, draw_y, img.w * self.scale, img.h * self.scale)
        else:
            # 비행 중이면 비행 이미지 그리기 (회전 적용)
            if PantherShuriken.flying_image:
                img = PantherShuriken.flying_image
                # 회전을 적용하여 그리기
                img.rotate_draw(self.rotation_angle, draw_x, draw_y, img.w * self.scale, img.h * self.scale)
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


class Clone:
    """
    분신 객체 - 시각 효과 전용

    주의: play_mode의 entities 레이어에서 정상 작동하려면
          일부 더미 속성/메서드가 필요합니다.
    """
    def __init__(self, start_x, start_y, target_x, target_y, images, scale_factor):
        """
        Args:
            start_x, start_y: 시작 위치 (본체 위치)
            target_x, target_y: 목표 위치 (이동할 위치)
            images: 애니메이션에 사용할 이미지 딕셔너리 {'throw_1st': [...], 'throw_2nd': [...], 'move': [...], 'die': [...]}
            scale_factor: 본체의 스케일 팩터
        """
        print(f"[Clone.__init__] 분신 생성 시작 - 시작: ({start_x:.0f}, {start_y:.0f}), 목표: ({target_x:.0f}, {target_y:.0f})")

        self.start_x = start_x
        self.start_y = start_y
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.images = images
        self.scale_factor = scale_factor  # 본체와 동일한 스케일 사용

        # 이미지 딕셔너리 검증
        print(f"[Clone.__init__] 이미지 딕셔너리 키: {list(images.keys())}")
        for key, img_list in images.items():
            print(f"[Clone.__init__] {key}: {len(img_list)}개 이미지")
            if len(img_list) == 0:
                print(f"[Clone.__init__] 경고: {key} 이미지 리스트가 비어있음!")

        # 이동 관련
        self.move_duration = 1.5  # 이동 시간 (1.5초로 변경)
        self.move_timer = 0.0
        self.is_moving = True

        # 잔상 효과
        self.afterimage_alpha = 1.0  # 시작 위치의 잔상 투명도
        self.afterimage_fade_duration = 0.5  # 잔상 사라지는 시간

        # 애니메이션
        self.current_animation = 'move'
        self.frame = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.1  # 프레임당 시간

        # 사라지는 애니메이션 관련
        self.is_dying = False  # 사라지는 애니메이션 재생 중 플래그
        self.die_frame = 0  # Die 애니메이션 현재 프레임
        self.die_frame_duration = 0.08  # Die 애니메이션 프레임당 시간
        self.die_animation_frames = 11  # Die 애니메이션 프레임 수 (0~10)

        # 제거 플래그 (entities에서 자동 제거되도록)
        self.to_be_removed = False

        print(f"[Clone.__init__] 분신 생성 완료!")

        # play_mode 호환성을 위한 더미 속성 추가
        self.mark_for_removal = False  # play_mode의 제거 플래그
        self.hp = 1  # 더미 체력 (충돌 검사에서 필요할 수 있음)
        self.is_dead = False  # 더미 사망 플래그

        # 디버깅: 생성 직후 첫 업데이트 강제 호출 테스트
        print(f"[Clone.__init__] 테스트: 생성 직후 update() 호출 가능 여부 확인")
        try:
            # update()를 호출하지는 않고, 대신 필수 속성들이 모두 있는지만 확인
            assert hasattr(self, 'x'), "x 속성 누락!"
            assert hasattr(self, 'y'), "y 속성 누락!"
            assert hasattr(self, 'images'), "images 속성 누락!"
            assert hasattr(self, 'update'), "update 메서드 누락!"
            assert hasattr(self, 'draw'), "draw 메서드 누락!"
            print(f"[Clone.__init__] ✓ 필수 속성/메서드 검증 완료")
        except AssertionError as e:
            print(f"\033[91m[Clone.__init__] ✗ 속성 검증 실패: {e}\033[0m")

    def start_dying(self):
        """
        분신 사라지는 애니메이션 시작
        외부에서 이 메서드를 호출하여 분신을 제거 시작
        """
        if not self.is_dying:
            print(f"[Clone.start_dying] 분신 사라지는 애니메이션 시작 - 위치: ({self.x:.0f}, {self.y:.0f})")
            self.is_dying = True
            self.die_frame = 0
            self.frame_timer = 0.0
            self.current_animation = 'die'

    def update(self):
        """분신 업데이트 (play_mode에서 파라미터 없이 호출됨)"""
        try:
            # 첫 업데이트에만 로그 출력
            if not hasattr(self, '_update_logged'):
                print(f"[Clone.update] 첫 업데이트 - 위치: ({self.x:.0f}, {self.y:.0f}), is_moving: {self.is_moving}")
                self._update_logged = True

            # dt는 내부에서 가져오기
            dt = framework.get_delta_time()

            # 사라지는 애니메이션 재생 중
            if self.is_dying:
                self.frame_timer += dt
                if self.frame_timer >= self.die_frame_duration:
                    self.frame_timer = 0.0
                    self.die_frame += 1
                    
                    # Die 애니메이션 완료 시 제거 플래그 설정
                    if self.die_frame >= self.die_animation_frames:
                        print(f"[Clone.update] Die 애니메이션 완료 - 제거 플래그 설정")
                        self.mark_for_removal = True
                        self.to_be_removed = True
                        return True  # 제거 대기
                
                return True  # 애니메이션 재생 중

            # 일반 동작 (이동 및 투척 애니메이션)
            if self.is_moving:
                self.move_timer += dt
                progress = min(1.0, self.move_timer / self.move_duration)

                # 부드러운 이동 (easeOutCubic)
                ease_progress = 1 - pow(1 - progress, 3)
                self.x = self.start_x + (self.target_x - self.start_x) * ease_progress
                self.y = self.start_y + (self.target_y - self.start_y) * ease_progress

                # 잔상 투명도 감소
                self.afterimage_alpha = max(0.0, 1.0 - (self.move_timer / self.afterimage_fade_duration))

                if progress >= 1.0:
                    self.is_moving = False
                    self.current_animation = 'throw_1st'  # 이동 완료 후 투척 준비
                    self.frame = 0
                    print(f"[Clone.update] 이동 완료! 위치: ({self.x:.0f}, {self.y:.0f})")

            # 프레임 애니메이션
            self.frame_timer += dt
            if self.frame_timer >= self.frame_duration:
                self.frame_timer = 0.0

                # 현재 애니메이션에 따라 프레임 업데이트
                if self.current_animation in self.images:
                    img_list = self.images[self.current_animation]

                    if self.current_animation == 'move':
                        # Move 애니메이션은 반복 재생
                        if len(img_list) > 0:
                            self.frame = (self.frame + 1) % len(img_list)
                    elif self.current_animation in ['whirlwind']:
                        # Whirlwind 애니메이션은 반복 재생
                        if len(img_list) > 0:
                            self.frame = (self.frame + 1) % len(img_list)
                    elif self.current_animation in ['throw_1st', 'throw_2nd', 'withdraw']:
                        # 투척 및 Withdraw 애니메이션은 한 번만 재생
                        if len(img_list) > 0 and self.frame < len(img_list) - 1:
                            self.frame += 1
                else:
                    print(f"[Clone.update] 경고: {self.current_animation} 이미지가 없음!")

            # update 메서드는 True를 반환해야 entities에서 유지됨
            return True

        except Exception as e:
            print(f"\033[91m[Clone.update] 오류 발생: {e}\033[0m")
            import traceback
            traceback.print_exc()
            return True  # 오류가 나도 객체는 유지

    def switch_animation(self, animation_type):
        """
        애니메이션 변경
        Args:
            animation_type: 'move', 'whirlwind', 'withdraw', 'throw_1st', 'throw_2nd', 'die'
        """
        try:
            print(f"[Clone.switch_animation] {self.current_animation} -> {animation_type}")
            self.current_animation = animation_type
            self.frame = 0
            self.frame_timer = 0.0
        except Exception as e:
            print(f"\033[91m[Clone.switch_animation] 오류: {e}\033[0m")

    def switch_throw_animation(self, throw_type):
        """투척 애니메이션 변경 (1st <-> 2nd) - 하위 호환성 유지"""
        self.switch_animation(throw_type)

    def draw(self, draw_x, draw_y):
        """
        분신 그리기
        Args:
            draw_x, draw_y: 카메라가 적용된 화면 좌표
        """
        try:
            # 디버그: 첫 프레임에만 로그 출력
            if not hasattr(self, '_draw_logged'):
                print(f"[Clone.draw] 첫 그리기 - 화면좌표: ({draw_x:.0f}, {draw_y:.0f}), 월드좌표: ({self.x:.0f}, {self.y:.0f})")
                print(f"[Clone.draw] 애니메이션: {self.current_animation}, 프레임: {self.frame}")
                print(f"[Clone.draw] 이미지 개수: {len(self.images.get(self.current_animation, []))}")
                self._draw_logged = True

            # Die 애니메이션 재생 중
            if self.is_dying and 'die' in self.images:
                die_img_list = self.images['die']
                if len(die_img_list) > 0 and 0 <= self.die_frame < len(die_img_list):
                    die_img = die_img_list[self.die_frame]
                    die_img.draw(
                        draw_x, draw_y,
                        die_img.w * self.scale_factor,
                        die_img.h * self.scale_factor
                    )
                return  # Die 애니메이션 중에는 다른 것 그리지 않음

            # 일반 애니메이션 (move, whirlwind, withdraw, throw_1st, throw_2nd)
            if self.current_animation in self.images:
                img_list = self.images[self.current_animation]
                if len(img_list) == 0:
                    print(f"[Clone.draw] 경고: {self.current_animation} 이미지 리스트가 비어있음!")
                    return

                if 0 <= self.frame < len(img_list):
                    current_img = img_list[self.frame]

                    # 현재 위치에 분신 그리기 (카메라 좌표 이미 적용됨)
                    current_img.draw(
                        draw_x, draw_y,
                        current_img.w * self.scale_factor,
                        current_img.h * self.scale_factor
                    )

                    # 이동 중일 때 잔상 효과 (시작 위치)
                    if self.is_moving and self.afterimage_alpha > 0.0:
                        # 잔상 위치도 카메라 좌표로 변환 필요
                        # play_mode의 camera를 통해 변환
                        from game_logic import play_mode
                        if play_mode.camera is not None:
                            afterimage_draw_x, afterimage_draw_y = play_mode.camera.apply(self.start_x, self.start_y)
                        else:
                            afterimage_draw_x, afterimage_draw_y = self.start_x, self.start_y

                        current_img.opacify(self.afterimage_alpha)
                        current_img.draw(
                            afterimage_draw_x, afterimage_draw_y,
                            current_img.w * self.scale_factor,
                            current_img.h * self.scale_factor
                        )
                        current_img.opacify(1.0)  # 원래대로 복구
                else:
                    print(f"[Clone.draw] 경고: 프레임 인덱스 범위 초과 - frame={self.frame}, max={len(img_list)-1}")
            else:
                print(f"[Clone.draw] 경고: {self.current_animation} 키가 이미지 딕셔너리에 없음!")

        except Exception as e:
            print(f"\033[91m[Clone.draw] 오류 발생: {e}\033[0m")
            import traceback
            traceback.print_exc()
