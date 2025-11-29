import pico2d as p2
import math
import random
import game_framework as framework
from ..behavior_tree import BehaviorTree, Selector, Sequence, Action, Condition, RandomSelector
from ..projectile import Projectile
from .. import image_asset_manager as iam


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
    패턴1 - 90도 방사형으로 플레이어를 향해 2단 표창 투척
    """

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
        self.shot_interval = 0.0  # 투척 간격
        self.spread_angle = 90  # 방사형 각도 (90도)
        self.projectiles_per_shot = 0  # 한 번에 발사하는 표창 개수

    def update(self):
        """패턴 1 로직 실행"""
        dt = framework.get_delta_time()

        if self.phase == 0:
            # 초기화: 돌진 방향 설정
            if self.panther.target:
                dx = self.panther.target.x - self.panther.x
                dy = self.panther.target.y - self.panther.y
                dist = math.sqrt(dx**2 + dy**2)

                if dist > 0:
                    self.dash_dx = dx / dist
                    self.dash_dy = dy / dist
                else:
                    self.dash_dx = 1
                    self.dash_dy = 0

                self.dash_speed = 800  # 돌진 속도
                self.dash_duration = 0.5  # 돌진 지속 시간
                self.timer = 0.0
                self.phase = 1
                print("[Pattern1] 돌진 시작!")

        elif self.phase == 1:
            # 돌진 중
            self.panther.x += self.dash_dx * self.dash_speed * dt
            self.panther.y += self.dash_dy * self.dash_speed * dt
            self.timer += dt

            if self.timer >= self.dash_duration:
                # 돌진 완료
                self.phase = 0
                self.panther.attack_timer = self.panther.attack_cooldown
                print("[Pattern1] 돌진 완료!")
                return BehaviorTree.SUCCESS

        return BehaviorTree.RUNNING

    def draw(self, draw_x, draw_y):
        """
        패턴 1 시각 효과 드로잉

        Args:
            draw_x, draw_y: 보스의 현재 위치 (카메라 좌표계)
        """
        # Pattern 1 Draw Logic: 돌진 공격 시각 효과
        if self.phase == 1:  # 돌진 중일 때만 표시
            # 돌진 방향을 나타내는 화살표/궤적 표시
            trail_length = 100
            end_x = draw_x - self.dash_dx * trail_length
            end_y = draw_y - self.dash_dy * trail_length

            # 돌진 궤적 라인 (빨간색)
            p2.draw_line(draw_x, draw_y, end_x, end_y)

            # 돌진 이펙트 원 (진행도에 따라 크기 변화)
            progress = self.timer / self.dash_duration
            effect_radius = 30 + progress * 20
            p2.draw_circle(draw_x, draw_y, int(effect_radius))


class AttackPattern2Action:
    """
    패턴2 - 은신 후 다른 곳에서 나타나 플레이어를 향해 강한 돌진 공격 2회
    """

    dash_img_seq = []
    dash_img_seq_count = 8
    swing_img_seq = []
    swing_img_seq_count = 10

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
        # 돌진 공격 관련 변수
        self.dash_count = 0  # 현재 돌진 횟수
        self.max_dash_count = 2  # 최대 돌진 횟수
        self.dash_dx = 0.0
        self.dash_dy = 0.0
        self.dash_speed = 0.0
        self.dash_duration = 0.0

        # 이미지 시퀀스 로드
        if not AttackPattern2Action.dash_img_seq:
            try:
                for i in range(self.dash_img_seq_count):
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_BladeAttack{i:02d}.png')
                    AttackPattern2Action.dash_img_seq.append(img)
                for i in range(self.swing_img_seq_count):
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_BladeAttack{i+8:02d}.png')
                    AttackPattern2Action.swing_img_seq.append(img)
            except FileNotFoundError as e:
                print(f'\033[91m[Pattern2] 이미지 로드 실패: {e}\033[0m')

    def update(self):
        """패턴 2 로직 실행"""
        dt = framework.get_delta_time()

        if self.phase == 0:
            # 초기화: 발사 준비
            self.shot_count = 0
            self.max_shots = 5
            self.shot_interval = 0.15  # 발사 간격
            self.timer = 0.0
            self.phase = 1
            print("[Pattern2] 연속 수리검 시작!")

        elif self.phase == 1:
            # 수리검 발사
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
                    print(f"[Pattern2] 수리검 발사 {self.shot_count + 1}/{self.max_shots}")

                self.shot_count += 1
                self.timer = 0.0

                if self.shot_count >= self.max_shots:
                    # 모든 수리검 발사 완료
                    self.phase = 0
                    self.panther.attack_timer = self.panther.attack_cooldown
                    print("[Pattern2] 연속 수리검 완료!")
                    return BehaviorTree.SUCCESS

        return BehaviorTree.RUNNING

    def draw(self, draw_x, draw_y):
        """
        패턴 2 시각 효과 드로잉

        Args:
            draw_x, draw_y: 보스의 현재 위치 (카메라 좌표계)
        """
        # Pattern 2 Draw Logic: 연속 수리검 발사 시각 효과
        if self.phase == 1:  # 발사 중일 때
            # 타겟 방향 조준선 표시
            if self.panther.target:
                p2.draw_line(draw_x, draw_y, self.panther.target.x, self.panther.target.y)

            # 발사 카운트 표시 (원형 인디케이터)
            progress = self.shot_count / self.max_shots
            indicator_radius = 20 + progress * 30
            p2.draw_circle(draw_x, draw_y + 60, int(indicator_radius))


class AttackPattern3Action:
    """
    BTActionWrapper: 패턴3 - 은신 후 다른 곳에서 나타나 플레이어를 향해 돌진 후 8방향 방사형으로 수리검 투척
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
        self.stat = PantherAssassinStats()

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

        # 공격 관련
        self.recognition_distance = 400 # 플레이어 인식 거리
        self.unrecognition_distance = 800 # 플레이어 미인식 거리
        self.attack_range = 800  # 공격 범위 (추가)
        self.attack_cooldown = 2.0  # 공격 쿨타임 (초)
        self.attack_timer = 0.0  # 현재 쿨타임 타이머

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

        try:
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
        │       ├── BTActionWrapper: 패턴1 - 90도 방사형으로 플레이어를 향해 2단 표창 투척
        │       ├── BTActionWrapper: 패턴2 - 은신 후 다른 곳에서 나타나 플레이어를 향해 강한 돌진 공격 2회
        │       ├── BTActionWrapper: 패턴3 - 은신 후 다른 곳에서 나타나 플레이어를 향해 돌 진 후 8방향 방사형으로 수리검 투척
        │       │   # 그림자 분신과 함꼐하는 패턴 4, 5, 6
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
            BTActionWrapper("Pattern1: Dash", self.pattern1_action),
            BTActionWrapper("Pattern2: Shuriken", self.pattern2_action),
            BTActionWrapper("Pattern3: Circular", self.pattern3_action),
            BTActionWrapper("Pattern4: Teleport", self.pattern4_action),
            BTActionWrapper("Pattern5: Shockwave", self.pattern5_action),
            BTActionWrapper("Pattern6: Shadow Clone", self.pattern6_action)
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
        대기 또는 순찰 행동
        타겟을 향해 천천히 이동
        """
        if self.target is None:
            return BehaviorTree.SUCCESS

        dt = framework.get_delta_time()

        # 타겟을 향해 이동
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance > 50:  # 최소 거리 유지
            move_x = (dx / distance) * self.stat.get('move_speed') * dt
            move_y = (dy / distance) * self.stat.get('move_speed') * dt
            self.x += move_x
            self.y += move_y

        return BehaviorTree.SUCCESS

    # ==================== 업데이트 & 렌더링 ====================

    def update(self):
        """매 프레임 업데이트"""
        dt = framework.get_delta_time()

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

        # 행동 트리 실행
        if self.behavior_tree:
            self.behavior_tree.run()



    def draw(self, draw_x, draw_y):
        """몬스터 렌더링"""
        """
        일반적 Hit 일땐 대미지만 적용, (hit 판정의 이미지 시퀀스 x )
        Death 상태 일땐 현재 이미지 시퀀스를 Death 이미지로 교체 후 재생
        1. Hit 판정시 이미지 시퀀스 교체 없이 대미지만 적용
        2. Death 판정시 이미지 시퀀스를 Death 이미지로 교체
        3. Death 이미지 시퀀스 재생 후 3초 후 몬스터 제거
        
        TODO: 1. 몬스터 사망 후 아이템 드랍 구현
        """
        # 몬스터 본체 드로잉
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
        if self.current_action_instance is not None:
            # 패턴 인스턴스가 draw 메서드를 가지고 있는지 확인 후 호출
            if hasattr(self.current_action_instance, 'draw'):
                self.current_action_instance.draw(draw_x, draw_y)

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
        current_health = self.stat.get('health')
        self.stat.set_base('health', max(0, current_health - damage))
        print(f"[PantherAssassin] 피해 {damage}, 남은 HP: {self.stat.get('health')}/{self.stat.get('max_health')}")

        if self.stat.get('health') <= 0:
            print("[PantherAssassin] 처치됨!")
            return True  # 사망
        return False

    def set_target(self, target):
        """타겟 설정 (주로 플레이어)"""
        self.target = target
