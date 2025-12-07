import pico2d as p2
from ...behavior_tree import BehaviorTree
import game_framework as framework
import math
import random

class AttackPattern3Action:
    """
    panther_assassin.py의 보스 개체(PantherAssassin)의 공격패턴 3 구현 클래스
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

    # 클래스 레벨 이미지 시퀀스
    combo1_ready_img_seq = []    # Combo1_Ready 0~8 (9프레임)
    combo1_attack_img_seq = []   # Combo1_Attack 0~6 (7프레임)
    combo2_ready_img_seq = []    # Combo2_Ready 0~6 (7프레임)
    combo2_attack_start_img_seq = []  # Combo2_Attack_Start 0~3 (4프레임)
    combo2_attack_cycle_img_seq = []  # Combo2_Attack_Cycle 0~3 (4프레임)
    combo3_ready_img_seq = []    # Combo3_Ready 0~3 (4프레임)
    combo3_attack_img_seq = []   # Combo3_Attack 0~9 (10프레임)
    combo3_swing_fx_img_seq = []  # Combo3 수리검 발사 이펙트 0~3 (4프레임) - 대미지 없음

    def __init__(self, panther):
        """
        Args:
            panther: PantherAssassin 인스턴스 참조
        """
        self.panther = panther
        self.phase = 0
        self.timer = 0.0

        # 콤보 진행 관련 변수
        self.current_combo = 0  # 현재 콤보 단계 (1, 2, 3)
        self.max_combo = 3      # 최대 콤보 수

        # 콤보1 준비 모션 관련 변수
        self.combo1_ready_frame = 0
        self.combo1_ready_frame_timer = 0.0
        self.combo1_ready_frame_speed = 15.0
        self.combo1_ready_total_frames = 9  # 0~8

        # 콤보1 돌진 공격 관련 변수
        self.combo1_dash_start_x = 0.0
        self.combo1_dash_start_y = 0.0
        self.combo1_dash_target_x = 0.0
        self.combo1_dash_target_y = 0.0
        self.combo1_dash_duration = 0.5  # 0.5초 돌진
        self.combo1_dash_progress = 0.0
        self.combo1_dash_frame = 0
        self.combo1_dash_frame_timer = 0.0
        self.combo1_dash_frame_speed = 14.0  # 7프레임을 0.5초에
        self.combo1_dash_total_frames = 7  # 0~6
        self.combo1_dash_distance_multiplier = 1.0  # 플레이어까지 거리의 1배
        self.combo1_flip_x = False  # 좌우 반전 플래그

        # 콤보2 준비 모션 관련 변수
        self.combo2_ready_frame = 0
        self.combo2_ready_frame_timer = 0.0
        self.combo2_ready_frame_speed = 15.0
        self.combo2_ready_total_frames = 7  # 0~6

        # 콤보2 돌진 공격 관련 변수
        self.combo2_dash_start_x = 0.0
        self.combo2_dash_start_y = 0.0
        self.combo2_dash_target_x = 0.0
        self.combo2_dash_target_y = 0.0
        self.combo2_dash_duration = 0.3  # 0.3초 돌진 (더 빠름)
        self.combo2_dash_progress = 0.0
        self.combo2_dash_frame = 0  # Start 또는 Cycle 프레임
        self.combo2_dash_frame_timer = 0.0
        self.combo2_dash_frame_speed = 13.3  # Start 4프레임을 0.3초에
        self.combo2_dash_start_total_frames = 4  # Start 0~3
        self.combo2_dash_cycle_total_frames = 4  # Cycle 0~3
        self.combo2_dash_distance_multiplier = 1.5  # 플레이어까지 거리의 1.5배
        self.combo2_in_cycle = False  # Cycle 모션으로 전환되었는지
        self.combo2_flip_x = False  # 좌우 반전 플래그

        # 콤보3 준비 모션 관련 변수
        self.combo3_ready_frame = 0
        self.combo3_ready_frame_timer = 0.0
        self.combo3_ready_frame_speed = 15.0
        self.combo3_ready_total_frames = 4  # 0~3

        # 콤보3 수리검 발사 관련 변수
        self.combo3_attack_frame = 0
        self.combo3_attack_frame_timer = 0.0
        self.combo3_attack_frame_speed = 20.0
        self.combo3_attack_total_frames = 10  # 0~9
        self.combo3_shuriken_thrown = False  # 수리검 발사 완료 플래그
        self.combo3_shoot_frame = 5  # 5번 프레임에서 수리검 발사
        self.combo3_has_shot = False  # 수리검을 이미 발사했는지
        self.combo3_projectile_directions = 8  # 8방향
        self.combo3_projectile_speed = 600  # 수리검 속도

        # 콤보3 수리검 발사 이펙트 관련 변수
        self.combo3_fx_frame = 0
        self.combo3_fx_frame_timer = 0.0
        self.combo3_fx_frame_speed = 20.0
        self.combo3_fx_total_frames = 4  # 0~3
        self.combo3_show_fx = False  # 이펙트 표시 여부

        # 이미지 로드 (클래스 레벨에서 한 번만)
        if not AttackPattern3Action.combo1_ready_img_seq:
            try:
                # 콤보1 준비 모션 (0~8)
                for i in range(9):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Combo1_Ready{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern3Action.combo1_ready_img_seq.append(img)
                print(f'[Pattern3] 콤보1 준비 모션 이미지 로드 완료: {len(AttackPattern3Action.combo1_ready_img_seq)}개')

                # 콤보1 돌진 모션 (0~6)
                for i in range(7):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Combo1_Attack{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern3Action.combo1_attack_img_seq.append(img)
                print(f'[Pattern3] 콤보1 공격 모션 이미지 로드 완료: {len(AttackPattern3Action.combo1_attack_img_seq)}개')

                # 콤보2 준비 모션 (0~6)
                for i in range(7):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Combo2_Ready{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern3Action.combo2_ready_img_seq.append(img)
                print(f'[Pattern3] 콤보2 준비 모션 이미지 로드 완료: {len(AttackPattern3Action.combo2_ready_img_seq)}개')

                # 콤보2 돌진 Start 모션 (0~3)
                for i in range(4):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Combo2_Attack_Start{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern3Action.combo2_attack_start_img_seq.append(img)
                print(f'[Pattern3] 콤보2 돌진 Start 모션 이미지 로드 완료: {len(AttackPattern3Action.combo2_attack_start_img_seq)}개')

                # 콤보2 돌진 Cycle 모션 (0~3)
                for i in range(4):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Combo2_Attack_Cycle{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern3Action.combo2_attack_cycle_img_seq.append(img)
                print(f'[Pattern3] 콤보2 돌진 Cycle 모션 이미지 로드 완료: {len(AttackPattern3Action.combo2_attack_cycle_img_seq)}개')

                # 콤보3 준비 모션 (0~3)
                for i in range(4):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Combo3_Ready{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern3Action.combo3_ready_img_seq.append(img)
                print(f'[Pattern3] 콤보3 준비 모션 이미지 로드 완료: {len(AttackPattern3Action.combo3_ready_img_seq)}개')

                # 콤보3 수리검 발사 모션 (0~9)
                for i in range(10):
                    img_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/Character/PantherAssassin_Combo3_Attack{i:02d}.png'
                    img = p2.load_image(img_path)
                    AttackPattern3Action.combo3_attack_img_seq.append(img)
                print(f'[Pattern3] 콤보3 공격 모션 이미지 로드 완료: {len(AttackPattern3Action.combo3_attack_img_seq)}개')

                # 콤보3 수리검 발사 이펙트 (0~3) - 대미지 없음
                for i in range(4):
                    fx_path = f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/FX/PantherAssassin_Combo3_Attack_SwingFX{i:02d}.png'
                    fx_img = p2.load_image(fx_path)
                    AttackPattern3Action.combo3_swing_fx_img_seq.append(fx_img)
                print(f'[Pattern3] 콤보3 이펙트 이미지 로드 완료: {len(AttackPattern3Action.combo3_swing_fx_img_seq)}개')

            except FileNotFoundError as e:
                print(f'\033[91m[Pattern3] 이미지 로드 실패: {e}\033[0m')

    def update(self):
        """패턴 3 로직 실행"""
        dt = framework.get_delta_time()

        if self.phase == 0:
            # 초기화: 콤보1 준비 시작
            self.current_combo = 1
            self.combo1_ready_frame = 0
            self.combo1_ready_frame_timer = 0.0
            self.timer = 0.0
            self.phase = 1
            print("[Pattern3] 패턴 시작 - 콤보1 준비 모션 시작!")

        # ==================== 콤보 1 ====================
        elif self.phase == 1:
            # 콤보1 준비 모션 재생
            self.combo1_ready_frame_timer += dt

            if self.combo1_ready_frame_timer >= 1.0 / self.combo1_ready_frame_speed:
                self.combo1_ready_frame += 1
                self.combo1_ready_frame_timer = 0.0

                # 준비 모션 종료
                if self.combo1_ready_frame >= self.combo1_ready_total_frames:
                    # 돌진 준비
                    self._prepare_combo1_dash()
                    self.phase = 2
                    print("[Pattern3] 콤보1 준비 완료 - 돌진 시작!")

        elif self.phase == 2:
            # 콤보1 돌진 공격 실행
            self.timer += dt
            self.combo1_dash_progress = min(1.0, self.timer / self.combo1_dash_duration)

            # 돌진 애니메이션 프레임 업데이트
            self.combo1_dash_frame_timer += dt
            if self.combo1_dash_frame_timer >= 1.0 / self.combo1_dash_frame_speed:
                self.combo1_dash_frame = min(self.combo1_dash_frame + 1, self.combo1_dash_total_frames - 1)
                self.combo1_dash_frame_timer = 0.0

                # 중간 프레임(3번)에서 검격 이펙트 생성
                if self.combo1_dash_frame == 3 and not hasattr(self, 'combo1_blade_effect_spawned'):
                    self._spawn_combo1_blade_swing_effect()
                    self.combo1_blade_effect_spawned = True

            # 선형 보간으로 다음 위치 계산
            next_x = self.combo1_dash_start_x + (self.combo1_dash_target_x - self.combo1_dash_start_x) * self.combo1_dash_progress
            next_y = self.combo1_dash_start_y + (self.combo1_dash_target_y - self.combo1_dash_start_y) * self.combo1_dash_progress

            # 벽 충돌 체크 - 다음 위치가 벽이면 돌진 즉시 종료
            if self._is_position_on_wall(next_x, next_y, check_radius=30):
                print(f"[Pattern3] 콤보1 돌진 중 벽 충돌 감지! 위치: ({int(next_x)}, {int(next_y)}) - 돌진 강제 종료")
                # 현재 위치 유지 (next_x, next_y로 이동하지 않음)

                # combo1_blade_effect_spawned 플래그 초기화
                if hasattr(self, 'combo1_blade_effect_spawned'):
                    delattr(self, 'combo1_blade_effect_spawned')

                # 콤보2 준비로 전환
                self.current_combo = 2
                self.combo2_ready_frame = 0
                self.combo2_ready_frame_timer = 0.0
                self.timer = 0.0
                self.phase = 3
                print("[Pattern3] 벽 충돌로 인한 조기 종료 - 콤보2 준비 시작!")
                return BehaviorTree.RUNNING
            else:
                # 벽이 아니면 위치 업데이트
                self.panther.x = next_x
                self.panther.y = next_y

            # 돌진 종료 (정상 완료)
            if self.combo1_dash_progress >= 1.0:
                # combo1_blade_effect_spawned 플래그 초기화
                if hasattr(self, 'combo1_blade_effect_spawned'):
                    delattr(self, 'combo1_blade_effect_spawned')

                # 콤보2 준비로 전환
                self.current_combo = 2
                self.combo2_ready_frame = 0
                self.combo2_ready_frame_timer = 0.0
                self.timer = 0.0
                self.phase = 3
                print("[Pattern3] 콤보1 완료 - 콤보2 준비 시작!")

        # ==================== 콤보 2 ====================
        elif self.phase == 3:
            # 콤보2 준비 모션 재생
            self.combo2_ready_frame_timer += dt

            if self.combo2_ready_frame_timer >= 1.0 / self.combo2_ready_frame_speed:
                self.combo2_ready_frame += 1
                self.combo2_ready_frame_timer = 0.0

                # 준비 모션 종료
                if self.combo2_ready_frame >= self.combo2_ready_total_frames:
                    # 돌진 준비
                    self._prepare_combo2_dash()
                    self.phase = 4
                    print("[Pattern3] 콤보2 준비 완료 - 돌진 시작!")

        elif self.phase == 4:
            # 콤보2 돌진 공격 실행
            self.timer += dt
            self.combo2_dash_progress = min(1.0, self.timer / self.combo2_dash_duration)

            # 돌진 애니메이션 프레임 업데이트
            self.combo2_dash_frame_timer += dt
            if self.combo2_dash_frame_timer >= 1.0 / self.combo2_dash_frame_speed:
                self.combo2_dash_frame += 1
                self.combo2_dash_frame_timer = 0.0

                # Start 모션 종료 후 Cycle 모션으로 전환
                if not self.combo2_in_cycle and self.combo2_dash_frame >= self.combo2_dash_start_total_frames:
                    self.combo2_in_cycle = True
                    self.combo2_dash_frame = 0
                    print("[Pattern3] 콤보2 Start -> Cycle 전환")

                # Cycle 모션 루프
                if self.combo2_in_cycle and self.combo2_dash_frame >= self.combo2_dash_cycle_total_frames:
                    self.combo2_dash_frame = 0

                # Start 모션 2번 프레임 또는 Cycle 진입 시 검격 이펙트 생성
                if ((not self.combo2_in_cycle and self.combo2_dash_frame == 2) or
                    (self.combo2_in_cycle and self.combo2_dash_frame == 0)) and not hasattr(self, 'combo2_blade_effect_spawned'):
                    self._spawn_combo2_blade_swing_effect()
                    self.combo2_blade_effect_spawned = True

            # 선형 보간으로 다음 위치 계산
            next_x = self.combo2_dash_start_x + (self.combo2_dash_target_x - self.combo2_dash_start_x) * self.combo2_dash_progress
            next_y = self.combo2_dash_start_y + (self.combo2_dash_target_y - self.combo2_dash_start_y) * self.combo2_dash_progress

            # 벽 충돌 체크 - 다음 위치가 벽이면 돌진 즉시 종료
            if self._is_position_on_wall(next_x, next_y, check_radius=30):
                print(f"[Pattern3] 콤보2 돌진 중 벽 충돌 감지! 위치: ({int(next_x)}, {int(next_y)}) - 돌진 강제 종료")
                # combo2_blade_effect_spawned 플래그 초기화
                if hasattr(self, 'combo2_blade_effect_spawned'):
                    delattr(self, 'combo2_blade_effect_spawned')

                # 콤보3 준비로 전환
                self.current_combo = 3
                self.combo3_ready_frame = 0
                self.combo3_ready_frame_timer = 0.0
                self.combo2_in_cycle = False  # Cycle 플래그 초기화
                self.timer = 0.0
                self.phase = 5
                print("[Pattern3] 벽 충돌로 인한 조기 종료 - 콤보3 준비 시작!")
            else:
                # 벽이 아니면 위치 업데이트
                self.panther.x = next_x
                self.panther.y = next_y

            # 돌진 종료 (정상 완료)
            if self.combo2_dash_progress >= 1.0 and self.phase == 4:  # phase 체크 추가 (벽 충돌로 이미 종료되지 않은 경우만)
                # combo2_blade_effect_spawned 플래그 초기화
                if hasattr(self, 'combo2_blade_effect_spawned'):
                    delattr(self, 'combo2_blade_effect_spawned')

                # 콤보3 준비로 전환
                self.current_combo = 3
                self.combo3_ready_frame = 0
                self.combo3_ready_frame_timer = 0.0
                self.combo2_in_cycle = False  # Cycle 플래그 초기화
                self.timer = 0.0
                self.phase = 5
                print("[Pattern3] 콤보2 완료 - 콤보3 준비 시작!")

        # ==================== 콤보 3 ====================
        elif self.phase == 5:
            # 콤보3 준비 모션 재생
            self.combo3_ready_frame_timer += dt

            if self.combo3_ready_frame_timer >= 1.0 / self.combo3_ready_frame_speed:
                self.combo3_ready_frame += 1
                self.combo3_ready_frame_timer = 0.0

                # 준비 모션 종료
                if self.combo3_ready_frame >= self.combo3_ready_total_frames:
                    # 수리검 발사 공격 시작
                    self.combo3_attack_frame = 0
                    self.combo3_attack_frame_timer = 0.0
                    self.combo3_has_shot = False
                    self.combo3_show_fx = False
                    self.combo3_fx_frame = 0
                    self.combo3_fx_frame_timer = 0.0
                    self.phase = 6
                    print("[Pattern3] 콤보3 준비 완료 - 수리검 발사 시작!")

        elif self.phase == 6:
            # 콤보3 수리검 발사 모션 재생
            self.combo3_attack_frame_timer += dt

            if self.combo3_attack_frame_timer >= 1.0 / self.combo3_attack_frame_speed:
                self.combo3_attack_frame += 1
                self.combo3_attack_frame_timer = 0.0

                # 5번 프레임에서 수리검 발사
                if self.combo3_attack_frame == self.combo3_shoot_frame and not self.combo3_has_shot:
                    self._shoot_combo3_shurikens()
                    self.combo3_has_shot = True
                    self.combo3_show_fx = True  # 이펙트 표시 시작
                    print("[Pattern3] 콤보3 수리검 8방향 발사!")

                # 공격 모션 종료
                if self.combo3_attack_frame >= self.combo3_attack_total_frames:
                    # 패턴 완료
                    self.phase = 0
                    self.panther.attack_timer = self.panther.attack_cooldown
                    print("[Pattern3] 패턴 완료 - 3단 콤보 종료!")
                    return BehaviorTree.SUCCESS

            # 이펙트 애니메이션 업데이트 (수리검 발사 후)
            if self.combo3_show_fx:
                self.combo3_fx_frame_timer += dt
                if self.combo3_fx_frame_timer >= 1.0 / self.combo3_fx_frame_speed:
                    self.combo3_fx_frame += 1
                    self.combo3_fx_frame_timer = 0.0

                    # 이펙트 종료
                    if self.combo3_fx_frame >= self.combo3_fx_total_frames:
                        self.combo3_show_fx = False

        return BehaviorTree.RUNNING

    def _prepare_combo1_dash(self):
        """콤보1 돌진 준비: 시작 위치와 목표 위치 계산"""
        self.combo1_dash_start_x = self.panther.x
        self.combo1_dash_start_y = self.panther.y

        if not self.panther.target:
            # 타겟이 없으면 현재 위치에서 랜덤 방향으로 돌진
            angle = random.uniform(0, 360)
            rad = math.radians(angle)
            distance = 200
            self.combo1_dash_target_x = self.panther.x + math.cos(rad) * distance
            self.combo1_dash_target_y = self.panther.y + math.sin(rad) * distance
        else:
            # 플레이어까지의 거리의 1배 지점으로 돌진
            dx = self.panther.target.x - self.panther.x
            dy = self.panther.target.y - self.panther.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                # 정규화된 방향 벡터
                dir_x = dx / distance
                dir_y = dy / distance

                # 1배 거리
                dash_distance = distance * self.combo1_dash_distance_multiplier
                self.combo1_dash_target_x = self.panther.x + dir_x * dash_distance
                self.combo1_dash_target_y = self.panther.y + dir_y * dash_distance

                # 좌우 반전 결정 (왼쪽으로 이동하면 반전)
                self.combo1_flip_x = (dx < 0)
            else:
                # 플레이어와 같은 위치면 랜덤 방향으로
                angle = random.uniform(0, 360)
                rad = math.radians(angle)
                self.combo1_dash_target_x = self.panther.x + math.cos(rad) * 200
                self.combo1_dash_target_y = self.panther.y + math.sin(rad) * 200
                self.combo1_flip_x = False

        # 돌진 변수 초기화
        self.combo1_dash_progress = 0.0
        self.combo1_dash_frame = 0
        self.combo1_dash_frame_timer = 0.0
        self.timer = 0.0

    def _spawn_combo1_blade_swing_effect(self):
        """콤보1 검격 이펙트 생성 - 종베기 참격"""
        if not self.panther.world or 'effects_front' not in self.panther.world:
            print("[Pattern3] world 또는 effects_front가 없어서 콤보1 검격 이펙트 생성 실패")
            return

        try:
            # 검격 이펙트 위치 계산 (보스 앞쪽)
            dash_dx = self.combo1_dash_target_x - self.combo1_dash_start_x
            dash_dy = self.combo1_dash_target_y - self.combo1_dash_start_y
            dash_distance = math.sqrt(dash_dx**2 + dash_dy**2)

            if dash_distance > 0:
                direction_x = dash_dx / dash_distance
                direction_y = dash_dy / dash_distance
            else:
                direction_x = 1.0
                direction_y = 0.0

            # 검격 이펙트 위치 (보스 앞쪽 60픽셀)
            offset_distance = 60
            effect_x = self.panther.x + direction_x * offset_distance
            effect_y = self.panther.y + direction_y * offset_distance

            # 검격 방향 각도 계산 (라디안)
            effect_angle = math.atan2(direction_y, direction_x)

            # PantherCombo1SwingEffect 생성
            blade_effect = PantherCombo1SwingEffect(
                effect_x,
                effect_y,
                effect_angle,
                owner=self.panther,
                scale=4.0,
                damage=25.0  # 콤보1 검격 데미지
            )

            self.panther.world['effects_front'].append(blade_effect)
            print(f"[Pattern3] 콤보1 검격 이펙트 생성 완료: ({int(effect_x)}, {int(effect_y)}), 각도: {math.degrees(effect_angle):.1f}도")

        except Exception as e:
            print(f'\033[91m[Pattern3] 콤보1 검격 이펙트 생성 실패: {e}\033[0m')

    def _prepare_combo2_dash(self):
        """콤보2 돌진 준비: 시작 위치와 목표 위치 계산"""
        self.combo2_dash_start_x = self.panther.x
        self.combo2_dash_start_y = self.panther.y

        if not self.panther.target:
            # 타겟이 없으면 현재 위치에서 랜덤 방향으로 돌진
            angle = random.uniform(0, 360)
            rad = math.radians(angle)
            distance = 300
            self.combo2_dash_target_x = self.panther.x + math.cos(rad) * distance
            self.combo2_dash_target_y = self.panther.y + math.sin(rad) * distance
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
                dash_distance = distance * self.combo2_dash_distance_multiplier
                self.combo2_dash_target_x = self.panther.x + dir_x * dash_distance
                self.combo2_dash_target_y = self.panther.y + dir_y * dash_distance

                # 좌우 반전 결정 (왼쪽으로 이동하면 반전)
                self.combo2_flip_x = (dx < 0)
            else:
                # 플레이어와 같은 위치면 랜덤 방향으로
                angle = random.uniform(0, 360)
                rad = math.radians(angle)
                self.combo2_dash_target_x = self.panther.x + math.cos(rad) * 300
                self.combo2_dash_target_y = self.panther.y + math.sin(rad) * 300
                self.combo2_flip_x = False

        # 돌진 변수 초기화
        self.combo2_dash_progress = 0.0
        self.combo2_dash_frame = 0
        self.combo2_dash_frame_timer = 0.0
        self.combo2_in_cycle = False
        self.timer = 0.0

    def _spawn_combo2_blade_swing_effect(self):
        """콤보2 검격 이펙트 생성 - 횡베기 참격"""
        if not self.panther.world or 'effects_front' not in self.panther.world:
            print("[Pattern3] world 또는 effects_front가 없어서 콤보2 검격 이펙트 생성 실패")
            return

        try:
            # 검격 이펙트 위치 계산 (보스 앞쪽)
            dash_dx = self.combo2_dash_target_x - self.combo2_dash_start_x
            dash_dy = self.combo2_dash_target_y - self.combo2_dash_start_y
            dash_distance = math.sqrt(dash_dx**2 + dash_dy**2)

            if dash_distance > 0:
                direction_x = dash_dx / dash_distance
                direction_y = dash_dy / dash_distance
            else:
                direction_x = 1.0
                direction_y = 0.0

            # 검격 이펙트 위치 (보스 앞쪽 60픽셀)
            offset_distance = 60
            effect_x = self.panther.x + direction_x * offset_distance
            effect_y = self.panther.y + direction_y * offset_distance

            # 검격 방향 각도 계산 (라디안)
            effect_angle = math.atan2(direction_y, direction_x)

            # PantherCombo2SwingEffect 생성
            blade_effect = PantherCombo2SwingEffect(
                effect_x,
                effect_y,
                effect_angle,
                owner=self.panther,
                scale=4.0,
                damage=30.0  # 콤보2 검격 데미지
            )

            self.panther.world['effects_front'].append(blade_effect)
            print(f"[Pattern3] 콤보2 검격 이펙트 생성 완료: ({int(effect_x)}, {int(effect_y)}), 각도: {math.degrees(effect_angle):.1f}도")

        except Exception as e:
            print(f'\033[91m[Pattern3] 콤보2 검격 이펙트 생성 실패: {e}\033[0m')

    def _shoot_combo3_shurikens(self):
        """콤보3 수리검 8방향 발사"""
        if not self.panther.world or 'effects_front' not in self.panther.world:
            print("[Pattern3] world가 없어서 수리검 발사 실패")
            return

        # 8방향으로 수리검 발사
        for i in range(self.combo3_projectile_directions):
            # 360도를 8개로 나누어 각도 계산
            angle = (360 / self.combo3_projectile_directions) * i
            rad = math.radians(angle)

            # 수리검의 목표 지점 계산 (멀리 날아가도록)
            distance = 1000  # 충분히 먼 거리
            target_x = self.panther.x + math.cos(rad) * distance
            target_y = self.panther.y + math.sin(rad) * distance

            # 수리검 생성
            from ..panther_assassin import PantherShuriken
            shuriken = PantherShuriken(
                self.panther.x,
                self.panther.y,
                target_x,
                target_y,
                speed=self.combo3_projectile_speed,
                from_player=False,
                damage=20,
                scale=2.5
            )

            # world의 effects_front 레이어에 추가
            self.panther.world['effects_front'].append(shuriken)
            print(f"[Pattern3] 콤보3 수리검 발사: 각도 {angle:.0f}도")

    def _is_position_on_wall(self, x, y, check_radius=30):
        """
        주어진 위치가 벽 위에 있는지 확인
        Args:
            x: 월드 x 좌표
            y: 월드 y 좌표
            check_radius: 체크할 반경 (보스의 크기 고려)
        Returns:
            bool: 벽 위에 있으면 True, 아니면 False
        """
        if not self.panther.world or 'walls' not in self.panther.world:
            return False

        walls = self.panther.world['walls']
        for wall in walls:
            # 벽과의 충돌 체크 (보스의 크기를 고려하여 check_radius만큼 여유 공간 확보)
            if (wall.x - wall.w/2 - check_radius < x < wall.x + wall.w/2 + check_radius and
                wall.y - wall.h/2 - check_radius < y < wall.y + wall.h/2 + check_radius):
                return True
        return False

    def draw(self, draw_x, draw_y):
        """
        패턴 3 시각 효과 드로잉

        Args:
            draw_x, draw_y: 보스의 현재 위치 (카메라 좌표계)
        """
        # ==================== 콤보 1 ====================
        # Phase 1: 콤보1 준비 모션
        if self.phase == 1:
            if AttackPattern3Action.combo1_ready_img_seq and self.combo1_ready_frame < len(AttackPattern3Action.combo1_ready_img_seq):
                img = AttackPattern3Action.combo1_ready_img_seq[self.combo1_ready_frame]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

        # Phase 2: 콤보1 돌진 공격
        elif self.phase == 2:
            if AttackPattern3Action.combo1_attack_img_seq and self.combo1_dash_frame < len(AttackPattern3Action.combo1_attack_img_seq):
                img = AttackPattern3Action.combo1_attack_img_seq[self.combo1_dash_frame]
                if img:
                    # 좌우 반전 적용
                    flip = 'h' if self.combo1_flip_x else ''
                    if flip:
                        img.composite_draw(0, flip, draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)
                    else:
                        img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

        # ==================== 콤보 2 ====================
        # Phase 3: 콤보2 준비 모션
        elif self.phase == 3:
            if AttackPattern3Action.combo2_ready_img_seq and self.combo2_ready_frame < len(AttackPattern3Action.combo2_ready_img_seq):
                img = AttackPattern3Action.combo2_ready_img_seq[self.combo2_ready_frame]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

        # Phase 4: 콤보2 돌진 공격 (Start 또는 Cycle)
        elif self.phase == 4:
            if not self.combo2_in_cycle:
                # Start 모션
                if AttackPattern3Action.combo2_attack_start_img_seq and self.combo2_dash_frame < len(AttackPattern3Action.combo2_attack_start_img_seq):
                    img = AttackPattern3Action.combo2_attack_start_img_seq[self.combo2_dash_frame]
                    if img:
                        # 좌우 반전 적용
                        flip = 'h' if self.combo2_flip_x else ''
                        if flip:
                            img.composite_draw(0, flip, draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)
                        else:
                            img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)
            else:
                # Cycle 모션
                if AttackPattern3Action.combo2_attack_cycle_img_seq and self.combo2_dash_frame < len(AttackPattern3Action.combo2_attack_cycle_img_seq):
                    img = AttackPattern3Action.combo2_attack_cycle_img_seq[self.combo2_dash_frame]
                    if img:
                        # 좌우 반전 적용
                        flip = 'h' if self.combo2_flip_x else ''
                        if flip:
                            img.composite_draw(0, flip, draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)
                        else:
                            img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

        # ==================== 콤보 3 ====================
        # Phase 5: 콤보3 준비 모션
        elif self.phase == 5:
            if AttackPattern3Action.combo3_ready_img_seq and self.combo3_ready_frame < len(AttackPattern3Action.combo3_ready_img_seq):
                img = AttackPattern3Action.combo3_ready_img_seq[self.combo3_ready_frame]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

        # Phase 6: 콤보3 수리검 발사 모션
        elif self.phase == 6:
            # 공격 모션 그리기
            if AttackPattern3Action.combo3_attack_img_seq and self.combo3_attack_frame < len(AttackPattern3Action.combo3_attack_img_seq):
                img = AttackPattern3Action.combo3_attack_img_seq[self.combo3_attack_frame]
                if img:
                    img.draw(draw_x, draw_y, img.w * self.panther.scale_factor, img.h * self.panther.scale_factor)

            # 수리검 발사 이펙트 그리기 (대미지 없음, 시각 효과용)
            if self.combo3_show_fx and AttackPattern3Action.combo3_swing_fx_img_seq:
                if self.combo3_fx_frame < len(AttackPattern3Action.combo3_swing_fx_img_seq):
                    fx_img = AttackPattern3Action.combo3_swing_fx_img_seq[self.combo3_fx_frame]
                    if fx_img:
                        # 이펙트는 캐릭터와 같은 위치에 출력
                        fx_img.draw(draw_x, draw_y, fx_img.w * self.panther.scale_factor, fx_img.h * self.panther.scale_factor)


# ==================== PantherCombo1SwingEffect 검격 이펙트 클래스 (콤보1용) ====================

class PantherCombo1SwingEffect:
    """
    Panther Assassin의 콤보1 검격 이펙트 (PantherAssassin_Combo1_Attack_SwingFX 0~3)
    패턴3의 콤보1 종베기 공격 시 플레이어에게 피해를 주는 이펙트
    """
    images = None

    def __init__(self, x, y, angle, owner=None, scale=4.0, damage=25.0):
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
        if PantherCombo1SwingEffect.images is None:
            PantherCombo1SwingEffect.images = []
            try:
                for i in range(4):  # PantherAssassin_Combo1_Attack_SwingFX0 ~ SwingFX3
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/FX/PantherAssassin_Combo1_Attack_SwingFX{i:02d}.png')
                    PantherCombo1SwingEffect.images.append(img)
                print(f"[PantherCombo1SwingEffect] 이미지 로드 완료: {len(PantherCombo1SwingEffect.images)}개")
            except Exception as e:
                print(f"\033[91m[PantherCombo1SwingEffect] 이미지 로드 실패: {e}\033[0m")
                PantherCombo1SwingEffect.images = []

        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 20  # 빠른 애니메이션 (20 FPS)
        self.finished = False

        # 충돌 체크용 변수
        self.has_hit_player = False  # 플레이어를 이미 맞췄는지 여부

        print(f"[PantherCombo1SwingEffect] 생성됨 at ({int(x)}, {int(y)}), 각도: {math.degrees(angle):.1f}도, 크기: {scale}, 데미지: {damage}")

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
            print(f"[PantherCombo1SwingEffect] 프레임 업데이트: {self.frame}/{len(PantherCombo1SwingEffect.images) if PantherCombo1SwingEffect.images else 0}")

            # 애니메이션이 끝나면 제거
            if PantherCombo1SwingEffect.images and self.frame >= len(PantherCombo1SwingEffect.images):
                self.finished = True
                print(f"[PantherCombo1SwingEffect] 애니메이션 완료 - 제거")
                return False

        return True

    def get_collision_box(self):
        """충돌 박스 크기 반환 (play_mode에서 충돌 검사에 사용)

        Returns:
            tuple: (width, height) - 이펙트의 충돌 박스 크기
        """
        if PantherCombo1SwingEffect.images and len(PantherCombo1SwingEffect.images) > 0:
            effect_img = PantherCombo1SwingEffect.images[min(self.frame, len(PantherCombo1SwingEffect.images) - 1)]
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
        if not PantherCombo1SwingEffect.images or len(PantherCombo1SwingEffect.images) == 0:
            print(f"[PantherCombo1SwingEffect] 이미지 없음 - 그리기 실패")
            return

        if self.finished:
            return

        frame_idx = min(self.frame, len(PantherCombo1SwingEffect.images) - 1)
        try:
            # 회전 각도를 degree로 변환 (pico2d는 degree 사용)
            # 기본 이미지가 오른쪽 방향이므로 각도 보정
            angle_deg = math.degrees(self.angle)

            # 이미지 그리기 (회전 적용)
            PantherCombo1SwingEffect.images[frame_idx].composite_draw(
                angle_deg, '',  # 각도, 플립 없음
                draw_x, draw_y,
                PantherCombo1SwingEffect.images[frame_idx].w * self.scale,
                PantherCombo1SwingEffect.images[frame_idx].h * self.scale
            )

            # DEBUG: 검격 이펙트 그리기 확인 (첫 프레임만)
            if self.frame == 0:
                print(f"[PantherCombo1SwingEffect] 첫 프레임 그리기: 화면좌표({int(draw_x)}, {int(draw_y)}), 월드좌표({int(self.x)}, {int(self.y)}), 각도: {angle_deg:.1f}도")

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
            print(f"\033[91m[PantherCombo1SwingEffect] draw 에러: {e}\033[0m")


# ==================== PantherCombo2SwingEffect 검격 이펙트 클래스 (콤보2용) ====================

class PantherCombo2SwingEffect:
    """
    Panther Assassin의 콤보2 검격 이펙트 (PantherAssassin_Combo2_Attack_SwingFX 0~3)
    패턴3의 콤보2 횡베기 공격 시 플레이어에게 피해를 주는 이펙트
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
        if PantherCombo2SwingEffect.images is None:
            PantherCombo2SwingEffect.images = []
            try:
                for i in range(4):  # PantherAssassin_Combo2_Attack_SwingFX0 ~ SwingFX3
                    img = p2.load_image(f'resources/Texture_organize/Entity/Stage2_Forest_Boss/Panther_Assassin/FX/PantherAssassin_Combo2_Attack_SwingFX{i:02d}.png')
                    PantherCombo2SwingEffect.images.append(img)
                print(f"[PantherCombo2SwingEffect] 이미지 로드 완료: {len(PantherCombo2SwingEffect.images)}개")
            except Exception as e:
                print(f"\033[91m[PantherCombo2SwingEffect] 이미지 로드 실패: {e}\033[0m")
                PantherCombo2SwingEffect.images = []

        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 20  # 빠른 애니메이션 (20 FPS)
        self.finished = False

        # 충돌 체크용 변수
        self.has_hit_player = False  # 플레이어를 이미 맞췄는지 여부

        print(f"[PantherCombo2SwingEffect] 생성됨 at ({int(x)}, {int(y)}), 각도: {math.degrees(angle):.1f}도, 크기: {scale}, 데미지: {damage}")

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
            print(f"[PantherCombo2SwingEffect] 프레임 업데이트: {self.frame}/{len(PantherCombo2SwingEffect.images) if PantherCombo2SwingEffect.images else 0}")

            # 애니메이션이 끝나면 제거
            if PantherCombo2SwingEffect.images and self.frame >= len(PantherCombo2SwingEffect.images):
                self.finished = True
                print(f"[PantherCombo2SwingEffect] 애니메이션 완료 - 제거")
                return False

        return True

    def get_collision_box(self):
        """충돌 박스 크기 반환 (play_mode에서 충돌 검사에 사용)

        Returns:
            tuple: (width, height) - 이펙트의 충돌 박스 크기
        """
        if PantherCombo2SwingEffect.images and len(PantherCombo2SwingEffect.images) > 0:
            effect_img = PantherCombo2SwingEffect.images[min(self.frame, len(PantherCombo2SwingEffect.images) - 1)]
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
        if not PantherCombo2SwingEffect.images or len(PantherCombo2SwingEffect.images) == 0:
            print(f"[PantherCombo2SwingEffect] 이미지 없음 - 그리기 실패")
            return

        if self.finished:
            return

        frame_idx = min(self.frame, len(PantherCombo2SwingEffect.images) - 1)
        try:
            # 회전 각도를 degree로 변환 (pico2d는 degree 사용)
            # 기본 이미지가 오른쪽 방향이므로 각도 보정
            angle_deg = math.degrees(self.angle)

            # 이미지 그리기 (회전 적용)
            PantherCombo2SwingEffect.images[frame_idx].composite_draw(
                angle_deg, '',  # 각도, 플립 없음
                draw_x, draw_y,
                PantherCombo2SwingEffect.images[frame_idx].w * self.scale,
                PantherCombo2SwingEffect.images[frame_idx].h * self.scale
            )

            # DEBUG: 검격 이펙트 그리기 확인 (첫 프레임만)
            if self.frame == 0:
                print(f"[PantherCombo2SwingEffect] 첫 프레임 그리기: 화면좌표({int(draw_x)}, {int(draw_y)}), 월드좌표({int(self.x)}, {int(self.y)}), 각도: {angle_deg:.1f}도")

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
            print(f"\033[91m[PantherCombo2SwingEffect] draw 에러: {e}\033[0m")
