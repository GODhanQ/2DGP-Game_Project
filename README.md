# 🎮 2DGP Game Project

**2D 액션 로그라이크 게임 프로젝트**

2024학년도 2학기 2D 게임 프로그래밍 수업 과제로 제작된 Python/pico2d 기반의 본격 액션 로그라이크 게임입니다.

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![pico2d](https://img.shields.io/badge/pico2d-Game%20Engine-green.svg)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow.svg)

---

## 📋 목차

- [게임 소개](#-게임-소개)
- [주요 기능](#-주요-기능)
- [시스템 요구사항](#-시스템-요구사항)
- [설치 및 실행](#-설치-및-실행)
- [게임 조작법](#-게임-조작법)
- [프로젝트 구조](#-프로젝트-구조)
- [기술 스택](#-기술-스택)
- [개발 통계](#-개발-통계)
- [개발 과정](#-개발-과정)
- [라이선스](#-라이선스)

---

## 🎯 게임 소개

플레이어는 다양한 장비를 장착하여 몬스터들과 전투를 벌이는 2D 액션 로그라이크 게임입니다.
상/하체가 분리된 정교한 애니메이션, 행동 트리 기반 AI를 특징으로 합니다.

### 🎪 게임 특징

- **👾 지능적인 적 AI**: 행동 트리(Behavior Tree) 기반의 몬스터 AI
- **⚔️ 다채로운 전투**: 근접/원거리 공격, 가드/패링, 대시/회피 시스템
- **🎨 정교한 애니메이션**: 상/하체 분리 애니메이션으로 자연스러운 움직임
- **💎 완전한 인벤토리**: 아이템 수집, 장비 교체, 스탯 관리
- **🏆 보스 전투**: 6가지 패턴을 가진 Panther Assassin 보스
- **🗺️ 3개 스테이지**: 각기 다른 테마의 스테이지

---

## ✨ 주요 기능

### 🎮 게임플레이 시스템

#### 플레이어 시스템
- ✅ 상태 머신(State Machine) 기반 캐릭터 제어
- ✅ 체력, 마나, 스태미나 관리
- ✅ 대시 및 회피 시스템
- ✅ 가드 및 패링 시스템

#### 전투 시스템
- ✅ 일반 공격 및 강공격
- ✅ 원거리 발사체 공격
- ✅ 콤보 시스템
- ✅ 데미지 계산 및 표시
- ✅ 다양한 VFX 이펙트

#### 장비 및 아이템
- ✅ 인벤토리 시스템
- ✅ 장비 착용 및 교체
- ✅ 아이템 드롭 및 획득
- ✅ 스탯 변화 시각화

### 🤖 AI 시스템

- ✅ 행동 트리(Behavior Tree) 기반 AI
- ✅ 일반 몬스터: Cat Assassin, Cat Thief, Panther Assassin
- ✅ 보스 몬스터: Panther Assassin (6가지 공격 패턴)
- ✅ 상태 기반 행동 전환

### 🎨 그래픽 및 UI

- ✅ 1,000개 이상의 프레임 애니메이션
- ✅ 체력/마나/대시 게이지 UI
- ✅ 인벤토리 및 장비 UI
- ✅ 버프/디버프 표시
- ✅ 데미지 인디케이터
- ✅ 커서 시스템

### 🗺️ 스테이지

- ✅ Stage 1: 첫 번째 구역
- ✅ Stage 2: 두 번째 구역
- ✅ Stage 3: 보스 구역

---

## 💻 시스템 요구사항

### 최소 사양
- **OS**: Windows 10 이상, macOS 10.14+, Linux
- **Python**: 3.8 이상 (권장: 3.13)
- **RAM**: 4GB 이상
- **저장공간**: 500MB 이상

### 권장 사양
- **OS**: Windows 11, macOS 13+
- **Python**: 3.13
- **RAM**: 8GB 이상
- **저장공간**: 1GB 이상

---

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/2DGP-Game_Project.git
cd 2DGP-Game_Project
```

### 2. 가상환경 생성 (선택사항)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 필수 패키지 설치
```bash
pip install pico2d
pip install pillow
```

### 4. 게임 실행
```bash
python main.py
```

---

## 🎮 게임 조작법

### 기본 조작
- **이동**: `W` `A` `S` `D` 또는 방향키
- **일반 공격**: `마우스 좌클릭`
- **강공격**: `마우스 우클릭` (길게 누름)
- **대시/회피**: `Space`
- **가드**: `Shift`

### UI 조작
- **인벤토리 열기**: `I` 또는 `Tab`
- **아이템 사용**: 인벤토리에서 아이템 클릭
- **장비 착용/해제**: 장비 슬롯에 드래그 앤 드롭

### 시스템
- **일시정지**: `ESC`
- **게임 종료**: `ESC` (타이틀 화면에서)

---

## 📁 프로젝트 구조

```
2DGP-Game_Project/
│
├── main.py                      # 게임 진입점
├── game_framework.py            # 게임 프레임워크
├── README.md                    # 프로젝트 설명서
├── PROJECT_STATISTICS.md        # 개발 통계
│
├── game_logic/                  # 게임 로직 패키지
│   ├── __init__.py
│   │
│   ├── # 플레이어 시스템
│   ├── player.py               # 플레이어 캐릭터
│   ├── state_machine.py        # 상태 머신
│   ├── stats.py                # 스탯 시스템
│   ├── inventory.py            # 인벤토리
│   ├── equipment.py            # 장비 시스템
│   │
│   ├── # 게임 모드
│   ├── title_mode.py           # 타이틀 화면
│   ├── lobby_mode.py           # 로비
│   ├── play_mode.py            # 플레이 모드
│   ├── victory_mode.py         # 승리 화면
│   ├── defeat_mode.py          # 패배 화면
│   ├── loading_screen.py       # 로딩 화면
│   │
│   ├── # AI 시스템
│   ├── behavior_tree.py        # 행동 트리
│   │
│   ├── # 전투 시스템
│   ├── projectile.py           # 발사체
│   ├── damage_indicator.py     # 데미지 표시
│   ├── vfx.py                  # 시각 효과
│   │
│   ├── # UI 시스템
│   ├── ui_overlay.py           # UI 오버레이
│   ├── cursor.py               # 커서
│   │
│   ├── # 월드 시스템
│   ├── map.py                  # 맵
│   ├── background.py           # 배경
│   ├── item_entity.py          # 아이템 엔티티
│   │
│   ├── # 아이템 시스템
│   ├── items.py                # 아이템 정의
│   ├── event_to_string.py      # 이벤트 문자열
│   │
│   ├── # 리소스 관리
│   ├── image_asset_manager.py  # 이미지 에셋 관리
│   │
│   ├── monsters/               # 몬스터 패키지
│   │   ├── __init__.py
│   │   ├── cat_assassin.py
│   │   ├── cat_theif.py
│   │   ├── panther_assassin.py
│   │   └── Boss_Logic/         # 보스 패턴
│   │       ├── panther_assassin_1pattern.py
│   │       ├── panther_assassin_2pattern.py
│   │       ├── panther_assassin_3pattern.py
│   │       ├── panther_assassin_4pattern.py
│   │       ├── panther_assassin_5pattern.py
│   │       └── panther_assassin_6pattern.py
│   │
│   └── stages/                 # 스테이지 패키지
│       ├── __init__.py
│       ├── stage_1.py
│       ├── stage_2.py
│       └── stage_3.py
│
├── resources/                   # 리소스 폴더
│   ├── Fonts/                  # 폰트
│   │   └── pixelroborobo.otf
│   │
│   └── Texture_organize/       # 텍스처 (1,000+ 파일)
│       ├── Player_character/   # 플레이어 애니메이션
│       ├── Entity/             # 몬스터 및 NPC
│       ├── Weapon/             # 무기 및 이펙트
│       ├── VFX/                # 시각 효과
│       ├── UI/                 # UI 요소
│       ├── Map/                # 맵 타일
│       ├── Item/               # 아이템 아이콘
│       ├── Prologue/           # 프롤로그 시퀀스
│       └── ...
│
└── tools/                       # 개발 도구
    └── test_map_load.py        # 맵 로드 테스트

```

---

## 🛠️ 기술 스택

### 핵심 기술
- **Python 3.13**: 메인 프로그래밍 언어
- **pico2d**: 2D 게임 엔진
- **PIL/Pillow**: 이미지 처리

### 주요 시스템 구현
- **상태 머신 (State Machine)**: 캐릭터 상태 관리
- **행동 트리 (Behavior Tree)**: AI 의사결정
- **이벤트 시스템**: 게임 이벤트 처리
- **리소스 관리**: 이미지 에셋 최적화 로딩

### 디자인 패턴
- **Singleton Pattern**: 리소스 관리자
- **State Pattern**: 게임 모드 및 캐릭터 상태
- **Observer Pattern**: UI 업데이트
- **Component Pattern**: 게임 오브젝트 구성

---

## 📊 개발 통계

### 코드 통계
- **Python 파일**: 41개
- **코드 모듈**: 
  - 게임 시스템: 20개
  - AI 시스템: 10개
  - 스테이지: 4개
- **총 개발 규모**: 5,000+ 라인 (추정)

### 리소스 통계
- **PNG 이미지**: 1,000개 이상
- **애니메이션 프레임**: 
  - 플레이어: 150+ 프레임
  - VFX: 100+ 프레임
  - 프롤로그: 131 프레임
- **폰트**: 1개

### 주요 시스템
✅ 41개 Python 모듈  
✅ 1,000+ 그래픽 리소스  
✅ 6패턴 보스 AI  
✅ 3개 스테이지  
✅ 완전한 인벤토리 시스템  

*상세 통계는 [PROJECT_STATISTICS.md](PROJECT_STATISTICS.md)를 참조하세요.*

---

## 📚 개발 과정

### Phase 1: 기초 시스템 (Week 1-4)
- [x] 프로젝트 구조 설계
- [x] 기본 게임 프레임워크
- [x] 플레이어 캐릭터 기본 구현
- [x] 상태 머신 구현

### Phase 2: 핵심 게임플레이 (Week 5-8)
- [x] 전투 시스템
- [x] 인벤토리 및 장비 시스템
- [x] AI 시스템 (행동 트리)
- [x] 몬스터 구현

### Phase 3: 콘텐츠 확장 (Week 9-12)
- [x] 보스 패턴 구현
- [x] 스테이지 제작
- [x] UI/UX 개선

### Phase 4: 완성 및 최적화 (Week 13-16)
- [x] 프롤로그 시퀀스
- [x] VFX 및 사운드
- [x] 밸런싱
- [x] 버그 수정 및 최적화

---

## 🎓 학습 성과

이 프로젝트를 통해 다음을 학습하고 구현했습니다:

### 게임 프로그래밍
- ✅ 게임 루프 및 프레임워크 설계
- ✅ 상태 머신 패턴 구현
- ✅ 행동 트리 AI 구현
- ✅ 충돌 감지 및 물리 시뮬레이션
- ✅ 애니메이션 시스템

### 소프트웨어 엔지니어링
- ✅ 객체지향 프로그래밍 (OOP)
- ✅ 디자인 패턴 적용
- ✅ 모듈화 및 코드 구조화
- ✅ 리소스 관리 및 최적화

### 게임 디자인
- ✅ 게임 밸런싱
- ✅ 레벨 디자인
- ✅ UI/UX 디자인
- ✅ 플레이어 피드백 시스템

---

## 🐛 알려진 이슈

- [ ] 보스 패턴 간 전환 최적화 필요
- [ ] 특정 조건에서 메모리 사용량 증가

---

## 🔮 향후 계획

- [ ] 추가 보스 몬스터 구현
- [ ] 새로운 스테이지 추가
- [ ] 멀티플레이어 모드
- [ ] 업적 시스템
- [ ] 사운드 및 배경음악 추가
- [ ] 스토리 모드 확장
- [ ] 무기 시스템 구현 (리소스 완료, 구현 예정)

---

## 👥 기여

### 개발자
- **[민현규]** - 프로젝트 리드, 프로그래밍, 시스템 디자인

### 크레딧
- **그래픽 리소스**: [TEAM HORAY:Sephira] https://store.steampowered.com/app/2436940/_/
- **폰트**: Pixel Roborobo
- **pico2d**: Korea University Game Development Team

---

## 📄 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.

```
Copyright (c) 2025 [GODhanQ]
All rights reserved.

This project is for educational purposes only.
```

---

## 📞 연락처

- **Email**: hg.min2018@gmail.com
- **GitHub**: [@GODhanQ](https://github.com/GODhanQ)

---

## 🙏 감사의 말

이 프로젝트는 2025학년도 2학기 2D 게임 프로그래밍 수업의 일환으로 제작되었습니다.
지도해주신 교수님께 감사의 말씀을 드립니다.

---

<div align="center">

**⭐ 이 프로젝트가 마음에 드셨다면 Star를 눌러주세요! ⭐**

Made with ❤️ and Python

[맨 위로 올라가기](#-2dgp-game-project)

</div>
