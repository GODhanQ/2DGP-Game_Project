import os
from pico2d import load_image
import pico2d as p2
import game_framework

class AnimatedVFX:
    """간단한 프레임 애니메이션 VFX 엔티티
    - folder: 폴더 경로 (예: resources/Texture_organize/VFX/Potion_Common)
    - prefix: 파일명 접두사 (예: 'Potion_Back_FX')
    - frames: 프레임 수
    - frame_time: 각 프레임 지속 시간
    - x,y: 위치
    - scale: 크기 배율
    """
    def __init__(self, folder, prefix, frames, frame_time, x, y, scale=1.0, life=None):
        self.folder = folder
        self.prefix = prefix
        self.frames_count = frames
        self.frame_time = frame_time
        self.x = x
        self.y = y
        self.scale = scale
        self.images = []
        self.frame = 0
        self.acc = 0.0
        self.life = life if life is not None else frames * frame_time
        self._load_frames()

    def _load_frames(self):
        self.images = []
        for i in range(self.frames_count):
            name1 = f"{self.prefix}{i:02d}.png"
            path = os.path.join(self.folder, name1)
            try:
                img = load_image(path)
                self.images.append(img)
            except Exception:
                # 로드 실패하면 다음 프레임도 시도하지만 중단
                print(f'\033[91m[AnimatedVFX] Failed to load frame: {path}\033[0m')
                break
        # fallback: 만약 아무 프레임도 로드되지 않으면 try single file without index
        if not self.images:
            single = os.path.join(self.folder, f"{self.prefix}.png")
            try:
                img = load_image(single)
                self.images.append(img)
            except Exception:
                print(f'\033[91m[AnimatedVFX] Failed to load single image: {single}\033[0m')
        # adjust frames_count to actual loaded
        self.frames_count = len(self.images)

    def update(self, dt=None):
        # dt None이면 framework에서 값을 가져옴 (main.update_world가 인자로 주지 않으므로)
        if dt is None:
            dt = game_framework.get_delta_time()
        if self.life <= 0:
            return False
        self.life -= dt
        if self.frames_count == 0:
            return self.life > 0
        self.acc += dt
        while self.acc >= self.frame_time and self.frame < self.frames_count - 1:
            self.acc -= self.frame_time
            self.frame += 1
        return self.life > 0

    def draw(self, draw_x, draw_y):
        if self.images and 0 <= self.frame < len(self.images):
            img = self.images[self.frame]
            img.draw(draw_x, draw_y, img.w * self.scale, img.h * self.scale)


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
                print(f"\033[91m[GuardFX] Failed to load images: {e}\033[0m")
                GuardFX.images = []

        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 20  # 빠르게 재생 (20 FPS)
        self.finished = False

        print(f"[GuardFX] 생성됨 at world({int(x)}, {int(y)}), 총 프레임: {len(GuardFX.images) if GuardFX.images else 0}")

    def update(self):
        """이펙트 애니메이션 업데이트"""
        if self.finished:
            return False

        dt = game_framework.get_delta_time()
        self.animation_time += dt

        if self.animation_time >= 1.0 / self.animation_speed:
            self.frame += 1
            self.animation_time = 0

            # 애니메이션이 끝나면 제거
            if GuardFX.images and self.frame >= len(GuardFX.images):
                self.finished = True
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
            print(f"\033[91m[GuardFX] draw 에러: {e}\033[0m")


class ShieldCrashEffect:
    """방패가 깨질 때 표시되는 이펙트 (Crash_Blue)"""
    front_images = None
    back_images = None

    def __init__(self, x, y, scale=3.0):
        # 월드 좌표 저장 (카메라 적용 전 좌표)
        self.x = x
        self.y = y
        self.scale = scale

        # 이미지 로드 (클래스 변수로 한 번만 로드)
        if ShieldCrashEffect.front_images is None:
            ShieldCrashEffect.front_images = []
            try:
                for i in range(11):  # Crash_Blue_Front_FX00 ~ FX10 (0~10)
                    img = p2.load_image(f'resources/Texture_organize/VFX/Crash_Effect/Crash_Blue_Front_FX0{i}.png')
                    ShieldCrashEffect.front_images.append(img)
                print(f"[ShieldCrashEffect] Loaded {len(ShieldCrashEffect.front_images)} front images")
            except Exception as e:
                print(f"\033[91m[ShieldCrashEffect] Failed to load front images: {e}\033[0m")
                ShieldCrashEffect.front_images = []

        if ShieldCrashEffect.back_images is None:
            ShieldCrashEffect.back_images = []
            try:
                for i in range(3, 9):  # Crash_Blue_Back_FX03 ~ FX08 (3~8)
                    img = p2.load_image(f'resources/Texture_organize/VFX/Crash_Effect/Crash_Blue_Back_FX0{i}.png')
                    ShieldCrashEffect.back_images.append(img)
                print(f"[ShieldCrashEffect] Loaded {len(ShieldCrashEffect.back_images)} back images")
            except Exception as e:
                print(f"\033[91m[ShieldCrashEffect] Failed to load back images: {e}\033[0m")
                ShieldCrashEffect.back_images = []

        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 20  # 빠른 애니메이션 (20 FPS)
        self.finished = False

        print(f"[ShieldCrashEffect] 생성됨 at world({int(x)}, {int(y)})")

    def update(self):
        """이펙트 애니메이션 업데이트"""
        if self.finished:
            return False

        dt = game_framework.get_delta_time()
        self.animation_time += dt

        if self.animation_time >= 1.0 / self.animation_speed:
            self.frame += 1
            self.animation_time = 0

            # Front 이미지 기준으로 애니메이션이 끝나면 제거
            if ShieldCrashEffect.front_images and self.frame >= len(ShieldCrashEffect.front_images):
                self.finished = True
                return False

        return True

    def draw(self, draw_x, draw_y):
        """
        이펙트 그리기 (Front와 Back을 레이어링)

        Args:
            draw_x: 카메라가 적용된 화면 X 좌표
            draw_y: 카메라가 적용된 화면 Y 좌표
        """
        if self.finished:
            return

        # Front 이미지 그리기 (0~10 프레임)
        if ShieldCrashEffect.front_images and self.frame < len(ShieldCrashEffect.front_images):
            try:
                ShieldCrashEffect.front_images[self.frame].draw(
                    draw_x, draw_y,
                    ShieldCrashEffect.front_images[self.frame].w * self.scale,
                    ShieldCrashEffect.front_images[self.frame].h * self.scale
                )
            except Exception as e:
                print(f"\033[91m[ShieldCrashEffect] front draw 에러: {e}\033[0m")

        # Back 이미지 그리기 (Front 프레임 3부터 시작)
        # Front frame 3 = Back index 0 (Back_FX03)
        # Front frame 4 = Back index 1 (Back_FX04) ...
        if self.frame >= 3:
            back_index = self.frame - 3
            if ShieldCrashEffect.back_images and back_index < len(ShieldCrashEffect.back_images):
                try:
                    ShieldCrashEffect.back_images[back_index].draw(
                        draw_x, draw_y,
                        ShieldCrashEffect.back_images[back_index].w * self.scale,
                        ShieldCrashEffect.back_images[back_index].h * self.scale
                    )
                except Exception as e:
                    print(f"\033[91m[ShieldCrashEffect] back draw 에러: {e}\033[0m")
