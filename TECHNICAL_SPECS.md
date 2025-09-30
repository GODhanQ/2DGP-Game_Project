# 기술 사양서 (Technical Specifications)

## 시스템 요구사항

### 최소 사양
- **OS**: Windows 10 / macOS 10.14 / Linux (Ubuntu 18.04+)
- **CPU**: 2.0 GHz Dual Core
- **RAM**: 4 GB
- **GPU**: OpenGL 2.0 지원
- **저장공간**: 500 MB

### 권장 사양
- **OS**: Windows 10/11 / macOS 11+ / Linux (최신)
- **CPU**: 3.0 GHz Quad Core
- **RAM**: 8 GB
- **GPU**: OpenGL 3.0+ 지원
- **저장공간**: 1 GB

---

## 기술 스택

### 개발 언어
- **주 언어**: Python 3.8+
- **스크립팅**: Python

### 게임 엔진/라이브러리
- **그래픽**: Pico2D (SDL2 기반)
- **물리**: 자체 구현 (간단한 2D 물리)
- **사운드**: Pico2D 사운드 시스템

### 개발 도구
- **IDE**: PyCharm / VS Code
- **버전 관리**: Git / GitHub
- **이미지 편집**: GIMP / Aseprite
- **맵 에디터**: Tiled (선택사항)

---

## 게임 사양

### 해상도
- **기본 해상도**: 1280 x 720 (HD)
- **종횡비**: 16:9
- **풀스크린**: 지원
- **창 모드**: 지원

### 프레임률
- **목표 FPS**: 60 FPS
- **최소 FPS**: 30 FPS
- **VSync**: 선택 가능

### 입력
- **키보드**: 필수
- **마우스**: 메뉴 전용
- **게임패드**: 선택사항 (추후 지원)

---

## 게임플레이 사양

### 플레이어 캐릭터

#### 기본 속성
```python
PLAYER_SPECS = {
    'max_health': 100,
    'max_mana': 50,
    'base_damage': 10,
    'base_defense': 5,
    'move_speed': 300,  # 픽셀/초
    'jump_power': 500,  # 픽셀/초
    'gravity': -980,    # 픽셀/초²
}
```

#### 움직임 속성
```python
MOVEMENT_SPECS = {
    'acceleration': 1500,      # 픽셀/초²
    'deceleration': 1200,      # 픽셀/초²
    'max_speed': 300,          # 픽셀/초
    'jump_speed': 500,         # 픽셀/초
    'double_jump_speed': 400,  # 픽셀/초
    'dash_speed': 800,         # 픽셀/초
    'dash_duration': 0.2,      # 초
    'dash_cooldown': 1.0,      # 초
    'wall_jump_speed': 450,    # 픽셀/초
}
```

#### 전투 속성
```python
COMBAT_SPECS = {
    'basic_attack_damage': 10,
    'basic_attack_cooldown': 0.5,  # 초
    'heavy_attack_damage': 25,
    'heavy_attack_cooldown': 2.0,  # 초
    'invincibility_time': 1.0,     # 피격 후 무적 시간
    'knockback_force': 200,        # 픽셀/초
}
```

---

### 스킬 사양

#### 스킬 1: 기본 공격
```python
SKILL_BASIC_ATTACK = {
    'name': '기본 공격',
    'type': 'melee',
    'damage': 10,
    'range': 50,      # 픽셀
    'cooldown': 0.5,  # 초
    'mana_cost': 0,
    'combo_count': 3,
    'animation_duration': 0.3,  # 초
}
```

#### 스킬 2: 강 공격
```python
SKILL_HEAVY_ATTACK = {
    'name': '강 공격',
    'type': 'melee',
    'damage': 25,
    'range': 70,
    'cooldown': 2.0,
    'mana_cost': 10,
    'charge_time': 1.0,    # 최대 차지 시간
    'max_damage': 40,      # 완전 차지 시
    'animation_duration': 0.5,
}
```

#### 스킬 3: 마법 발사체
```python
SKILL_PROJECTILE = {
    'name': '마법 화살',
    'type': 'projectile',
    'damage': 15,
    'speed': 400,     # 픽셀/초
    'range': 500,     # 픽셀
    'cooldown': 3.0,
    'mana_cost': 15,
    'projectile_size': 16,  # 픽셀
    'piercing': False,
}
```

#### 스킬 4: 범위 공격
```python
SKILL_AOE = {
    'name': '충격파',
    'type': 'aoe',
    'damage': 20,
    'radius': 100,    # 픽셀
    'cooldown': 5.0,
    'mana_cost': 20,
    'knockback': 300,  # 픽셀/초
    'duration': 0.5,   # 이펙트 지속 시간
}
```

#### 스킬 5: 버프
```python
SKILL_BUFF = {
    'name': '전투 강화',
    'type': 'buff',
    'damage_increase': 1.5,  # 배율
    'duration': 10.0,        # 초
    'cooldown': 30.0,
    'mana_cost': 30,
    'visual_effect': True,
}
```

---

### 몬스터 사양

#### 몬스터 1: 슬라임
```python
MONSTER_SLIME = {
    'name': '슬라임',
    'health': 30,
    'attack_power': 5,
    'defense': 2,
    'move_speed': 100,     # 픽셀/초
    'detection_range': 200,  # 픽셀
    'attack_range': 40,    # 픽셀
    'attack_cooldown': 2.0,  # 초
    'exp_reward': 10,
    'drop_rate': 0.3,
}
```

#### 몬스터 2: 박쥐
```python
MONSTER_BAT = {
    'name': '박쥐',
    'health': 20,
    'attack_power': 8,
    'defense': 0,
    'move_speed': 200,
    'detection_range': 300,
    'attack_range': 30,
    'attack_cooldown': 1.5,
    'flying': True,
    'exp_reward': 15,
    'drop_rate': 0.2,
}
```

#### 몬스터 3: 해골 전사
```python
MONSTER_SKELETON = {
    'name': '해골 전사',
    'health': 50,
    'attack_power': 12,
    'defense': 5,
    'move_speed': 120,
    'detection_range': 250,
    'attack_range': 50,
    'attack_cooldown': 1.8,
    'combo_attack': True,
    'exp_reward': 25,
    'drop_rate': 0.4,
}
```

#### 몬스터 4: 고블린 궁수
```python
MONSTER_GOBLIN_ARCHER = {
    'name': '고블린 궁수',
    'health': 35,
    'attack_power': 10,
    'defense': 3,
    'move_speed': 150,
    'detection_range': 400,
    'attack_range': 300,  # 원거리
    'attack_cooldown': 2.5,
    'projectile_speed': 300,
    'exp_reward': 20,
    'drop_rate': 0.35,
}
```

#### 몬스터 5: 골렘
```python
MONSTER_GOLEM = {
    'name': '골렘',
    'health': 100,
    'attack_power': 20,
    'defense': 10,
    'move_speed': 80,
    'detection_range': 200,
    'attack_range': 60,
    'attack_cooldown': 3.0,
    'super_armor': True,  # 경직 무시
    'exp_reward': 50,
    'drop_rate': 0.5,
}
```

---

### 보스 사양

#### 보스 1: 숲의 수호자
```python
BOSS_FOREST_GUARDIAN = {
    'name': '숲의 수호자',
    'max_health': 500,
    'phases': [
        {  # Phase 1: 100%-70%
            'attack_power': 15,
            'defense': 10,
            'move_speed': 150,
            'attack_cooldown': 2.0,
            'patterns': ['melee', 'charge', 'summon'],
        },
        {  # Phase 2: 70%-30%
            'attack_power': 20,
            'defense': 12,
            'move_speed': 180,
            'attack_cooldown': 1.5,
            'patterns': ['melee', 'charge', 'summon', 'aoe'],
        },
        {  # Phase 3: 30%-0%
            'attack_power': 25,
            'defense': 15,
            'move_speed': 200,
            'attack_cooldown': 1.0,
            'patterns': ['all', 'berserk'],
        },
    ],
    'exp_reward': 500,
    'guaranteed_drop': 'boss_key_1',
}
```

#### 보스 2: 어둠의 기사
```python
BOSS_DARK_KNIGHT = {
    'name': '어둠의 기사',
    'max_health': 600,
    'phases': [
        {  # Phase 1: 100%-60%
            'attack_power': 18,
            'defense': 12,
            'move_speed': 180,
            'attack_cooldown': 1.8,
            'patterns': ['sword_combo', 'dash_slash', 'guard'],
        },
        {  # Phase 2: 60%-20%
            'attack_power': 23,
            'defense': 15,
            'move_speed': 200,
            'attack_cooldown': 1.5,
            'patterns': ['sword_combo', 'dark_magic', 'teleport', 'aoe'],
        },
        {  # Phase 3: 20%-0%
            'attack_power': 30,
            'defense': 18,
            'move_speed': 220,
            'attack_cooldown': 1.2,
            'patterns': ['ultimate', 'all_enhanced'],
        },
    ],
    'exp_reward': 1000,
    'guaranteed_drop': 'boss_key_2',
}
```

---

## 맵 사양

### 타일 사양
```python
TILE_SPECS = {
    'size': 32,  # 픽셀
    'types': {
        'ground': {'collision': True, 'platform': False},
        'platform': {'collision': True, 'platform': True},
        'wall': {'collision': True, 'platform': False},
        'spike': {'collision': True, 'damage': 10},
        'water': {'collision': False, 'slow': 0.5},
    }
}
```

### 맵 크기
```python
MAP_SPECS = {
    'level_1': {
        'width': 100,   # 타일
        'height': 50,   # 타일
        'pixel_width': 3200,   # 픽셀
        'pixel_height': 1600,  # 픽셀
    },
    'level_2': {
        'width': 120,
        'height': 60,
        'pixel_width': 3840,
        'pixel_height': 1920,
    },
    'boss_room': {
        'width': 40,
        'height': 30,
        'pixel_width': 1280,
        'pixel_height': 960,
    },
}
```

---

## 충돌 감지 사양

### 충돌 레이어
```python
COLLISION_LAYERS = {
    'player': 1 << 0,      # 0001
    'monster': 1 << 1,     # 0010
    'projectile': 1 << 2,  # 0100
    'terrain': 1 << 3,     # 1000
}

COLLISION_MATRIX = {
    'player': ['monster', 'terrain', 'projectile'],
    'monster': ['player', 'terrain'],
    'projectile': ['player', 'monster', 'terrain'],
    'terrain': ['player', 'monster', 'projectile'],
}
```

### 히트박스 크기
```python
HITBOX_SPECS = {
    'player': {
        'width': 30,
        'height': 48,
        'offset_x': 0,
        'offset_y': 0,
    },
    'player_attack': {
        'width': 50,
        'height': 30,
        'offset_x': 25,  # 앞쪽
        'offset_y': 0,
    },
    'slime': {
        'width': 32,
        'height': 32,
        'offset_x': 0,
        'offset_y': 0,
    },
}
```

---

## 애니메이션 사양

### 프레임 구성
```python
ANIMATION_SPECS = {
    'player_idle': {
        'frames': 4,
        'frame_delay': 0.15,  # 초
        'loop': True,
    },
    'player_walk': {
        'frames': 6,
        'frame_delay': 0.1,
        'loop': True,
    },
    'player_jump': {
        'frames': 3,
        'frame_delay': 0.1,
        'loop': False,
    },
    'player_attack': {
        'frames': 5,
        'frame_delay': 0.06,
        'loop': False,
    },
}
```

---

## 사운드 사양

### 효과음
```python
SOUND_EFFECTS = {
    'player_jump': {'volume': 0.5, 'priority': 'medium'},
    'player_attack': {'volume': 0.6, 'priority': 'high'},
    'player_hit': {'volume': 0.7, 'priority': 'high'},
    'monster_hit': {'volume': 0.5, 'priority': 'medium'},
    'coin_collect': {'volume': 0.4, 'priority': 'low'},
}
```

### 배경음악
```python
MUSIC_SPECS = {
    'menu': {'volume': 0.5, 'loop': True},
    'stage_1': {'volume': 0.4, 'loop': True},
    'boss_battle': {'volume': 0.6, 'loop': True},
}
```

---

## 성능 사양

### 목표
- **FPS**: 60 (고정)
- **프레임 시간**: 16.67ms 이하
- **메모리 사용**: 200MB 이하
- **로딩 시간**: 2초 이하

### 최적화 기법
- 객체 풀링 (발사체, 이펙트)
- 공간 분할 (충돌 감지)
- 타일 컬링 (화면 밖 제외)
- 스프라이트 아틀라스

---

## 저장 데이터 형식

### 게임 세이브
```json
{
  "version": "1.0",
  "player": {
    "level": 5,
    "health": 100,
    "mana": 50,
    "position": {"x": 100, "y": 200},
    "current_map": "level_2"
  },
  "unlocked_skills": ["slash", "fireball"],
  "inventory": ["health_potion", "mana_potion"],
  "progress": {
    "defeated_bosses": ["forest_guardian"],
    "discovered_maps": ["level_1", "level_2"]
  }
}
```

---

## 디버그 모드

### 디버그 키
```python
DEBUG_KEYS = {
    'F1': 'toggle_hitbox',
    'F2': 'toggle_fps',
    'F3': 'god_mode',
    'F4': 'teleport_mode',
    'F5': 'spawn_monster',
}
```

### 디버그 정보
- FPS 카운터
- 플레이어 위치
- 히트박스 표시
- AI 상태 표시

---

**문서 버전**: 1.0
**마지막 업데이트**: 2024
