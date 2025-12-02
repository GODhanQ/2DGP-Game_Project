import pico2d as p2
import random
import math
import game_framework as framework
from ...behavior_tree import BehaviorTree


class AttackPattern5Action:
    """
    패턴5 - 분신 1체 랜덤 위치에 소환후 모든 방향 방사형으로 수리검 투척 2회 ( 두 번째 투척 수리검의 속도는 첫 번째 투척 속도의 반 )
    자세한 설명:
    1. 플레이어 주변으로 분신 1체를 소환한다. 소환 방식은 panther_assassin_4pattern.py의 패턴4와 동일하다.
    2. 분신이 이동을 완료하면, 분신에서 모든 방향으로 수리검을 투척한다. (360도)
        - 첫 번째 투척은 기본 속도(650 픽셀/초)로 투척한다.
        - 두 번째 투척은 첫 번째 투척의 절반 속도(325 픽셀/초)로 투척한다.
        - 수리검 투척은 첫번째 투척 후, 0.15초 후에 두 번째 투척이 이루어진다.
    3. 수리검 투척이 완료되면, 분신은 사라진다.
    4. 패턴이 종료된다.

    기본 모션 경로 : 'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character'
    투척시 모션 : PantherAssassin_Whirlwind{i:02d}.png 0 ~ 5
        - 던지는 동안 계속해서 반복 재생
    투척 이후 모션 : PantherAssassin_Throw_All_Withdraw{i:02d}.png 0 ~ 9

    주의 :
        - 수리검은 PantherShuriken를 사용한다.
        - 투척 이후 모션 재생 후 패턴 종료
        - 투척 각도는 0도, 90도, 180도, 270도 를 기준으로 +- 10도는 투척 각도에서 제외한다.
          이렇게 하여 플레이어가 피하기 쉽도록 한다.
          각 투척 각도(10~80, 100~170, 190~260, 280~350)에서 약 7개씩 투척된다.
        - 투척 휠윈드 모션 3 이후 부터 투척한다.
        - 분신과 본체 모두 똑같이 행동한다. (투척 모션 재생 등)
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
        self.clone = None  # 분신 객체
        self.clones_spawned = False  # 분신 소환 완료 플래그

        # 수리검 투척 관련 변수
        self.shot_count = 0  # 현재 투척 횟수 (1회, 2회)
        self.max_shots = 2  # 최대 투척 횟수 (2회)
        self.shot_interval = 0.1  # 투척 간격
        self.first_speed = 450  # 첫 번째 투척 속도
        self.second_speed = 325  # 두 번째 투척 속도
        self.projectiles_per_shot = 35  # 한 번에 발사하는 수리검 개수 (약 7개씩 * 4구간)

        # 애니메이션 관련 변수
        self.whirlwind_frame = 0  # Whirlwind 애니메이션 프레임
        self.whirlwind_frame_timer = 0.0
        self.whirlwind_frame_speed = 12.0  # 초당 프레임 수
        self.whirlwind_total_frames = 6  # 0~5 (총 6프레임)
        self.throw_start_frame = 3  # 3번 프레임부터 투척 시작
        self.has_thrown_in_cycle = False  # 현재 사이클에서 이미 투척했는지

        self.withdraw_frame = 0  # Withdraw 애니메이션 프레임
        self.withdraw_frame_timer = 0.0
        self.withdraw_frame_speed = 15.0  # 초당 프레임 수
        self.withdraw_total_frames = 10  # 0~9 (총 10프레임)

        # 이미지 로드
        self._load_images()

    def _load_images(self):
        """애니메이션 이미지 로드"""
        try:
            from game_logic import image_asset_manager as iam

            base_path = "resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character"
            print(f"[Pattern5._load_images] 이미지 로드 시작 - 경로: {base_path}")

            # 원본 이미지 로드 및 분신용 어두운 이미지 생성
            self.original_images = {
                'whirlwind': [],
                'withdraw': [],
                'move': [],
                'stealth': [],  # 은신 모션 (Die 모션 재활용)
                'die': []  # 분신 사라지는 애니메이션용
            }

            self.clone_images = {
                'whirlwind': [],
                'withdraw': [],
                'move': [],
                'die': []
            }

            # Whirlwind 모션 (0~5)
            for i in range(6):
                try:
                    img_path = f"{base_path}/PantherAssassin_Whirlwind{i:02d}.png"
                    img = p2.load_image(img_path)
                    self.original_images['whirlwind'].append(img)

                    # 분신용 어두운 버전 생성
                    iam.register_image_path(img, img_path)
                    clone_img = iam.make_dark(img, darkness=0.25)
                    self.clone_images['whirlwind'].append(clone_img)
                except Exception as e:
                    print(f"\033[91m[Pattern5._load_images] Whirlwind{i:02d}.png 로드 실패: {e}\033[0m")

            # Throw_All_Withdraw 모션 (0~9)
            for i in range(10):
                try:
                    img_path = f"{base_path}/PantherAssassin_Throw_All_Withdraw{i:02d}.png"
                    img = p2.load_image(img_path)
                    self.original_images['withdraw'].append(img)

                    # 분신용 어두운 버전 생성
                    iam.register_image_path(img, img_path)
                    clone_img = iam.make_dark(img, darkness=0.25)
                    self.clone_images['withdraw'].append(clone_img)
                except Exception as e:
                    print(f"\033[91m[Pattern5._load_images] Throw_All_Withdraw{i:02d}.png 로드 실패: {e}\033[0m")

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
                    print(f"\033[91m[Pattern5._load_images] Move{i:02d}.png 로드 실패: {e}\033[0m")

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
                    print(f"\033[91m[Pattern5._load_images] Die{i:02d}.png 로드 실패: {e}\033[0m")

            # Stealth 모션도 Die 모션 사용 (본체용)
            self.original_images['stealth'] = self.original_images['die']

            print(f"[Pattern5._load_images] 원본 이미지 로드 완료 - "
                  f"Whirlwind: {len(self.original_images['whirlwind'])}개, "
                  f"Withdraw: {len(self.original_images['withdraw'])}개, "
                  f"Move: {len(self.original_images['move'])}개, "
                  f"Die: {len(self.original_images['die'])}개")

            print(f"[Pattern5._load_images] 분신 이미지 생성 완료 - "
                  f"Whirlwind: {len(self.clone_images['whirlwind'])}개, "
                  f"Withdraw: {len(self.clone_images['withdraw'])}개, "
                  f"Move: {len(self.clone_images['move'])}개, "
                  f"Die: {len(self.clone_images['die'])}개")

        except Exception as e:
            print(f"\033[91m[Pattern5._load_images] 전체 로드 과정 오류: {e}\033[0m")
            import traceback
            traceback.print_exc()

    def update(self):
        """패턴 5 로직 실행"""
        try:
            dt = framework.get_delta_time()

            if self.phase == 0:
                # Phase 0: 초기화 및 분신 소환 시작
                self.timer = 0.0
                self.shot_count = 0
                self.whirlwind_frame = 0
                self.whirlwind_frame_timer = 0.0
                self.has_thrown_in_cycle = False
                self.clone = None
                self.clones_spawned = False

                print("[Pattern5] 패턴 시작 - 분신 소환 시작!")
                self.phase = 1

            elif self.phase == 1:
                # Phase 1: 분신 소환 (본체 위치에 생성 후 랜덤 위치로 이동)
                if not self.clones_spawned:
                    try:
                        print(f"[Pattern5] 분신 소환 - 본체 위치: ({self.panther.x:.0f}, {self.panther.y:.0f})")

                        # 랜덤 위치 계산 (본체로부터 거리)
                        angle = random.uniform(0, 360)
                        rad = math.radians(angle)
                        distance = random.uniform(200, 300)

                        target_x = self.panther.x + math.cos(rad) * distance
                        target_y = self.panther.y + math.sin(rad) * distance

                        # 분신 생성
                        from ..panther_assassin import Clone
                        self.clone = Clone(
                            self.panther.x, self.panther.y,
                            target_x, target_y,
                            self.clone_images,
                            self.panther.scale_factor
                        )

                        # effects_front 레이어에 추가
                        if self.panther.world and 'effects_front' in self.panther.world:
                            self.panther.world['effects_front'].append(self.clone)
                            print(f"[Pattern5] 분신 소환 완료: ({target_x:.0f}, {target_y:.0f}) - effects_front 레이어에 추가됨")

                        self.clones_spawned = True

                    except Exception as e:
                        print(f"\033[91m[Pattern5] 분신 소환 중 오류: {e}\033[0m")
                        import traceback
                        traceback.print_exc()

                # 분신 이동 완료 대기 (이 단계에서는 본체가 IDLE 모션 유지)
                if self.clones_spawned and self.clone and not self.clone.is_moving:
                    print("[Pattern5] 분신 이동 완료! 수리검 투척 준비")
                    self.timer = 0.0
                    self.whirlwind_frame = 0
                    self.whirlwind_frame_timer = 0.0
                    self.has_thrown_in_cycle = False

                    # 분신을 Whirlwind 애니메이션으로 전환
                    self.clone.switch_animation('whirlwind')
                    self.phase = 2

            elif self.phase == 2:
                # Phase 2: Whirlwind 애니메이션 재생 및 첫 번째 수리검 투척
                self.whirlwind_frame_timer += dt

                if self.whirlwind_frame_timer >= 1.0 / self.whirlwind_frame_speed:
                    self.whirlwind_frame_timer = 0.0

                    # 프레임 3에 도달하면 첫 번째 투척
                    if self.whirlwind_frame >= self.throw_start_frame and not self.has_thrown_in_cycle:
                        self._shoot_shurikens_360(self.first_speed)
                        self.shot_count = 1
                        self.has_thrown_in_cycle = True
                        print(f"[Pattern5] 1차 투척 완료 (속도: {self.first_speed})")

                    self.whirlwind_frame += 1

                    # Whirlwind 애니메이션 반복 (0~5)
                    if self.whirlwind_frame >= self.whirlwind_total_frames:
                        self.whirlwind_frame = 0
                        self.has_thrown_in_cycle = False

                        # 첫 번째 투척 완료 후 대기로 전환
                        if self.shot_count >= 1:
                            self.timer = 0.0
                            self.phase = 3
                            print("[Pattern5] 1차 투척 완료, 2차 투척 대기")

            elif self.phase == 3:
                # Phase 3: 두 번째 투척 대기 (0.1초) - Whirlwind 애니메이션 계속 재생
                self.timer += dt

                # Whirlwind 애니메이션 계속 재생
                self.whirlwind_frame_timer += dt
                if self.whirlwind_frame_timer >= 1.0 / self.whirlwind_frame_speed:
                    self.whirlwind_frame_timer = 0.0
                    self.whirlwind_frame = (self.whirlwind_frame + 1) % self.whirlwind_total_frames

                if self.timer >= self.shot_interval:
                    # 두 번째 투척 준비
                    self.whirlwind_frame = 0
                    self.whirlwind_frame_timer = 0.0
                    self.has_thrown_in_cycle = False
                    self.phase = 4
                    print("[Pattern5] 2차 투척 시작")

            elif self.phase == 4:
                # Phase 4: Whirlwind 애니메이션 재생 및 두 번째 수리검 투척
                self.whirlwind_frame_timer += dt

                if self.whirlwind_frame_timer >= 1.0 / self.whirlwind_frame_speed:
                    self.whirlwind_frame_timer = 0.0

                    # 프레임 3에 도달하면 두 번째 투척
                    if self.whirlwind_frame >= self.throw_start_frame and not self.has_thrown_in_cycle:
                        self._shoot_shurikens_360(self.second_speed)
                        self.shot_count = 2
                        self.has_thrown_in_cycle = True
                        print(f"[Pattern5] 2차 투척 완료 (속도: {self.second_speed})")

                    self.whirlwind_frame += 1

                    # Whirlwind 애니메이션 반복
                    if self.whirlwind_frame >= self.whirlwind_total_frames:
                        self.whirlwind_frame = 0
                        self.has_thrown_in_cycle = False

                        # 두 번째 투척 완료 후 Withdraw 애니메이션으로 전환
                        if self.shot_count >= 2:
                            self.withdraw_frame = 0
                            self.withdraw_frame_timer = 0.0

                            # 분신을 Withdraw 애니메이션으로 전환
                            if self.clone:
                                self.clone.switch_animation('withdraw')
                            self.phase = 5
                            print("[Pattern5] 2차 투척 완료, Withdraw 애니메이션 시작")

            elif self.phase == 5:
                # Phase 5: Throw_All_Withdraw 애니메이션 재생
                self.withdraw_frame_timer += dt

                if self.withdraw_frame_timer >= 1.0 / self.withdraw_frame_speed:
                    self.withdraw_frame += 1
                    self.withdraw_frame_timer = 0.0

                    # Withdraw 애니메이션 종료 (0~9)
                    if self.withdraw_frame >= self.withdraw_total_frames:
                        # 분신 사라지는 애니메이션 시작
                        if self.clone:
                            self.clone.start_dying()
                        self.phase = 6
                        print("[Pattern5] Withdraw 애니메이션 완료, 분신 소멸 시작")

            elif self.phase == 6:
                # Phase 6: 분신 사라지는 애니메이션 대기
                # 분신의 Die 애니메이션이 완료될 때까지 대기
                if self.clone and (self.clone.to_be_removed or self.clone.mark_for_removal):
                    # 패턴 완료
                    self.phase = 0
                    self.panther.attack_timer = self.panther.attack_cooldown
                    print("[Pattern5] 패턴 완료!")
                    return BehaviorTree.SUCCESS

            return BehaviorTree.RUNNING

        except Exception as e:
            print(f"\033[91m[Pattern5.update] 오류 발생: {e}\033[0m")
            import traceback
            traceback.print_exc()
            # 오류 발생 시 패턴 종료
            self.phase = 0
            self.panther.attack_timer = self.panther.attack_cooldown
            return BehaviorTree.FAIL

    def _shoot_shurikens_360(self, speed):
        """
        360도 모든 방향으로 수리검 발사 (0, 90, 180, 270도 +-10도 제외)

        Args:
            speed: 수리검 속도
        """
        if not self.clone or not self.panther.world:
            return

        try:
            # 허용된 각도 범위 계산
            excluded_angle = 20
            allowed_ranges = [
                (0 + excluded_angle, 90 - excluded_angle),
                (90 + excluded_angle, 180 - excluded_angle),
                (180 + excluded_angle, 270 - excluded_angle),
                (270 + excluded_angle, 360 - excluded_angle),
            ]

            # 각 범위에서 7개씩 수리검 발사
            shurikens_per_range = 7
            total_shurikens = 0

            for angle_min, angle_max in allowed_ranges:
                angle_step = (angle_max - angle_min) / (shurikens_per_range - 1)

                for i in range(shurikens_per_range):
                    angle = angle_min + angle_step * i
                    rad = math.radians(angle)

                    # 수리검이 날아갈 목표 위치 계산 (충분히 먼 거리)
                    target_distance = 2000
                    target_x = self.clone.x + math.cos(rad) * target_distance
                    target_y = self.clone.y + math.sin(rad) * target_distance

                    # 본체에서 수리검 발사
                    from ..panther_assassin import PantherShuriken
                    shuriken_body = PantherShuriken(
                        self.panther.x, self.panther.y,
                        target_x, target_y,
                        speed=speed,
                        from_player=False,
                        damage=20,
                        scale=2.5
                    )
                    self.panther.world['effects_front'].append(shuriken_body)
                    total_shurikens += 1

                    # 분신에서 수리검 발사
                    shuriken_clone = PantherShuriken(
                        self.clone.x, self.clone.y,
                        target_x, target_y,
                        speed=speed,
                        from_player=False,
                        damage=20,
                        scale=2.5
                    )
                    self.panther.world['effects_front'].append(shuriken_clone)
                    total_shurikens += 1

            print(f"[Pattern5] 360도 방사형 수리검 발사 완료")
            print(f"  - 속도: {speed} 픽셀/초")
            print(f"  - 총 수리검 개수: {total_shurikens}개 (본체: {shurikens_per_range * 4}개, 분신: {shurikens_per_range * 4}개)")
            print(f"  - 각 사분면당: {shurikens_per_range}개씩")
            print(f"  - 제외 각도: 0°±{excluded_angle}°, 90°±{excluded_angle}°, 180°±{excluded_angle}°, 270°±{excluded_angle}°")

        except Exception as e:
            print(f"\033[91m[Pattern5._shoot_shurikens_360] 수리검 발사 중 오류: {e}\033[0m")
            import traceback
            traceback.print_exc()

    def draw(self, draw_x, draw_y):
        """
        패턴 5 시각 효과 드로잉

        Args:
            draw_x, draw_y: 보스의 현재 위치 (카메라 좌표계)
        """
        try:
            # 본체 애니메이션 그리기
            if self.phase in [2, 3, 4]:  # Whirlwind 애니메이션 중
                if self.original_images['whirlwind'] and self.whirlwind_frame < len(self.original_images['whirlwind']):
                    img = self.original_images['whirlwind'][self.whirlwind_frame]
                    if img:
                        img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

            elif self.phase == 5:  # Withdraw 애니메이션 중
                if self.original_images['withdraw'] and self.withdraw_frame < len(self.original_images['withdraw']):
                    img = self.original_images['withdraw'][self.withdraw_frame]
                    if img:
                        img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

        except Exception as e:
            print(f"\033[91m[Pattern5.draw] 드로잉 중 오류: {e}\033[0m")
