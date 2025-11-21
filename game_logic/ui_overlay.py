import os
import ctypes
from pico2d import load_image, get_canvas_width, get_canvas_height, load_font
from sdl2 import SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT, SDL_MOUSEMOTION, SDL_MOUSEBUTTONUP, SDL_GetMouseState, SDL_KEYDOWN, SDLK_F5, SDLK_F6
from .inventory import Item

class InventoryOverlay:
    """UI 레이어에서 그려지는 인벤토리 오버레이 (배경 + 슬롯 그리드 + 아이템 아이콘 + 드래그)
    이제 main에서 생성할 때 world 레퍼런스를 전달하도록 권장합니다: InventoryOverlay(player, world)
    """
    def __init__(self, player, world=None):
        self.player = player
        # 외부에서 주입된 world 딕셔너리(권장)
        self.world = world

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

        # 수량 텍스트용 폰트 (동적 크기 캐시)
        self._font = None
        self._font_size = None
        self._font_loaded = False

        # 그리드 설정 (플레이어 인벤토리 크기에 동기화)
        self.cols = getattr(self.player.inventory, 'cols', 6)
        self.rows = getattr(self.player.inventory, 'rows', 5)
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

        # 드래그 상태
        self.dragging = False
        self.drag_from = None  # (r,c)
        self.drag_icon = None
        self.drag_qty = 0
        self.drag_mouse = (0, 0)

        # 계산 캐시
        self._last_layout = None  # (canvas_w, canvas_h, scale) -> layout dict

    def _ensure_font(self, slot_h):
        """슬롯 높이에 맞춰 폰트를 로드/캐시한다. 실패 시 _font=None 유지."""
        # 대략적인 폰트 크기 산정 (슬롯 높이의 35%)
        target_size = max(12, int(slot_h * 0.35))
        if self._font_loaded and self._font is not None and abs((self._font_size or 0) - target_size) <= 2:
            return
        # 폰트 경로 후보: 리소스 내 존재하면 우선, 없으면 Windows 기본 폰트 경로 사용
        candidates = [
            os.path.join('resources', 'Fonts', 'Arial.ttf'),
            os.path.join('resources', 'Fonts', 'NanumGothic.ttf'),
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/malgun.ttf',  # 한글 폰트
        ]
        for path in candidates:
            try:
                self._font = load_font(path, target_size)
                self._font_size = target_size
                self._font_loaded = True
                return
            except Exception:
                continue
        # 실패 시 폰트 사용하지 않음
        self._font = None
        self._font_size = None
        self._font_loaded = True

    def update(self):
        # 플레이어 인벤토리 크기 변경 시 동기화
        self.cols = getattr(self.player.inventory, 'cols', self.cols)
        self.rows = getattr(self.player.inventory, 'rows', self.rows)
        # 인벤토리 닫힐 때 드래그 상태 초기화
        if not getattr(self.player, 'inventory_open', False) and self.dragging:
            self.dragging = False
            self.drag_from = None
            self.drag_icon = None
            self.drag_qty = 0

    def handle_event(self, event):
        # 인벤토리가 열려있을 때만 입력 처리
        if not getattr(self.player, 'inventory_open', False):
            return
        # 디버그: F5/F6로 아이템 추가 테스트
        if event.type == SDL_KEYDOWN:
            try:
                if event.key == SDLK_F5:
                    # 포션 5개 스택으로 추가
                    potion = Item.from_filename('Potion/Item_RedPotion0.png', '빨간 포션')
                    leftover = potion.append_to(self.player.inventory, qty=5, prefer_stack=True)
                    # 패시브 재적용
                    if hasattr(self.player, 'rebuild_inventory_passives'):
                        self.player.rebuild_inventory_passives()
                    print(f"[InventoryOverlay] F5: 포션 5개 추가 (남은 {leftover})")
                    return
                if event.key == SDLK_F6:
                    # 일반 아이템 3개 빈 슬롯 분할로 추가(당근: 비스택)
                    carrot = Item.from_filename('Carrot.png', '당근')
                    leftover = carrot.append_to(self.player.inventory, qty=3, prefer_stack=False)
                    # 패시브 재적용
                    if hasattr(self.player, 'rebuild_inventory_passives'):
                        self.player.rebuild_inventory_passives()
                    print(f"[InventoryOverlay] F6: 당근 3개 추가 (남은 {leftover})")
                    return
            except Exception as ex:
                print('[InventoryOverlay] 디버그 append 실패:', ex)
        # 우클릭: 소비 아이템 사용
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_RIGHT:
            hit = self._hit_test(event.x, event.y)
            if hit is not None and hasattr(self.player, 'consume_item_at'):
                r, c = hit
                used = self.player.consume_item_at(r, c)
                if not used:
                    # 소비 불가 아이템 정보 출력
                    try:
                        slot = self.player.inventory.get_slot(r, c)
                        if slot.is_empty() or not getattr(slot.item, 'consumable', None):
                            print(f"[InventoryOverlay] 소비 불가: ({r}, {c})")
                    except Exception:
                        pass
            return
        # 좌클릭 다운: 드래그 시작 또는 슬롯 정보 출력
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            hit = self._hit_test(event.x, event.y)
            if hit is not None:
                r, c = hit
                try:
                    slot = self.player.inventory.get_slot(r, c)
                    if not slot.is_empty():
                        # 드래그 시작 (소스 슬롯 상태는 유지, 드래그 고스트만 표시)
                        self.dragging = True
                        self.drag_from = (r, c)
                        self.drag_icon = slot.item.get_icon()
                        self.drag_qty = slot.quantity
                        self.drag_mouse = (event.x, event.y)
                    else:
                        print(f"[InventoryOverlay] 클릭: ({r}, {c}) 빈 슬롯")
                except Exception as ex:
                    print('[InventoryOverlay] 슬롯 접근 오류:', ex)
            return
        # 마우스 모션: 드래그 중이면 위치 갱신
        if event.type == SDL_MOUSEMOTION:
            if self.dragging:
                self.drag_mouse = (event.x, event.y)
            return
        # 좌클릭 업: 드롭 처리
        if event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_LEFT:
            if self.dragging and self.drag_from is not None:
                dst = self._hit_test(event.x, event.y)
                if dst is not None and dst != self.drag_from:
                    try:
                        self.player.inventory.move(self.drag_from, dst)
                        # 위치 변경 후 패시브 재적용(슬롯 기반 식별자 변경 대응)
                        if hasattr(self.player, 'rebuild_inventory_passives'):
                            self.player.rebuild_inventory_passives()
                    except Exception as ex:
                        print('[InventoryOverlay] 드롭 실패:', ex)
                else:
                    # 슬롯 외부에 드롭한 경우: 아이템을 버리고 월드에 생성
                    try:
                        # drag_from 소스 슬롯 정보
                        sr, sc = self.drag_from
                        slot = self.player.inventory.get_slot(sr, sc)
                        if slot.is_empty():
                            # 이미 비어있다면 아무것도 하지 않음
                            pass
                        else:
                            # 제거할 수량(드래그 시 보였던 수량 사용)
                            qty_to_remove = int(self.drag_qty) if self.drag_qty else slot.quantity
                            # 저장: 제거 전에 아이템 레퍼런스를 확보
                            item_ref = slot.item
                            # 안전한 제거
                            removed = self.player.inventory.remove_from(sr, sc, qty_to_remove)
                            if removed > 0:
                                # determine the preferred target world: injected world (self.world) takes precedence,
                                # fallback to __main__.world if available (for backwards compatibility)
                                try:
                                    target_world = self.world if self.world is not None else None
                                    if target_world is None:
                                        import sys
                                        _main = sys.modules.get('__main__') or sys.modules.get('main')
                                        target_world = getattr(_main, 'world', None) if _main is not None else None
                                except Exception:
                                    target_world = None

                                if target_world is not None and isinstance(target_world.get('entities', None), list):
                                    try:
                                        from .item_entity import WorldItem
                                        spawn_x = getattr(self.player, 'x', 0) + (30 * getattr(self.player, 'face_dir', 1))
                                        spawn_y = getattr(self.player, 'y', 0)
                                        wi = WorldItem(item_ref, removed, spawn_x, spawn_y, scale=0.5 * getattr(self.player, 'scale_factor', 1.0), world=target_world)
                                        target_world['entities'].append(wi)
                                        print(f"[InventoryOverlay] 아이템 버림: {getattr(item_ref, 'name', 'Unknown')} x{removed} -> world.entities")
                                    except Exception as ex:
                                        print('[InventoryOverlay] 월드 아이템 생성 실패:', ex)
                                else:
                                    print('[InventoryOverlay] 월드에 접근할 수 없어 아이템을 버리지 못했습니다.')
                                # 패시브 재적용
                                if hasattr(self.player, 'rebuild_inventory_passives'):
                                    try:
                                        self.player.rebuild_inventory_passives()
                                    except Exception:
                                        pass
                    except Exception as ex:
                        print('[InventoryOverlay] 슬롯 외부 드롭 처리 실패:', ex)
                # 드래그 종료
                self.dragging = False
                self.drag_from = None
                self.drag_icon = None
                self.drag_qty = 0
            return

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

        # 배경 중심 기준 + 오프셋 적용된 그리드 좌표계 계산
        base_slot_draw_w = (self.slot_image.w * slot_scale) if self.slot_image else slot_size
        base_slot_draw_h = (self.slot_image.h * slot_scale) if self.slot_image else slot_size
        slot_draw_w = base_slot_draw_w * getattr(self, 'slot_scale_mult_x', 1.0)
        slot_draw_h = base_slot_draw_h * getattr(self, 'slot_scale_mult_y', 1.0)
        total_w = self.cols * slot_draw_w
        total_h = self.rows * slot_draw_h
        grid_left_centered = target_x - total_w / 2 + self.grid_offset_x * scale
        grid_bottom_centered = target_y - total_h / 2 + self.grid_offset_y * scale

        return {
            'target_x': target_x,
            'target_y': target_y,
            'scale': scale,
            'bg_w': bg_w,
            'bg_h': bg_h,
            'grid_left_centered': grid_left_centered,
            'grid_bottom_centered': grid_bottom_centered,
            'slot_draw_w': slot_draw_w,
            'slot_draw_h': slot_draw_h,
        }

    def _hit_test(self, mx, my):
        """윈도우 좌표(mx,my)를 게임 좌표로 변환 후 슬롯 인덱스(r,c)를 반환. 없으면 None"""
        if self.image is None:
            return None
        canvas_w = get_canvas_width()
        canvas_h = get_canvas_height()
        # y 뒤집기
        gy = canvas_h - my
        layout = self._compute_layout(canvas_w, canvas_h)
        left = layout['grid_left_centered']
        bottom = layout['grid_bottom_centered']
        w = layout['slot_draw_w']
        h = layout['slot_draw_h']
        # 전체 그리드 박스 안인지 빠른 체크
        if not (left <= mx <= left + w * self.cols and bottom <= gy <= bottom + h * self.rows):
            return None
        # 인덱스 계산
        c = int((mx - left) // w)
        r = int((gy - bottom) // h)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return (r, c)
        return None

    def _get_mouse_pos(self):
        mx = ctypes.c_int(0)
        my = ctypes.c_int(0)
        try:
            SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))
            return mx.value, my.value
        except Exception:
            # 모션 이벤트 기반 위치 사용
            return self.drag_mouse

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
        slot_draw_w = layout['slot_draw_w']
        slot_draw_h = layout['slot_draw_h']
        grid_left = layout['grid_left_centered']
        grid_bottom = layout['grid_bottom_centered']

        for r in range(self.rows):
            for c in range(self.cols):
                cx = grid_left + c * slot_draw_w + slot_draw_w / 2
                cy = grid_bottom + r * slot_draw_h + slot_draw_h / 2
                self.slot_image.draw(cx, cy, slot_draw_w, slot_draw_h)

        # 아이템 아이콘 그리기 (슬롯 중앙, 여백 10~20%) + 수량 텍스트
        inv = getattr(self.player, 'inventory', None)
        if inv is None:
            return
        margin_ratio = 0.18
        icon_box_w = slot_draw_w * (1.0 - margin_ratio)
        icon_box_h = slot_draw_h * (1.0 - margin_ratio)
        self._ensure_font(slot_draw_h)

        # 드래그 중이면 현재 마우스가 가리키는 슬롯(호버)을 계산하여 임시 비표시 처리
        hover_rc = None
        if self.dragging:
            mx, my = self._get_mouse_pos()
            hover_rc = self._hit_test(mx, my)

        for r in range(self.rows):
            for c in range(self.cols):
                try:
                    slot = inv.get_slot(r, c)
                except Exception:
                    continue
                # 드래그 중 원본 또는 호버 슬롯은 표시하지 않음(고스트가 더 잘 보이도록)
                if self.dragging and (self.drag_from == (r, c) or (hover_rc is not None and hover_rc == (r, c))):
                    continue
                if slot.is_empty():
                    continue
                icon = slot.item.get_icon()
                if icon is None:
                    continue
                # 아이콘을 슬롯 박스에 맞춰 비율 유지 스케일
                scale = min(icon_box_w / icon.w, icon_box_h / icon.h)
                draw_w = icon.w * scale
                draw_h = icon.h * scale
                cx = grid_left + c * slot_draw_w + slot_draw_w / 2
                cy = grid_bottom + r * slot_draw_h + slot_draw_h / 2
                icon.draw(cx, cy, draw_w, draw_h)
                # 수량 텍스트(2 이상일 때만)
                if getattr(slot, 'quantity', 1) > 1 and self._font is not None:
                    txt = str(slot.quantity)
                    # 우하단 여백 약간 띄워서 그림
                    tx = cx + (slot_draw_w * 0.5) - 4
                    ty = cy - (slot_draw_h * 0.5) + 4
                    # 그림자
                    try:
                        self._font.draw(tx - 1, ty - 1, txt, (0, 0, 0))
                        self._font.draw(tx, ty, txt, (255, 255, 255))
                    except Exception:
                        pass

        # 드래그 고스트 아이콘 (최상단)
        if self.dragging and self.drag_icon is not None:
            mx, my = self._get_mouse_pos()
            scale = min(icon_box_w / self.drag_icon.w, icon_box_h / self.drag_icon.h) * 0.85
            dw = self.drag_icon.w * scale
            dh = self.drag_icon.h * scale
            # 오프셋: x는 -, y는 + 방향으로 슬롯 크기 비율만큼 이동 (되돌림: 0.2)
            offset_x = -slot_draw_w * 0.2
            offset_y =  slot_draw_h * 0.2
            try:
                self.drag_icon.opacify(0.7)
                gy = get_canvas_height() - my
                self.drag_icon.draw(mx + offset_x, gy + offset_y, dw, dh)
            finally:
                try:
                    self.drag_icon.opacify(1.0)
                except Exception:
                    pass
            # 수량 표시
            if self.drag_qty > 1 and self._font is not None:
                tx = (mx + offset_x) + (dw * 0.5) - 4
                ty = (get_canvas_height() - my + offset_y) - (dh * 0.5) + 4
                try:
                    self._font.draw(tx - 1, ty - 1, str(self.drag_qty), (0, 0, 0))
                    self._font.draw(tx, ty, str(self.drag_qty), (255, 255, 255))
                except Exception:
                    pass


class HealthBar:
    """화면 왼쪽 상단에 표시되는 체력 바 UI"""
    _hp_images = None  # 클래스 변수로 이미지 공유

    def __init__(self, player):
        self.player = player

        # 체력 바 이미지 로드 (최초 1회만)
        if HealthBar._hp_images is None:
            HealthBar._hp_images = []
            hp_folder = os.path.join('resources', 'Texture_organize', 'UI', 'Erta_HP')
            try:
                for i in range(6):  # ExtraHP00 ~ ExtraHP05
                    img_path = os.path.join(hp_folder, f'ExtraHP0{i}.png')
                    img = load_image(img_path)
                    HealthBar._hp_images.append(img)
                print(f"[HealthBar] 체력 바 이미지 로드 완료: {len(HealthBar._hp_images)}개")
            except Exception as ex:
                print(f"[HealthBar] 체력 바 이미지 로드 실패: {ex}")
                HealthBar._hp_images = []

        # UI 위치 및 크기 설정
        self.x = 150  # 화면 왼쪽에서 150픽셀
        self.y_from_top = 50  # 화면 위에서 50픽셀
        self.width_scale = 5.0  # 가로 방향으로 5배 확대
        self.height_scale = 2.0  # 세로 방향으로 2배 확대

        # 애니메이션 관련 변수
        self.frame_time = 0.0  # 현재 프레임 경과 시간
        self.frame_index = 0  # 현재 애니메이션 프레임 인덱스
        self.frame_duration = 0.1  # 각 프레임 지속 시간 (초) - 조정 가능

        # 폰트 로드
        self.font = None
        try:
            # 폰트 경로 후보
            font_candidates = [
                os.path.join('resources', 'Fonts', 'Arial.ttf'),
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/malgun.ttf',
            ]
            for font_path in font_candidates:
                try:
                    self.font = load_font(font_path, 20)  # 폰트 크기 20으로 조정
                    print(f"[HealthBar] 폰트 로드 성공: {font_path}")
                    break
                except Exception:
                    continue
        except Exception as ex:
            print(f"[HealthBar] 폰트 로드 실패: {ex}")

    def update(self):
        """애니메이션 프레임 업데이트"""
        if not HealthBar._hp_images or len(HealthBar._hp_images) == 0:
            return

        # 시간 기반 애니메이션 진행
        import time
        current_time = time.time()
        if not hasattr(self, '_last_update_time'):
            self._last_update_time = current_time

        delta_time = current_time - self._last_update_time
        self._last_update_time = current_time

        self.frame_time += delta_time

        # 프레임 전환
        if self.frame_time >= self.frame_duration:
            self.frame_time -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(HealthBar._hp_images)

    def draw(self):
        """플레이어의 현재 체력에 따라 적절한 체력 바를 표시"""
        if not HealthBar._hp_images or len(HealthBar._hp_images) == 0:
            return

        # 플레이어의 현재 체력 비율 계산
        try:
            current_health = self.player.stats.get('health')
            max_health = self.player.stats.get('max_health')
            health_ratio = current_health / max_health if max_health > 0 else 0
        except Exception:
            current_health = 100
            max_health = 100
            health_ratio = 1.0  # 기본값

        # 애니메이션 프레임 사용 (상시 재생)
        image_index = self.frame_index
        if image_index < 0 or image_index >= len(HealthBar._hp_images):
            image_index = 0

        hp_image = HealthBar._hp_images[image_index]

        # 화면 좌표 계산 (pico2d는 하단이 0)
        canvas_h = get_canvas_height()
        draw_y = canvas_h - self.y_from_top

        # 가로로 늘려서 그리기
        draw_width = hp_image.w * self.width_scale
        draw_height = hp_image.h * self.height_scale

        hp_image.draw(self.x, draw_y, draw_width, draw_height)

        # 체력 텍스트 표시 (체력 바 중앙에)
        if self.font:
            text_x = self.x * 0.8  # 체력 바 중앙
            text_y = draw_y  # 체력 바 중앙

            # 체력 텍스트 (현재/최대)
            health_text = f"{int(current_health)}/{int(max_health)}"

            # 그림자 효과 (가독성 향상)
            self.font.draw(text_x - 2, text_y - 2, health_text, (0, 0, 0))
            self.font.draw(text_x - 1, text_y - 1, health_text, (0, 0, 0))
            # 실제 텍스트 (흰색)
            self.font.draw(text_x, text_y, health_text, (255, 255, 255))


class ManaBar:
    """화면 왼쪽 상단에 표시되는 마나 바 UI"""
    _mp_images = None  # 클래스 변수로 이미지 공유

    def __init__(self, player):
        self.player = player

        # 마나 바 이미지 로드 (최초 1회만)
        if ManaBar._mp_images is None:
            ManaBar._mp_images = []
            mp_folder = os.path.join('resources', 'Texture_organize', 'UI', 'Erta_MP')
            try:
                for i in range(6):  # ExtraMP00 ~ ExtraMP05
                    img_path = os.path.join(mp_folder, f'ExtraMP0{i}.png')
                    img = load_image(img_path)
                    ManaBar._mp_images.append(img)
                print(f"[ManaBar] 마나 바 이미지 로드 완료: {len(ManaBar._mp_images)}개")
            except Exception as ex:
                print(f"[ManaBar] 마나 바 이미지 로드 실패: {ex}")
                ManaBar._mp_images = []

        # UI 위치 및 크기 설정 (HealthBar보다 아래)
        self.x = 150  # 화면 왼쪽에서 150픽셀
        self.y_from_top = 80  # 화면 위에서 120픽셀 (HealthBar보다 아래)
        self.width_scale = 5.0
        self.height_scale = 2.0

        # 애니메이션 관련 변수
        self.frame_time = 0.0
        self.frame_index = 0
        self.frame_duration = 0.1

        # 폰트 로드
        self.font = None
        try:
            font_candidates = [
                os.path.join('resources', 'Fonts', 'Arial.ttf'),
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/malgun.ttf',
            ]
            for font_path in font_candidates:
                try:
                    self.font = load_font(font_path, 20)
                    print(f"[ManaBar] 폰트 로드 성공: {font_path}")
                    break
                except Exception:
                    continue
        except Exception as ex:
            print(f"[ManaBar] 폰트 로드 실패: {ex}")

    def update(self):
        if not ManaBar._mp_images or len(ManaBar._mp_images) == 0:
            return
        import time
        current_time = time.time()
        if not hasattr(self, '_last_update_time'):
            self._last_update_time = current_time
        delta_time = current_time - self._last_update_time
        self._last_update_time = current_time
        self.frame_time += delta_time
        if self.frame_time >= self.frame_duration:
            self.frame_time -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(ManaBar._mp_images)

    def draw(self):
        if not ManaBar._mp_images or len(ManaBar._mp_images) == 0:
            return
        try:
            current_mana = self.player.stats.get('mana')
            max_mana = self.player.stats.get('max_mana')
            mana_ratio = current_mana / max_mana if max_mana > 0 else 0
        except Exception:
            current_mana = 100
            max_mana = 100
            mana_ratio = 1.0
        image_index = self.frame_index
        if image_index < 0 or image_index >= len(ManaBar._mp_images):
            image_index = 0
        mp_image = ManaBar._mp_images[image_index]
        canvas_h = get_canvas_height()
        draw_y = canvas_h - self.y_from_top
        draw_width = mp_image.w * self.width_scale
        draw_height = mp_image.h * self.height_scale
        mp_image.draw(self.x, draw_y, draw_width, draw_height)
        if self.font:
            text_x = self.x * 0.8
            text_y = draw_y
            mana_text = f"{int(current_mana)}/{int(max_mana)}"
            self.font.draw(text_x - 2, text_y - 2, mana_text, (0, 0, 0))
            self.font.draw(text_x - 1, text_y - 1, mana_text, (0, 0, 0))
            self.font.draw(text_x, text_y, mana_text, (255, 255, 255))  # 파란색 계열

