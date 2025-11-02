# 패키지 내부 모듈. 공용 아이템 팩토리와 샘플 세트 제공
from .inventory import Item

# 개별 아이템 팩토리 (파일 경로는 Item 폴더 상대 경로)

def lantern():
    # 랜턴은 스탯 효과 없음(예시)
    return Item.from_filename('Lantern.png', '랜턴')

def magic_glasses():
    # 치명타 확률 +5% (패시브)
    return Item.from_filename('MagicGlasses.png', '마법 안경',
                              passive={'crit_chance': 0.05})

def rabbit_guard_helm():
    # 방어력 +5 (패시브)
    return Item.from_filename('RabbitGuardHelm.png', '토끼 수호자 투구',
                              passive={'defense': 5.0})

def carrot():
    # 소비 시 8초간 이동속도 +50
    return Item.from_filename('Carrot.png', '당근',
                              consumable={'move_speed': 50.0}, consume_duration=8.0)

def amber():
    # 예시: 공격력 +2 (패시브)
    return Item.from_filename('Amber.png', '호박보석',
                              passive={'attack_damage': 2.0})

def ruby():
    # 예시: 공격력 +3 (패시브)
    return Item.from_filename('Ruby.png', '루비',
                              passive={'attack_damage': 3.0})

def white_bread():
    # 소비 시 10초간 방어력 +2
    return Item.from_filename('WhiteCrustedBread.png',
                              '하얀 빵', consumable={'defense': 2.0}, consume_duration=10.0)

def potion_red0():
    # 소비 시 15초간 공격력 +5
    return Item.from_filename('Potion/Item_RedPotion0.png', '빨간 포션',
                              consumable={'attack_damage': 5.0}, consume_duration=15.0)


# 디버그용 샘플 목록 생성기

def sample_debug_list():
    """디버그 시드에 사용할 (Item, qty) 리스트를 반환"""
    return [
        (lantern(), 1),
        (magic_glasses(), 1),
        (rabbit_guard_helm(), 1),
        (carrot(), 3),              # 비스택: 각 1개씩 여러 슬롯
        (amber(), 2),
        (ruby(), 2),
        (white_bread(), 1),
        (potion_red0(), 15),        # 스택: 한 슬롯에 누적
    ]
