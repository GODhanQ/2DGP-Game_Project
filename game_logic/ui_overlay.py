import os
from pico2d import load_image, get_canvas_width, get_canvas_height

class InventoryOverlay:
    """UI 레이어에서 그려지는 인벤토리 오버레이"""
    def __init__(self, player):
        self.player = player
        img_path = os.path.join('resources', 'Texture_organize', 'UI', 'Inventory', 'InventoryBase_New1.png')
        try:
            self.image = load_image(img_path)
        except Exception as ex:
            print('Failed to load inventory image:', img_path, ex)
            self.image = None
        self.scale = 1.0

    def update(self):
        # 오버레이는 별도 업데이트 없음
        pass

    def handle_event(self, event):
        # UI 입력 별도 처리 필요 시 확장
        pass

    def draw(self):
        # 플레이어 인벤토리가 열려 있을 때만 그리기
        if not getattr(self.player, 'inventory_open', False):
            return
        if self.image is None:
            return
        canvas_w = get_canvas_width()
        canvas_h = get_canvas_height()
        target_x = canvas_w * 0.75
        target_y = canvas_h * 0.5
        max_w = canvas_w * 0.5
        max_h = canvas_h * 0.8
        scale_w = max_w / self.image.w
        scale_h = max_h / self.image.h
        self.scale = min(1.0, scale_w, scale_h)
        self.image.clip_composite_draw(
            0, 0, self.image.w, self.image.h,
            0, '',
            target_x, target_y,
            self.image.w * self.scale,
            self.image.h * self.scale
        )
