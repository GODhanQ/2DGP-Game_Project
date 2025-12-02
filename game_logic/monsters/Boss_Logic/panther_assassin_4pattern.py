import pico2d as p2
import random
import math
import game_framework as framework
from ...behavior_tree import BehaviorTree

class AttackPattern4Action:
    """
    panther_assassin.py의 보스 개체(PantherAssassin)의 공격패턴 4 구현 클래스
    패턴4 - 은신과 분신 2체를 랜덤 위치에 소환 후 플레이어를 향해 수리검 10회 연속 투척 이후 본체 은신 풀림
    자세한 설명:
    1. 은신과 동시에 분신 2체를 Panther의 위치에 소환후 랜덤한 위치로 이동시킨다.
        분신 소환시 분신이 위치로 부드럽게 이동한다 + 이동시 제자리에 동일한 모션 하나를 더 만들어
        alpha를 0.5초만에 1에서 0으로 점점 줄여가며 사라지게 한다 (이동 이펙트)
    2. 분신에서만 PantherShuriken 투척 (본체는 투척하지 않음)
    3. 수리검은 플레이어를 향해 10회 연속 투척, 투척 간격은 매우 짧음
    4. 모든 수리검 투척이 끝나면 본체의 은신이 풀림
    5. 패턴 종료

    기본 모션 경로: resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character
    Throw 1st 와 Throw 2nd 모션을 번갈아 가며 재생하여 양손에서 수리검을 던지는 효과 연출
    투척 1st 모션: PantherAssassin_Throw_1st{i:02d}.png 0 ~ 5
    투척 2nd 모션: PantherAssassin_Throw_2nd{i:02d}.png 0 ~ 5
    이동 모션: PantherAssassin_Move{i:02d}.png 0 ~ 7

    주의: 분신은 본체와 구별을 위해 image_asset_manager.py의 make_dark 함수를 이용해
        원본 이미지보다 검정색으로 편향된 이미지를 사용하여 구분한다.

        이 분신은 충돌 처리나 공격 처리 등이 필요 없으며, 단순히 시각 효과 용도이므로
        별도의 몬스터 객체로 만들지 않고 패턴 내부에서 위치 정보만 관리한다.

    """

    def __init__(self, panther):
        """
        Args:
            panther: PantherAssassin 인스턴스 참조
        """
        self.panther = panther
        self.phase = 0
        self.timer = 0.0

        # 은신 모션 관련 변수
        self.stealth_animation_frames = 11  # Die 모션 프레임 수 (0~10)
        self.stealth_frame = 0  # 현재 은신 모션 프레임
        self.stealth_frame_duration = 0.08  # 프레임당 시간 (초)
        self.is_stealth_animation_done = False  # 은신 모션 완료 플래그
        self.is_unstealth_animation_done = False  # 은신 해제 모션 완료 플래그

        # 은신 관련 변수
        self.stealth_duration = 1.0  # 은신 지속 시간
        self.is_stealthed = False  # 은신 상태

        # 분신 소환 관련 변수
        self.clone_count = 2  # 분신 개수
        self.clones = []  # Clone 객체 리스트
        self.clones_spawned = False  # 분신 소환 완료 플래그 (버그 수정용)

        # 수리검 투척 관련 변수
        self.shot_count = 0  # 현재 투척 횟수
        self.max_shots = 10  # 최대 투척 횟수 (10회)
        self.shot_interval = 0.15  # 투척 간격 (매우 짧음)
        self.projectile_speed = 700  # 수리검 속도

        # 본체 텔레포트 관련 변수
        self.teleport_target_x = 0  # 텔레포트 목표 위치 X
        self.teleport_target_y = 0  # 텔레포트 목표 위치 Y

        # 이미지 로드
        self._load_images()

    def _load_images(self):
        """애니메이션 이미지 로드"""
        try:
            from game_logic import image_asset_manager as iam

            base_path = "resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character"
            print(f"[Pattern4._load_images] 이미지 로드 시작 - 경로: {base_path}")

            # 원본 이미지 로드 및 분신용 어두운 이미지 생성
            self.original_images = {
                'throw_1st': [],
                'throw_2nd': [],
                'move': [],
                'stealth': []  # 은신 모션 추가 (Die 모션 재활용)
            }

            self.clone_images = {
                'throw_1st': [],
                'throw_2nd': [],
                'move': [],
                'die': []  # Die 모션 추가 (분신 사라지는 애니메이션용)
            }

            # Throw 1st 모션 (0~5)
            for i in range(6):
                try:
                    img_path = f"{base_path}/PantherAssassin_Throw_1st{i:02d}.png"
                    img = p2.load_image(img_path)
                    self.original_images['throw_1st'].append(img)

                    # 경로 등록 후 어두운 버전 생성 (panther_assassin과 동일한 방식)
                    iam.register_image_path(img, img_path)
                    clone_img = iam.make_dark(img, darkness=0.25)
                    self.clone_images['throw_1st'].append(clone_img)
                except Exception as e:
                    print(f"\033[91m[Pattern4._load_images] Throw_1st{i:02d}.png 로드 실패: {e}\033[0m")
                    import traceback
                    traceback.print_exc()

            # Throw 2nd 모션 (0~5)
            for i in range(6):
                try:
                    img_path = f"{base_path}/PantherAssassin_Throw_2nd{i:02d}.png"
                    img = p2.load_image(img_path)
                    self.original_images['throw_2nd'].append(img)

                    # 경로 등록 후 어두운 버전 생성
                    iam.register_image_path(img, img_path)
                    clone_img = iam.make_dark(img, darkness=0.25)
                    self.clone_images['throw_2nd'].append(clone_img)
                except Exception as e:
                    print(f"\033[91m[Pattern4._load_images] Throw_2nd{i:02d}.png 로드 실패: {e}\033[0m")
                    import traceback
                    traceback.print_exc()

            # Move 모션 (0~7)
            for i in range(8):
                try:
                    img_path = f"{base_path}/PantherAssassin_Move{i:02d}.png"
                    img = p2.load_image(img_path)
                    self.original_images['move'].append(img)

                    # 경로 등록 후 어두운 버전 생성
                    iam.register_image_path(img, img_path)
                    clone_img = iam.make_dark(img, darkness=0.25)
                    self.clone_images['move'].append(clone_img)
                except Exception as e:
                    print(f"\033[91m[Pattern4._load_images] Move{i:02d}.png 로드 실패: {e}\033[0m")
                    import traceback
                    traceback.print_exc()

            # Stealth 모션 (Die 모션 재활용, 0~10)
            for i in range(11):
                try:
                    img_path = f"{base_path}/PantherAssassin_Die{i:02d}.png"
                    img = p2.load_image(img_path)
                    self.original_images['stealth'].append(img)
                    
                    # 분신용 Die 애니메이션도 어두운 버전으로 생성
                    iam.register_image_path(img, img_path)
                    clone_die_img = iam.make_dark(img, darkness=0.25)
                    self.clone_images['die'].append(clone_die_img)
                except Exception as e:
                    print(f"\033[91m[Pattern4._load_images] Die{i:02d}.png (은신 모션) 로드 실패: {e}\033[0m")
                    import traceback
                    traceback.print_exc()

            print(f"[Pattern4._load_images] 원본 이미지 로드 결과 - "
                  f"Throw1st: {len(self.original_images['throw_1st'])}개, "
                  f"Throw2nd: {len(self.original_images['throw_2nd'])}개, "
                  f"Move: {len(self.original_images['move'])}개, "
                  f"Stealth: {len(self.original_images['stealth'])}개")

            print(f"[Pattern4._load_images] 분신 이미지 생성 완료 - "
                  f"Throw1st: {len(self.clone_images['throw_1st'])}개, "
                  f"Throw2nd: {len(self.clone_images['throw_2nd'])}개, "
                  f"Move: {len(self.clone_images['move'])}개")

        except Exception as e:
            print(f"\033[91m[Pattern4._load_images] 전체 로드 과정 오류: {e}\033[0m")
            import traceback
            traceback.print_exc()

    def update(self):
        """패턴 4 로직 실행"""
        try:
            dt = framework.get_delta_time()

            if self.phase == 0:
                # Phase 0: 초기화 및 은신 애니메이션 시작
                self.timer = 0.0
                self.stealth_frame = 0
                self.is_stealth_animation_done = False
                self.is_unstealth_animation_done = False
                self.clones = []
                self.clones_spawned = False
                self.shot_count = 0

                # 패턴 4 시작 시 본체 무적 활성화
                self.panther.invincible = True
                print("[Pattern4] 패턴 시작 - 은신 애니메이션 재생 (무적 활성화)")

                self.phase = 1

            elif self.phase == 1:
                # Phase 1: 은신 애니메이션 재생 (0 -> 10 프레임) + 분신 소환 동시 진행
                self.timer += dt

                # 분신 소환 (최초 1회만, 은신 애니메이션과 동시에 생성)
                if not self.clones_spawned:
                    try:
                        print(f"[Pattern4] 은신과 동시에 분신 소환 시작 - 본체 위치: ({self.panther.x:.0f}, {self.panther.y:.0f})")

                        # 모든 분신을 한 번에 생성
                        for i in range(self.clone_count):
                            # 각 분신마다 랜덤 위치 계산
                            angle = random.uniform(0, 360)
                            rad = math.radians(angle)
                            distance = random.uniform(150, 250)  # 본체로부터 거리

                            target_x = self.panther.x + math.cos(rad) * distance
                            target_y = self.panther.y + math.sin(rad) * distance

                            # 분신 생성 (본체 위치에서 시작, 본체의 scale_factor 전달)
                            from ..panther_assassin import Clone
                            clone = Clone(
                                self.panther.x, self.panther.y,
                                target_x, target_y,
                                self.clone_images,
                                self.panther.scale_factor  # 본체와 동일한 scale 사용
                            )
                            self.clones.append(clone)

                            # effects_front 레이어에 추가 (카메라 좌표 자동 적용, 충돌 검사 제외)
                            if self.panther.world and 'effects_front' in self.panther.world:
                                self.panther.world['effects_front'].append(clone)
                                print(f"[Pattern4] 분신 {i+1}/{self.clone_count} 소환: ({target_x:.0f}, {target_y:.0f}) - effects_front 레이어에 추가됨")

                        self.clones_spawned = True  # 소환 완료 플래그 설정
                        print(f"[Pattern4] 모든 분신 소환 완료! 총 {len(self.clones)}체")

                    except Exception as e:
                        print(f"\033[91m[Pattern4] 분신 소환 중 오류: {e}\033[0m")
                        import traceback
                        traceback.print_exc()

                # 프레임 업데이트
                if self.timer >= self.stealth_frame_duration:
                    self.stealth_frame += 1
                    self.timer = 0.0

                    # 은신 애니메이션 완료 체크 (0~10, 총 11프레임)
                    if self.stealth_frame >= self.stealth_animation_frames:
                        self.is_stealth_animation_done = True
                        self.is_stealthed = True
                        self.timer = 0.0
                        self.phase = 2
                        print("[Pattern4] 은신 애니메이션 완료! 분신 이동 대기")

            elif self.phase == 2:
                # Phase 2: 은신 중 - 분신 이동 대기
                self.timer += dt

                # 모든 분신의 이동 완료 체크
                if self.clones_spawned and len(self.clones) == self.clone_count:
                    # 모든 분신이 목표 위치에 도착했는지 확인
                    all_moved = all(not clone.is_moving for clone in self.clones)

                    if all_moved:
                        # Phase 3으로 전환 (수리검 투척 시작)
                        self.timer = 0.0
                        self.phase = 3
                        print("[Pattern4] 분신 이동 완료! 수리검 투척 시작!")

            elif self.phase == 3:
                # Phase 3: 수리검 투척 (분신에서만)
                self.timer += dt

                # 투척 간격마다 수리검 발사
                if self.timer >= self.shot_interval:
                    if self.shot_count < self.max_shots:
                        try:
                            # 각 분신에서 수리검 발사
                            for clone in self.clones:
                                if self.panther.target and self.panther.world and 'effects_front' in self.panther.world:
                                    # PantherShuriken 생성
                                    from ..panther_assassin import PantherShuriken
                                    shuriken = PantherShuriken(
                                        clone.x, clone.y,
                                        self.panther.target.x, self.panther.target.y,
                                        speed=self.projectile_speed,
                                        from_player=False,
                                        damage=15,
                                        scale=2.5
                                    )

                                    # world의 effects_front 레이어에 추가
                                    self.panther.world['effects_front'].append(shuriken)
                                    print(f"[Pattern4] 수리검 생성: ({int(clone.x)}, {int(clone.y)}) -> ({int(self.panther.target.x)}, {int(self.panther.target.y)})")

                                # 투척 애니메이션 교대 (1st <-> 2nd)
                                throw_type = 'throw_1st' if self.shot_count % 2 == 0 else 'throw_2nd'
                                clone.switch_throw_animation(throw_type)

                            self.shot_count += 1
                            self.timer = 0.0
                            print(f"[Pattern4] 수리검 발사 {self.shot_count}/{self.max_shots} (분신 {len(self.clones)}체)")

                        except Exception as e:
                            print(f"\033[91m[Pattern4] 수리검 발사 중 오류: {e}\033[0m")
                            import traceback
                            traceback.print_exc()

                # 모든 수리검 발사 완료
                if self.shot_count >= self.max_shots:
                    # 본체 텔레포트 목표 위치 계산 (플레이어 주위 랜덤 위치)
                    if self.panther.target:
                        angle = random.uniform(0, 360)
                        rad = math.radians(angle)
                        distance = random.uniform(100, 200)  # 플레이어로부터 거리

                        self.teleport_target_x = self.panther.target.x + math.cos(rad) * distance
                        self.teleport_target_y = self.panther.target.y + math.sin(rad) * distance

                        # 본체 텔레포트 즉시 실행
                        self.panther.x = self.teleport_target_x
                        self.panther.y = self.teleport_target_y
                        print(f"[Pattern4] 본체 텔레포트 완료: ({self.panther.x:.0f}, {self.panther.y:.0f})")
                    else:
                        # 타겟이 없으면 현재 위치 유지
                        self.teleport_target_x = self.panther.x
                        self.teleport_target_y = self.panther.y

                    self.phase = 4
                    self.timer = 0.0
                    self.stealth_frame = self.stealth_animation_frames - 1  # 역재생 시작 (10부터 시작)
                    print("[Pattern4] 수리검 투척 완료! 텔레포트 후 은신 해제 애니메이션 시작")

            elif self.phase == 4:
                # Phase 4: 은신 해제 애니메이션 재생 (10 -> 0 프레임, 역순)
                # 이미 Phase 3에서 텔레포트가 완료된 상태
                self.timer += dt

                # 프레임 업데이트 (역순)
                if self.timer >= self.stealth_frame_duration:
                    self.stealth_frame -= 1
                    self.timer = 0.0

                    # 은신 해제 애니메이션 완료 체크
                    if self.stealth_frame < 0:
                        self.is_unstealth_animation_done = True
                        self.is_stealthed = False
                        self.phase = 5
                        print("[Pattern4] 은신 해제 애니메이션 완료!")

            elif self.phase == 5:
                # Phase 5: 패턴 종료 정리

                # 패턴 4 종료 시 본체 무적 해제
                self.panther.invincible = False
                print("[Pattern4] 패턴 종료! (무적 해제)")

                # 분신에게 사라지는 애니메이션 시작 명령
                for clone in self.clones:
                    clone.start_dying()
                    print(f"[Pattern4] 분신 Die 애니메이션 시작 - 위치: ({clone.x:.0f}, {clone.y:.0f})")

                # 분신은 자동으로 애니메이션 후 제거되므로 여기서는 리스트만 비움
                self.clones = []

                # 패턴 종료
                self.phase = 0
                if hasattr(self.panther, 'attack_timer') and hasattr(self.panther, 'attack_cooldown'):
                    self.panther.attack_timer = self.panther.attack_cooldown
                return BehaviorTree.SUCCESS

            return BehaviorTree.RUNNING

        except Exception as e:
            print(f"\033[91m[Pattern4.update] 전체 업데이트 오류 (phase={self.phase}): {e}\033[0m")
            import traceback
            traceback.print_exc()

            # 오류 발생 시에도 무적 해제 (안전장치)
            self.panther.invincible = False
            print("[Pattern4] 오류로 인한 긴급 무적 해제")

            return BehaviorTree.RUNNING

    def draw(self, draw_x, draw_y):
        """
        패턴 4 전용 그리기 메서드

        본체의 은신/해제 애니메이션을 그립니다.
        - Phase 1: 은신 애니메이션 (0 -> 10 프레임)
        - Phase 2, 3: 은신 상태 (본체 숨김)
        - Phase 4: 은신 해제 애니메이션 (10 -> 0 프레임, 역순)
        - Phase 5: 정상 상태 (기본 Idle 애니메이션)
        """
        try:
            # Phase 1: 은신 애니메이션 재생 (0 -> 10)
            if self.phase == 1 and len(self.original_images['stealth']) > 0:
                if 0 <= self.stealth_frame < len(self.original_images['stealth']):
                    img = self.original_images['stealth'][self.stealth_frame]
                    img.draw(
                        draw_x, draw_y,
                        img.w * self.panther.scale_factor,
                        img.h * self.panther.scale_factor
                    )

            # Phase 2, 3: 은신 상태 (본체 숨김 - 아무것도 그리지 않음)
            elif self.phase in [2, 3]:
                pass  # 본체는 보이지 않음

            # Phase 4: 은신 해제 애니메이션 재생 (10 -> 0, 역순)
            elif self.phase == 4 and len(self.original_images['stealth']) > 0:
                if 0 <= self.stealth_frame < len(self.original_images['stealth']):
                    img = self.original_images['stealth'][self.stealth_frame]
                    img.draw(
                        draw_x, draw_y,
                        img.w * self.panther.scale_factor,
                        img.h * self.panther.scale_factor
                    )

            # Phase 0, 5: 기본 Idle 애니메이션 (PantherAssassin의 기본 draw에서 처리)
            else:
                # 기본 상태는 PantherAssassin.draw()에서 처리하도록 패스
                pass

        except Exception as e:
            print(f"\033[91m[Pattern4.draw] 그리기 오류: {e}\033[0m")
            import traceback
            traceback.print_exc()
