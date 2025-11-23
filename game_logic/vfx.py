import os
from pico2d import load_image
from . import framework

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
            dt = framework.get_delta_time()
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
