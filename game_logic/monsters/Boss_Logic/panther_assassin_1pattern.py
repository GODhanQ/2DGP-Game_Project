import pico2d as p2
from ...behavior_tree import BehaviorTree
import game_framework as framework
import math

class AttackPattern1Action:
    """
    panther_assassin.py의 보스 개체(PantherAssassin)의 공격패턴 1 구현 클래스
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

        # 사운드 로드
        try:
            self.throw_shuriken_sound = p2.load_wav('resources/Sounds/Throw_Shuriken.wav')
            self.throw_shuriken_sound.set_volume(32)  # 볼륨 설정 (0~128)
            print("[Pattern1] Throw_Shuriken.wav 사운드 로드 완료")
        except Exception as e:
            print(f"\033[91m[Pattern1] 사운드 로드 실패: {e}\033[0m")
            self.throw_shuriken_sound = None

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

        # 수리검 투척 사운드 재생
        if self.throw_shuriken_sound:
            self.throw_shuriken_sound.play()

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
            from ..panther_assassin import PantherThrowingStar
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
