import os
from pico2d import load_image, get_canvas_width, get_canvas_height

class InventoryOverlay:
    """UI 레이어에서 그려지는 인벤토리 오버레이 (배경 + 슬롯 그리드)"""
    def __init__(self, player):
        self.player = player
        # 배경 이미지
        img_path = os.path.join('resources', 'Texture_organize', 'UI', 'Inventory', 'InventoryBase_New1.png')
        try:
            self.image = load_image(img_path)
        except Exception as ex:
            print('Failed to load inventory image:', img_path, ex)
            self.image = None
        self.scale = 1.0

        # 슬롯 이미지 로드
        slot_path = os.path.join('resources', 'Texture_organize', 'UI', 'Inventory', 'InventorySlot_New0.png')
        try:
            self.slot_image = load_image(slot_path)
        except Exception as ex:
            print('Failed to load inventory slot image:', slot_path, ex)
            self.slot_image = None

        # 그리드 설정 (cols x rows)
        self.cols = 6
        self.rows = 5
        # 내부 패딩과 슬롯 간격(기본 px, 배율 적용) - 슬롯을 크게 보이도록 패딩 축소, 간격 제거
        self.pad_x = 8
        self.pad_y = 12
        self.gap_x = 5
        self.gap_y = 0
        # 슬롯 확대 배율 (가로/세로 분리): y만 <1.0으로 두면 세로 압축됨
        self.slot_scale_mult_x = 1.1
        self.slot_scale_mult_y = 0.95

        # 그리드 위치 오프셋(px): 음수면 왼쪽/아래, 양수면 오른쪽/위로 이동 (배경 스케일에 연동)
        self.grid_offset_x = 0
        self.grid_offset_y = -5

        # 계산 캐시
        self._last_layout = None  # (canvas_w, canvas_h, scale) -> layout dict

    def update(self):
        # 오버레이는 별도 업데이트 없음
        pass

    def handle_event(self, event):
        # UI 입력 별도 처리 필요 시 확장 (예: 슬롯 클릭 등)
        pass

    def _compute_layout(self, canvas_w, canvas_h):
        # 배경 목표 위치/배율 계산 (player 인벤토리 열렸을 때와 동일 로직)
        target_x = canvas_w * 0.75
        target_y = canvas_h * 0.5
        max_w = canvas_w * 0.5
        max_h = canvas_h * 0.8
        scale_w = max_w / self.image.w
        scale_h = max_h / self.image.h
        scale = min(1.0, scale_w, scale_h)
        bg_w = self.image.w * scale
        bg_h = self.image.h * scale
        left = target_x - bg_w / 2
        bottom = target_y - bg_h / 2
        right = target_x + bg_w / 2
        top = target_y + bg_h / 2

        # 슬롯 레이아웃 계산
        pad_x = self.pad_x * scale
        pad_y = self.pad_y * scale
        gap_x = self.gap_x * scale
        gap_y = self.gap_y * scale
        grid_left = left + pad_x
        grid_right = right - pad_x
        grid_bottom = bottom + pad_y
        grid_top = top - pad_y
        grid_w = max(0, grid_right - grid_left)
        grid_h = max(0, grid_top - grid_bottom)

        # 슬롯 크기: 가용 영역에 맞추어 정사각형으로 결정
        slot_w = (grid_w - gap_x * (self.cols - 1)) / self.cols if self.cols > 0 else 0
        slot_h = (grid_h - gap_y * (self.rows - 1)) / self.rows if self.rows > 0 else 0
        slot_size = max(1.0, min(slot_w, slot_h))

        # 실제 슬롯 이미지 배율
        slot_scale_x = slot_size / (self.slot_image.w if self.slot_image else slot_size)
        slot_scale_y = slot_size / (self.slot_image.h if self.slot_image else slot_size)
        slot_scale = min(slot_scale_x, slot_scale_y)

        return {
            'target_x': target_x,
            'target_y': target_y,
            'scale': scale,
            'bg_w': bg_w,
            'bg_h': bg_h,
            'grid_left': grid_left,
            'grid_bottom': grid_bottom,
            'slot_size': slot_size,
            'gap_x': gap_x,
            'gap_y': gap_y,
            'slot_scale': slot_scale
        }

    def draw(self):
        # 플레이어 인벤토리가 열려 있을 때만 그리기
        if not getattr(self.player, 'inventory_open', False):
            return
        if self.image is None:
            return
        canvas_w = get_canvas_width()
        canvas_h = get_canvas_height()

        # 레이아웃 계산
        layout = self._compute_layout(canvas_w, canvas_h)
        self.scale = layout['scale']

        # 배경 그리기
        self.image.clip_composite_draw(
            0, 0, self.image.w, self.image.h,
            0, '',
            layout['target_x'], layout['target_y'],
            layout['bg_w'], layout['bg_h']
        )

        # 슬롯 그리드 그리기
        if self.slot_image is None:
            return
        # 기본 계산된 슬롯 크기
        base_slot_draw_w = self.slot_image.w * layout['slot_scale']
        base_slot_draw_h = self.slot_image.h * layout['slot_scale']
        # 가로/세로 배율 각각 적용 (Y축 압축은 slot_scale_mult_y < 1.0)
        slot_draw_w = base_slot_draw_w * getattr(self, 'slot_scale_mult_x', 1.0)
        slot_draw_h = base_slot_draw_h * getattr(self, 'slot_scale_mult_y', 1.0)

        # 배경 중심 기준 + 오프셋 적용
        total_w = self.cols * slot_draw_w
        total_h = self.rows * slot_draw_h
        grid_left_centered = layout['target_x'] - total_w / 2
        grid_bottom_centered = layout['target_y'] - total_h / 2
        # 오프셋(px)을 배경 스케일에 맞춰 적용
        grid_left_centered += self.grid_offset_x * layout['scale']
        grid_bottom_centered += self.grid_offset_y * layout['scale']

        for r in range(self.rows):
            for c in range(self.cols):
                cx = grid_left_centered + c * slot_draw_w + slot_draw_w / 2
                cy = grid_bottom_centered + r * slot_draw_h + slot_draw_h / 2
                self.slot_image.draw(cx, cy, slot_draw_w, slot_draw_h)
