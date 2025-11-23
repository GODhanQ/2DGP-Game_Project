# Simple world item entity used when dropping items from inventory

class WorldItem:
    """월드에 떨어진 아이템 엔티티(간단한 표시용)
    - item: Inventory.Item 인스턴스
    - qty: 수량
    - x, y: 게임 좌표(픽셀)
    - world: (optional) reference to the main world's dict so the item can remove itself and find the player
    """
    def __init__(self, item, qty, x, y, scale=0.5, world=None, pickup_radius=60):
        self.item = item
        self.qty = qty
        self.x = x
        self.y = y
        self.scale = scale
        self._icon = None
        self.world = world
        # 픽업 가능 반경(픽셀)
        self.pickup_radius = pickup_radius

    @property
    def icon(self):
        if self._icon is None and self.item is not None:
            try:
                self._icon = self.item.get_icon()
            except Exception:
                self._icon = None
        return self._icon

    def update(self):
        # 정적 객체
        return

    def handle_event(self, event):
        # F 키로 줍기 처리
        try:
            from sdl2 import SDL_KEYDOWN, SDLK_f
        except Exception:
            SDL_KEYDOWN = None
            SDLK_f = None
        try:
            if SDL_KEYDOWN is not None and event.type == SDL_KEYDOWN and event.key == SDLK_f:
                # world 레퍼런스를 찾음
                world = self.world
                if world is None:
                    import sys
                    _main = sys.modules.get('__main__') or sys.modules.get('main')
                    world = getattr(_main, 'world', None) if _main is not None else None
                if world is None:
                    return
                # 플레이어 찾기 (첫 번째로 inventory를 가진 엔티티)
                player = None
                for o in world.get('entities', []):
                    if hasattr(o, 'inventory') and hasattr(o, 'x') and hasattr(o, 'y'):
                        player = o
                        break
                if player is None:
                    return
                # 거리 검사
                dx = getattr(player, 'x', 0) - self.x
                dy = getattr(player, 'y', 0) - self.y
                dist2 = dx * dx + dy * dy
                if dist2 > (self.pickup_radius * self.pickup_radius):
                    # 범위 밖
                    return
                # 인벤토리에 추가 시도
                try:
                    # Item.append_to returns leftover count
                    leftover = self.item.append_to(player.inventory, qty=self.qty, prefer_stack=True)
                except Exception:
                    # fallback: InventoryData.add_item
                    try:
                        leftover = player.inventory.add_item(self.item, self.qty)
                    except Exception:
                        leftover = self.qty
                added = self.qty - leftover
                if added > 0:
                    print(f"[WorldItem] picked up {getattr(self.item, 'name', 'Unknown')} x{added} by player")
                    self.qty = leftover
                # 완전히 주웠으면 월드에서 제거
                if self.qty <= 0:
                    try:
                        if world is not None and self in world.get('entities', []):
                            world['entities'].remove(self)
                    except Exception:
                        print(f'\033[91m[WorldItem] failed to remove picked up item from world\033[0m')
        except Exception:
            # 안전하게 무시
            print(f'\033[91m[WorldItem] handle_event exception\033[0m')

    def draw(self, draw_x, draw_y):
        ic = self.icon
        if ic is None:
            return
        w = ic.w * self.scale
        h = ic.h * self.scale
        # 아이콘을 중심 기준으로 그림
        try:
            ic.draw(draw_x, draw_y, w, h)
        except Exception:
            print(f'\033[91m[WorldItem] failed to draw icon\033[0m')
