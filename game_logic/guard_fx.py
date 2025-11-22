"""
방패 방어 이펙트 (Guard FX)
"""
import pico2d as p2
from . import framework


class GuardFX:
    """방패 방어 성공 시 표시되는 이펙트"""
    images = None

    def __init__(self, x, y, scale=3.0):
        # 월드 좌표 저장 (카메라 적용 전 좌표)
        self.x = x
        self.y = y
        self.scale = scale

        # 이미지 로드 (클래스 변수로 한 번만 로드)
        if GuardFX.images is None:
            GuardFX.images = []
            try:
                for i in range(5):  # GuardFX1_0.png ~ GuardFX1_4.png
                    img = p2.load_image(f'resources/Texture_organize/Weapon/SwordANDShield/Guard_FX/GuardFX1_{i}.png')
                    GuardFX.images.append(img)
                print(f"[GuardFX] Loaded {len(GuardFX.images)} images")
            except Exception as e:
                print(f"[GuardFX] Failed to load images: {e}")
                GuardFX.images = []

        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 20  # 빠르게 재생 (20 FPS)
        self.finished = False

        print(f"[GuardFX] 생성됨 at world({int(x)}, {int(y)}), 총 프레임: {len(GuardFX.images) if GuardFX.images else 0}")

    def update(self):
        """이펙트 애니메이션 업데이트"""
        if self.finished:
            print("[GuardFX] 애니메이션 완료, 제거됨")
            return False

        dt = framework.get_delta_time()
        self.animation_time += dt

        if self.animation_time >= 1.0 / self.animation_speed:
            self.frame += 1
            self.animation_time = 0

            print(f"[GuardFX] 프레임 업데이트: {self.frame}/{len(GuardFX.images) if GuardFX.images else 0}")

            # 애니메이션이 끝나면 제거
            if GuardFX.images and self.frame >= len(GuardFX.images):
                self.finished = True
                print("[GuardFX] 애니메이션 완료")
                return False

        return True

    def draw(self, draw_x, draw_y):
        """
        이펙트 그리기

        Args:
            draw_x: 카메라가 적용된 화면 X 좌표
            draw_y: 카메라가 적용된 화면 Y 좌표
        """
        if not GuardFX.images or len(GuardFX.images) == 0:
            print("[GuardFX] 이미지가 없음!")
            return

        if self.finished:
            return

        frame_idx = min(self.frame, len(GuardFX.images) - 1)
        try:
            # 카메라가 적용된 좌표(draw_x, draw_y)를 사용하여 그리기
            GuardFX.images[frame_idx].draw(
                draw_x, draw_y,
                GuardFX.images[frame_idx].w * self.scale,
                GuardFX.images[frame_idx].h * self.scale
            )
        except Exception as e:
            print(f"[GuardFX] draw 에러: {e}")
