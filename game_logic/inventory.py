# 패키지 내부 모듈을 직접 실행할 경우 친절한 안내 후 종료
if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    import sys
    print("이 모듈은 game_logic 패키지 내부 모듈입니다. 프로젝트 루트에서 main.py를 실행하세요.")
    sys.exit(1)

import os
from typing import Optional, List
from pico2d import load_image

ITEMS_BASE = os.path.join('resources', 'Texture_organize', 'Item')


class Item:
    """게임 아이템 단위. 동일 아이템은 stackable=True일 때 수량으로 누적.
    - id: 고유 문자열 (파일명 기반으로 기본 생성)
    - name: 표시용 이름
    - icon_path: 아이콘 png 경로
    - stackable: 스택 가능 여부
    - max_stack: 한 슬롯 최대 수량
    """
    def __init__(self, id: str, name: str, icon_path: str, stackable: bool = True, max_stack: int = 99):
        self.id = id
        self.name = name
        self.icon_path = icon_path
        self.stackable = stackable
        self.max_stack = max_stack
        self._icon_image = None  # 지연 로드

    def get_icon(self):
        if self._icon_image is None:
            try:
                self._icon_image = load_image(self.icon_path)
            except Exception as ex:
                print(f"[Item] 아이콘 로드 실패: {self.icon_path}", ex)
                self._icon_image = None
        return self._icon_image

    @classmethod
    def from_filename(cls, filename: str, name: Optional[str] = None, stackable: bool = True, max_stack: int = 99):
        path = os.path.join(ITEMS_BASE, filename)
        item_id = os.path.splitext(os.path.basename(filename))[0]
        # 규칙: Potion 폴더 내부만 스택 가능(최대 99), 그 외는 1개 제한
        norm = filename.replace('\\', '/')
        is_potion = norm.startswith('Potion/') or '/Potion/' in norm
        if is_potion:
            eff_stackable = True
            eff_max_stack = 99
        else:
            eff_stackable = False
            eff_max_stack = 1
        return cls(item_id, name or item_id, path, stackable=eff_stackable, max_stack=eff_max_stack)

    def append_to(self, inventory: 'InventoryData', qty: int = 1, prefer_stack: bool = True) -> int:
        """해당 아이템을 주어진 인벤토리에 추가한다.
        - prefer_stack=True: 기존 add_item과 동일하게 스택 우선 채우기
        - prefer_stack=False: 스택을 만들지 않고 빈 슬롯을 우선적으로 채움(슬롯당 max_stack 제한 적용)
        반환값: 수용하지 못한 남은 수량
        """
        return inventory.append_item(self, qty=qty, prefer_stack=prefer_stack)


class InventorySlot:
    def __init__(self):
        self.item: Optional[Item] = None
        self.quantity: int = 0

    def is_empty(self) -> bool:
        return self.item is None or self.quantity <= 0

    def clear(self):
        self.item = None
        self.quantity = 0

    def can_stack(self, item: Item) -> bool:
        return (
            not self.is_empty() and
            self.item.id == item.id and
            self.item.stackable and
            self.quantity < self.item.max_stack
        )

    def push(self, item: Item, qty: int) -> int:
        """슬롯에 아이템을 채워 넣는다. 남은 수량을 반환한다."""
        if qty <= 0:
            return 0
        if self.is_empty():
            self.item = item
            take = min(qty, item.max_stack if item.stackable else 1)
            self.quantity = take
            return qty - take
        # 스택 시도
        if self.can_stack(item):
            space = self.item.max_stack - self.quantity
            take = min(space, qty)
            self.quantity += take
            return qty - take
        # 스택 불가 -> 모두 남김
        return qty


class InventoryData:
    """인벤토리 데이터 컨테이너. UI와 분리된 순수 로직."""
    def __init__(self, cols: int = 6, rows: int = 5):
        self.cols = cols
        self.rows = rows
        self.slots: List[InventorySlot] = [InventorySlot() for _ in range(cols * rows)]

    def index(self, r: int, c: int) -> int:
        return r * self.cols + c

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get_slot(self, r: int, c: int) -> InventorySlot:
        if not self.in_bounds(r, c):
            raise IndexError('slot out of range')
        return self.slots[self.index(r, c)]

    def add_item(self, item: Item, qty: int = 1) -> int:
        """아이템을 인벤토리에 추가. 수용하지 못한 남은 수량을 반환."""
        if qty <= 0:
            return 0
        remaining = qty
        # 1) 같은 아이템 스택 먼저 채우기
        if item.stackable:
            for slot in self.slots:
                if remaining <= 0:
                    break
                if slot.can_stack(item):
                    remaining = slot.push(item, remaining)
        # 2) 빈 슬롯 채우기
        for slot in self.slots:
            if remaining <= 0:
                break
            if slot.is_empty():
                remaining = slot.push(item, remaining)
        return remaining

    def remove_from(self, r: int, c: int, qty: int = 1) -> int:
        """해당 슬롯에서 수량 제거. 실제로 제거된 수량 반환."""
        if qty <= 0:
            return 0
        slot = self.get_slot(r, c)
        if slot.is_empty():
            return 0
        take = min(qty, slot.quantity)
        slot.quantity -= take
        if slot.quantity <= 0:
            slot.clear()
        return take

    def move(self, src_rc, dst_rc):
        """간단 이동/스왑: 같은 아이템이면 스택 병합, 아니면 스왑."""
        (sr, sc) = src_rc
        (dr, dc) = dst_rc
        s = self.get_slot(sr, sc)
        d = self.get_slot(dr, dc)
        if s.is_empty():
            return
        if d.is_empty():
            d.item, d.quantity = s.item, s.quantity
            s.clear()
            return
        if s.item.id == d.item.id and s.item.stackable:
            space = d.item.max_stack - d.quantity
            take = min(space, s.quantity)
            d.quantity += take
            s.quantity -= take
            if s.quantity <= 0:
                s.clear()
        else:
            d.item, s.item = s.item, d.item
            d.quantity, s.quantity = s.quantity, d.quantity

    def append_item(self, item: Item, qty: int = 1, prefer_stack: bool = True) -> int:
        """아이템 추가(append 의미의 편의 API)
        - prefer_stack=True: add_item과 동일(스택 우선 -> 빈 슬롯)
        - prefer_stack=False: 스택을 고려하지 않고 빈 슬롯을 순서대로 채움.
          이때 stackable=True인 아이템도 한 슬롯에 최대 max_stack까지만 채우고, 남으면 다음 빈 슬롯으로 분할.
        반환값: 남은 수량(수용 불가)
        """
        if qty <= 0:
            return 0
        if prefer_stack:
            return self.add_item(item, qty)
        remaining = qty
        # 빈 슬롯만 순회하면서 채우기(스택 무시)
        for slot in self.slots:
            if remaining <= 0:
                break
            if slot.is_empty():
                if item.stackable:
                    take = min(item.max_stack, remaining)
                else:
                    take = 1
                slot.item = item
                slot.quantity = take
                remaining -= take
        return remaining


# 디버그용 아이템 채우기 도우미

def seed_debug_inventory(inventory: InventoryData):
    """리소스 폴더의 존재하는 파일명 위주로 샘플 아이템 채우기 (Potion만 다중 스택)"""
    from random import randint

    def mk(filename: str, name: Optional[str] = None) -> Item:
        return Item.from_filename(filename, name=name)

    samples = [
        (mk('Lantern.png', '랜턴'), 1),
        (mk('MagicGlasses.png', '마법 안경'), 1),
        (mk('RabbitGuardHelm.png', '토끼 수호자 투구'), 1),
        (mk('Carrot.png', '당근'), 3),  # 포션 아님 -> 각 1개씩 여러 슬롯 차지
        (mk('Amber.png', '호박보석'), 2),
        (mk('Ruby.png', '루비'), 2),
        (mk('WhiteCrustedBread.png', '하얀 빵'), 1),
        # 포션: 스택 가능 (한 슬롯에 누적)
        (mk('Potion/Item_RedPotion0.png', '빨간 포션'), 15),
    ]

    for item, qty in samples:
        leftover = inventory.add_item(item, qty)
        if leftover > 0:
            print(f"[Inventory] {item.name} {qty} 중 {leftover}개는 인벤토리에 공간이 없어 버려졌습니다.")

    # 포션 추가로 스택 합쳐지는지 확인
    inventory.add_item(mk('Potion/Item_RedPotion0.png', '빨간 포션'), randint(3, 8))
