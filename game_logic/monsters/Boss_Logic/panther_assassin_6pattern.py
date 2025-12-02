import pico2d as p2
import random
import math
import game_framework as framework
from ...behavior_tree import BehaviorTree


class AttackPattern6Action:
    """
    panther_assassin.py의 보스 개체(PantherAssassin)의 공격패턴 6 구현 클래스
    패턴6 - 분신 2체 랜덤 위치에 소환후 본체, 분신 2체 번갈아 가며 플레이어를 향해 수리검 5개 방사형으로 3회씩 투척
    자세한 설명:
    1. 플레이어 주변 랜덤 위치에 분신 2체 소환 (분신 소환은 panther_assassin_4pattern.py의 패턴4와 동일)
    2. 본체 → 분신1 → 분신2 → 본체 → ... 순서로 번갈아가며 투척 (총 3회 사이클, 9회 투척)
         - 각 투척당 5개 수리검을 방사형으로 발사 (총 45개)
         - 수리검은 플레이어를 향해 발사되며, 약간의 퍼짐(스프레드) 효과 적용 ±15, 30도
    3. 투척 순서: Ready 모션(준비) → Attack 모션(투척) → 대기 → 다음 투척자
    4. 모든 투척이 끝나면 분신 소멸
    5. 패턴 종료

    기본 모션 경로 : 'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character'
    투척 준비 모션: PantherAssassin_Throw_All_Ready{i:02d}.png 0 ~ 4
    투척 모션: PantherAssassin_Throw_All_Attack{i:02d}.png 0 ~ 9

    주의:
        - 분신 소환 코드는 panther_assassin_4pattern.py의 AttackPattern4Action과 유사
        - 분신 이동 중(Phase 1): 본체는 IDLE 모션
        - 투척 중(Phase 2~3): 본체와 분신 모두 Ready → Attack 모션 동기화
        - 분신 소멸 중(Phase 4): 본체는 IDLE 모션
        - 각 개체가 한 번씩 투척하는 것을 1사이클로 계산, 총 3사이클 반복

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
        self.clone_count = 2  # 분신 개수 (2체)
        self.clones = []  # Clone 객체 리스트
        self.clones_spawned = False  # 분신 소환 완료 플래그

        # 수리검 투척 관련 변수 (사이클 기반으로 재설계)
        self.total_shooters = 3  # 본체(1) + 분신(2) = 총 3명
        self.current_shooter = 0  # 현재 투척하는 개체 (0: 본체, 1: 분신1, 2: 분신2)
        self.current_cycle = 0  # 현재 사이클 (0, 1, 2 - 총 3사이클)
        self.max_cycles = 3  # 최대 사이클 수 (3회 반복)
        self.projectiles_per_shot = 5  # 한 번에 발사하는 수리검 개수 (5개)
        self.spread_angles = [-30, -15, 0, 15, 30]  # 방사형 각도 (플레이어 방향 기준 ±15, 30도)
        self.projectile_speed = 600  # 수리검 속도

        # 애니메이션 관련 변수
        self.ready_frame = 0  # Throw_All_Ready 애니메이션 프레임
        self.ready_frame_timer = 0.0
        self.ready_frame_speed = 12.0  # 초당 프레임 수
        self.ready_total_frames = 5  # 0~4 (총 5프레임)

        self.attack_frame = 0  # Throw_All_Attack 애니메이션 프레임
        self.attack_frame_timer = 0.0
        self.attack_frame_speed = 15.0  # 초당 프레임 수
        self.attack_total_frames = 10  # 0~9 (총 10프레임)
        self.attack_throw_frame = 0  # 5번 프레임에서 수리검 발사
        self.has_thrown_in_attack = False  # 현재 Attack 애니메이션에서 이미 투척했는지

        self.shot_interval = 0.1  # 각 투척 후 대기 시간 (다음 투척자로 전환)

        # 이미지 로드
        self._load_images()

    def _load_images(self):
        """애니메이션 이미지 로드"""
        try:
            from game_logic import image_asset_manager as iam

            base_path = "resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character"
            print(f"[Pattern6._load_images] 이미지 로드 시작 - 경로: {base_path}")

            # 원본 이미지 로드 및 분신용 어두운 이미지 생성
            self.original_images = {
                'ready': [],  # Throw_All_Ready 모션
                'attack': [],  # Throw_All_Attack 모션
                'move': [],
                'die': []  # 분신 사라지는 애니메이션용
            }

            self.clone_images = {
                'ready': [],
                'attack': [],
                'move': [],
                'die': []
            }

            # Throw_All_Ready 모션 (0~4)
            for i in range(5):
                try:
                    img_path = f"{base_path}/PantherAssassin_Throw_All_Ready{i:02d}.png"
                    img = p2.load_image(img_path)
                    self.original_images['ready'].append(img)

                    # 분신용 어두운 버전 생성
                    iam.register_image_path(img, img_path)
                    clone_img = iam.make_dark(img, darkness=0.25)
                    self.clone_images['ready'].append(clone_img)
                except Exception as e:
                    print(f"\033[91m[Pattern6._load_images] Throw_All_Ready{i:02d}.png 로드 실패: {e}\033[0m")

            # Throw_All_Attack 모션 (0~9)
            for i in range(10):
                try:
                    img_path = f"{base_path}/PantherAssassin_Throw_All_Attack{i:02d}.png"
                    img = p2.load_image(img_path)
                    self.original_images['attack'].append(img)

                    # 분신용 어두운 버전 생성
                    iam.register_image_path(img, img_path)
                    clone_img = iam.make_dark(img, darkness=0.25)
                    self.clone_images['attack'].append(clone_img)
                except Exception as e:
                    print(f"\033[91m[Pattern6._load_images] Throw_All_Attack{i:02d}.png 로드 실패: {e}\033[0m")

            # Move 모션 (0~7)
            for i in range(8):
                try:
                    img_path = f"{base_path}/PantherAssassin_Move{i:02d}.png"
                    img = p2.load_image(img_path)
                    self.original_images['move'].append(img)

                    # 분신용 어두운 버전 생성
                    iam.register_image_path(img, img_path)
                    clone_img = iam.make_dark(img, darkness=0.25)
                    self.clone_images['move'].append(clone_img)
                except Exception as e:
                    print(f"\033[91m[Pattern6._load_images] Move{i:02d}.png 로드 실패: {e}\033[0m")

            # Die 모션 (0~10) - 분신 사라지는 애니메이션용
            for i in range(11):
                try:
                    img_path = f"{base_path}/PantherAssassin_Die{i:02d}.png"
                    img = p2.load_image(img_path)
                    self.original_images['die'].append(img)

                    # 분신용 Die 애니메이션
                    iam.register_image_path(img, img_path)
                    clone_die_img = iam.make_dark(img, darkness=0.25)
                    self.clone_images['die'].append(clone_die_img)
                except Exception as e:
                    print(f"\033[91m[Pattern6._load_images] Die{i:02d}.png 로드 실패: {e}\033[0m")

            print(f"[Pattern6._load_images] 원본 이미지 로드 완료 - "
                  f"Ready: {len(self.original_images['ready'])}개, "
                  f"Attack: {len(self.original_images['attack'])}개, "
                  f"Move: {len(self.original_images['move'])}개, "
                  f"Die: {len(self.original_images['die'])}개")

            print(f"[Pattern6._load_images] 분신 이미지 생성 완료 - "
                  f"Ready: {len(self.clone_images['ready'])}개, "
                  f"Attack: {len(self.clone_images['attack'])}개, "
                  f"Move: {len(self.clone_images['move'])}개, "
                  f"Die: {len(self.clone_images['die'])}개")

        except Exception as e:
            print(f"\033[91m[Pattern6._load_images] 전체 로드 과정 오류: {e}\033[0m")
            import traceback
            traceback.print_exc()

    def update(self):
        """패턴 6 로직 실행"""
        try:
            dt = framework.get_delta_time()

            if self.phase == 0:
                # Phase 0: 초기화 및 분신 소환 시작
                self.timer = 0.0
                self.current_shooter = 0
                self.current_cycle = 0
                self.ready_frame = 0
                self.ready_frame_timer = 0.0
                self.attack_frame = 0
                self.attack_frame_timer = 0.0
                self.has_thrown_in_attack = False
                self.clones = []
                self.clones_spawned = False

                print("[Pattern6] 패턴 시작 - 분신 소환 시작!")
                self.phase = 1

            elif self.phase == 1:
                # Phase 1: 분신 소환 (본체 위치에 생성 후 랜덤 위치로 이동)
                # 이 단계에서는 본체 IDLE 모션 표시 (panther_assassin.py의 draw에서 처리)
                if not self.clones_spawned:
                    try:
                        print(f"[Pattern6] 분신 소환 - 본체 위치: ({self.panther.x:.0f}, {self.panther.y:.0f})")

                        # 모든 분신을 한 번에 생성
                        for i in range(self.clone_count):
                            # 각 분신마다 랜덤 위치 계산
                            angle = random.uniform(0, 360)
                            rad = math.radians(angle)
                            distance = random.uniform(200, 300)  # 본체로부터 거리

                            target_x = self.panther.x + math.cos(rad) * distance
                            target_y = self.panther.y + math.sin(rad) * distance

                            # 분신 생성 (본체 위치에서 시작)
                            from ..panther_assassin import Clone
                            clone = Clone(
                                self.panther.x, self.panther.y,
                                target_x, target_y,
                                self.clone_images,
                                self.panther.scale_factor
                            )
                            self.clones.append(clone)

                            # effects_front 레이어에 추가
                            if self.panther.world and 'effects_front' in self.panther.world:
                                self.panther.world['effects_front'].append(clone)
                                print(f"[Pattern6] 분신 {i+1}/{self.clone_count} 소환: ({target_x:.0f}, {target_y:.0f}) - effects_front 레이어에 추가됨")

                        self.clones_spawned = True
                        print(f"[Pattern6] 모든 분신 소환 완료! 총 {len(self.clones)}체")

                    except Exception as e:
                        print(f"\033[91m[Pattern6] 분신 소환 중 오류: {e}\033[0m")
                        import traceback
                        traceback.print_exc()

                # 모든 분신의 이동 완료 대기
                if self.clones_spawned and len(self.clones) == self.clone_count:
                    all_moved = all(not clone.is_moving for clone in self.clones)

                    if all_moved:
                        # Phase 2로 전환 (투척 준비)
                        self.timer = 0.0
                        self.ready_frame = 0
                        self.ready_frame_timer = 0.0

                        # 분신들을 Ready 애니메이션으로 전환
                        for clone in self.clones:
                            clone.switch_animation('ready')

                        self.phase = 2
                        print(f"[Pattern6] 분신 이동 완료! 투척 준비 시작 - Cycle {self.current_cycle + 1}/{self.max_cycles}, Shooter {self.current_shooter}")

            elif self.phase == 2:
                # Phase 2: Throw_All_Ready 애니메이션 재생 (본체와 분신 모두 동기화)
                self.ready_frame_timer += dt

                if self.ready_frame_timer >= 1.0 / self.ready_frame_speed:
                    self.ready_frame_timer = 0.0
                    self.ready_frame += 1

                    # Ready 애니메이션 완료 (0~4, 총 5프레임)
                    if self.ready_frame >= self.ready_total_frames:
                        # Attack 애니메이션으로 전환
                        self.attack_frame = 0
                        self.attack_frame_timer = 0.0
                        self.has_thrown_in_attack = False

                        # 분신들도 Attack 애니메이션으로 전환
                        for clone in self.clones:
                            clone.switch_animation('attack')

                        self.phase = 3
                        print(f"[Pattern6] Ready 완료, Attack 시작 - Cycle {self.current_cycle + 1}/{self.max_cycles}, Shooter {self.current_shooter}")

            elif self.phase == 3:
                # Phase 3: Throw_All_Attack 애니메이션 재생 및 수리검 투척
                self.attack_frame_timer += dt

                if self.attack_frame_timer >= 1.0 / self.attack_frame_speed:
                    self.attack_frame_timer = 0.0

                    # 프레임 5에 도달하면 수리검 발사 (한 번만)
                    if self.attack_frame == self.attack_throw_frame and not self.has_thrown_in_attack:
                        self._shoot_spread_shurikens()
                        self.has_thrown_in_attack = True
                        print(f"[Pattern6] 투척 실행! Cycle {self.current_cycle + 1}/{self.max_cycles}, Shooter {self.current_shooter}")

                    self.attack_frame += 1

                    # Attack 애니메이션 완료 (0~9, 총 10프레임)
                    if self.attack_frame >= self.attack_total_frames:
                        # 다음 투척자로 전환
                        self.current_shooter += 1

                        # 한 사이클 완료 체크 (본체 → 분신1 → 분신2 순서)
                        if self.current_shooter >= self.total_shooters:
                            self.current_shooter = 0
                            self.current_cycle += 1
                            print(f"[Pattern6] 사이클 {self.current_cycle}/{self.max_cycles} 완료!")

                            # 모든 사이클 완료 체크
                            if self.current_cycle >= self.max_cycles:
                                # 패턴 종료 - 분신 소멸
                                self.phase = 4
                                print("[Pattern6] 모든 사이클 완료! 분신 소멸 시작")
                                return BehaviorTree.RUNNING

                        # 다음 투척 대기
                        self.timer = 0.0
                        self.phase = 5
                        print(f"[Pattern6] 다음 투척자 대기 - Cycle {self.current_cycle + 1}/{self.max_cycles}, Next Shooter {self.current_shooter}")

            elif self.phase == 4:
                # Phase 4: 패턴 종료 정리 - 분신 소멸
                # 이 단계에서는 본체 IDLE 모션 표시 (panther_assassin.py의 draw에서 처리)

                # 분신에게 사라지는 애니메이션 시작 명령
                for clone in self.clones:
                    clone.start_dying()
                    print(f"[Pattern6] 분신 Die 애니메이션 시작 - 위치: ({clone.x:.0f}, {clone.y:.0f})")

                # 분신은 자동으로 애니메이션 후 제거되므로 여기서는 리스트만 비움
                self.clones = []

                # 패턴 종료
                self.phase = 0
                if hasattr(self.panther, 'attack_timer') and hasattr(self.panther, 'attack_cooldown'):
                    self.panther.attack_timer = self.panther.attack_cooldown
                print("[Pattern6] 패턴 종료!")
                return BehaviorTree.SUCCESS

            elif self.phase == 5:
                # Phase 5: 다음 투척자로 전환 대기 (대기 모션)
                self.timer += dt

                if self.timer >= self.shot_interval:
                    # 다음 투척 시작 - Ready 애니메이션으로 전환
                    self.ready_frame = 0
                    self.ready_frame_timer = 0.0

                    # 분신들도 Ready 애니메이션으로 전환
                    for clone in self.clones:
                        clone.switch_animation('ready')

                    self.phase = 2
                    print(f"[Pattern6] 대기 완료, Ready 시작 - Cycle {self.current_cycle + 1}/{self.max_cycles}, Shooter {self.current_shooter}")

            return BehaviorTree.RUNNING

        except Exception as e:
            print(f"\033[91m[Pattern6.update] 전체 업데이트 오류 (phase={self.phase}): {e}\033[0m")
            import traceback
            traceback.print_exc()
            return BehaviorTree.RUNNING

    def _shoot_spread_shurikens(self):
        """
        현재 투척자(본체 또는 분신)에서 플레이어를 향해 수리검 5개를 방사형으로 발사

        수리검은 플레이어 방향을 기준으로 ±15, 30도 각도로 퍼져서 발사됩니다.
        """
        if not self.panther.target or not self.panther.world:
            return

        try:
            # 투척자 위치 결정 (0: 본체, 1~2: 분신)
            if self.current_shooter == 0:
                shooter_x = self.panther.x
                shooter_y = self.panther.y
            elif 1 <= self.current_shooter <= len(self.clones):
                clone = self.clones[self.current_shooter - 1]
                shooter_x = clone.x
                shooter_y = clone.y
            else:
                print(f"\033[91m[Pattern6._shoot_spread_shurikens] 잘못된 shooter 인덱스: {self.current_shooter}\033[0m")
                return

            # 플레이어를 향한 기본 각도 계산
            dx = self.panther.target.x - shooter_x
            dy = self.panther.target.y - shooter_y
            base_angle = math.degrees(math.atan2(dy, dx))

            # 각 방사형 각도로 수리검 발사
            for spread_angle in self.spread_angles:
                # 최종 발사 각도 계산
                final_angle = base_angle + spread_angle
                rad = math.radians(final_angle)

                # 목표 위치 계산 (충분히 먼 거리)
                target_distance = 2000
                target_x = shooter_x + math.cos(rad) * target_distance
                target_y = shooter_y + math.sin(rad) * target_distance

                # 수리검 생성
                from ..panther_assassin import PantherShuriken
                shuriken = PantherShuriken(
                    shooter_x, shooter_y,
                    target_x, target_y,
                    speed=self.projectile_speed,
                    from_player=False,
                    damage=20,
                    scale=2.5
                )

                # world의 effects_front 레이어에 추가
                self.panther.world['effects_front'].append(shuriken)

            print(f"[Pattern6._shoot_spread_shurikens] 수리검 {self.projectiles_per_shot}개 발사 완료 - "
                  f"Cycle {self.current_cycle + 1}/{self.max_cycles}, Shooter {self.current_shooter}, 위치: ({shooter_x:.0f}, {shooter_y:.0f})")

        except Exception as e:
            print(f"\033[91m[Pattern6._shoot_spread_shurikens] 오류: {e}\033[0m")
            import traceback
            traceback.print_exc()

    def draw(self, draw_x, draw_y):
        """
        패턴 6 전용 그리기 메서드

        본체의 투척 애니메이션을 그립니다.
        - Phase 1: 본체는 IDLE 모션 (분신 이동 대기, panther_assassin.py에서 처리)
        - Phase 2: Throw_All_Ready 애니메이션
        - Phase 3, 5: Throw_All_Attack 애니메이션
        - Phase 4: 본체는 IDLE 모션 (분신 소멸 대기, panther_assassin.py에서 처리)
        """
        try:
            # Phase 2: Throw_All_Ready 애니메이션 재생
            if self.phase == 2 and len(self.original_images['ready']) > 0:
                if 0 <= self.ready_frame < len(self.original_images['ready']):
                    img = self.original_images['ready'][self.ready_frame]
                    img.draw(
                        draw_x, draw_y,
                        img.w * self.panther.scale_factor,
                        img.h * self.panther.scale_factor
                    )

            # Phase 3, 5: Throw_All_Attack 애니메이션 재생
            elif self.phase in [3, 5] and len(self.original_images['attack']) > 0:
                if 0 <= self.attack_frame < len(self.original_images['attack']):
                    img = self.original_images['attack'][self.attack_frame]
                    img.draw(
                        draw_x, draw_y,
                        img.w * self.panther.scale_factor,
                        img.h * self.panther.scale_factor
                    )

        except Exception as e:
            print(f"\033[91m[Pattern6.draw] 그리기 오류: {e}\033[0m")
