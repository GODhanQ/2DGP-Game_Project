# 간단한 스탯/버프 시스템
from typing import Dict, Optional
import game_framework

class StatModifier:
    def __init__(self, id: str, values: Dict[str, float], duration: Optional[float] = None):
        self.id = id
        self.values = dict(values)
        self.duration = duration
        self.time_left = duration

    def update(self, dt: float) -> bool:
        if self.duration is None:
            return False
        self.time_left -= dt
        return self.time_left <= 0

    @property
    def expired(self) -> bool:
        return self.duration is not None and self.time_left is not None and self.time_left <= 0


class PlayerStats:
    def __init__(self, base: Optional[Dict[str, float]] = None):
        self.base = base or {
            'max_health': 100.0,
            'max_mana': 50.0,
            'health_regen': 0.2,
            'mana_regen': 0.5,
            'health': 100.0,
            'mana': 50.0,
            'move_speed': 250.0,
            'attack_speed': 1.0,
            'attack_damage': 10.0,
            'defense': 0.0,
            'crit_chance': 0.05,
            'crit_damage': 1.5,
        }
        self._mods: Dict[str, StatModifier] = {}

    def set_base(self, key: str, value: float):
        self.base[key] = value

    def add_modifier(self, mod: StatModifier):
        self._mods[mod.id] = mod

    def remove_modifier(self, mod_id: str):
        if mod_id in self._mods:
            del self._mods[mod_id]

    def clear_by_prefix(self, prefix: str):
        ids = [k for k in self._mods.keys() if k.startswith(prefix)]
        for k in ids:
            del self._mods[k]

    def get(self, key: str) -> float:
        v = self.base.get(key, 0.0)
        for mod in self._mods.values():
            v += mod.values.get(key, 0.0)
        return v

    def __getitem__(self, key: str) -> float:
        """딕셔너리처럼 stats['key'] 형태로 접근 가능하도록 함"""
        return self.get(key)

    def __setitem__(self, key: str, value: float):
        """딕셔너리처럼 stats['key'] = value 형태로 설정 가능하도록 함"""
        self.set_base(key, value)

    def update(self):
        dt = game_framework.get_delta_time()
        to_remove = []
        for k, mod in self._mods.items():
            if mod.duration is not None:
                if mod.update(dt):
                    to_remove.append(k)
        for k in to_remove:
            del self._mods[k]

        # 자연 회복 처리
        self.base['health'] = min(self.get('max_health'), self.base['health'] + self.get('health_regen') * dt)

        # 마나 회복 처리 (방패 복구 로직 포함)
        old_mana = self.base['mana']
        self.base['mana'] = min(self.get('max_mana'), self.base['mana'] + self.get('mana_regen') * dt)

        # 마나가 0에서 0 초과로 회복되면 방패 복구
        if old_mana <= 0 and self.base['mana'] > 0:
            # 플레이어 객체를 찾아서 shield_broken 플래그 해제
            # 이 메서드는 PlayerStats의 인스턴스이므로, self를 가진 플레이어를 역참조해야 함
            # 하지만 이는 순환 참조 문제가 있으므로, 대신 외부에서 처리하도록 함
            print(f"[PlayerStats] 마나가 회복되었습니다! ({old_mana:.1f} -> {self.base['mana']:.1f})")


class MonsterStats:
    """몬스터용 스탯 시스템"""
    def __init__(self, base: Optional[Dict[str, float]] = None):
        self.base = base or {
            'max_health': 50.0,
            'health': 50.0,
            'move_speed': 100.0,
            'attack_damage': 5.0,
            'defense': 0.0,
            'attack_speed': 1.0,
            'attack_range': 300.0,
        }
        self._mods: Dict[str, StatModifier] = {}

    def set_base(self, key: str, value: float):
        self.base[key] = value

    def add_modifier(self, mod: StatModifier):
        self._mods[mod.id] = mod

    def remove_modifier(self, mod_id: str):
        if mod_id in self._mods:
            del self._mods[mod_id]

    def clear_by_prefix(self, prefix: str):
        ids = [k for k in self._mods.keys() if k.startswith(prefix)]
        for k in ids:
            del self._mods[k]

    def get(self, key: str) -> float:
        v = self.base.get(key, 0.0)
        for mod in self._mods.values():
            v += mod.values.get(key, 0.0)
        return v

    def update(self):
        dt = game_framework.get_delta_time()
        to_remove = []
        for k, mod in self._mods.items():
            if mod.duration is not None:
                if mod.update(dt):
                    to_remove.append(k)
        for k in to_remove:
            del self._mods[k]


class CatAssassinStats(MonsterStats):
    """CatAssassin 전용 스탯"""
    def __init__(self):
        super().__init__({
            'max_health': 50.0,
            'health': 50.0,
            'move_speed': 100.0,
            'attack_damage': 20.0,
            'defense': 2.0,
            'attack_speed': 1.2,
            'attack_range': 400.0,
        })

class CatThiefStats(MonsterStats):
    """CatThief 전용 스탯"""
    def __init__(self):
        super().__init__({
            'max_health': 70.0,
            'health': 70.0,
            'move_speed': 120.0,
            'attack_damage': 30.0,
            'defense': 2.0,
            'attack_speed': 1.2,
            'attack_range': 400.0,
        })
