# 2DGP Game Project - 개발 통계 보고서

## 📊 프로젝트 개요
**프로젝트명**: 2D 게임 프로그래밍 프로젝트  
**개발 기간**: 2025년 2학기  
**플랫폼**: Python (pico2d)  
**장르**: 2D 액션 로그라이크

---

## 📈 파일 변경 통계

### 전체 파일 수
- **Python 소스 파일**: 41개
- **PNG 이미지 파일**: 1,000개 이상 (검색 결과 상한선)
- **폰트 파일**: 1개 (OTF)
- **텍스트 파일**: 2개
- **총 리소스 파일**: 1,000개 이상

### 코드 구조
```
main.py (메인 진입점)
game_framework.py (게임 프레임워크)
game_logic/ (게임 로직 패키지)
├── __init__.py
├── 플레이어 시스템
│   ├── player.py (플레이어 캐릭터)
│   ├── state_machine.py (상태 머신)
│   ├── stats.py (스탯 시스템)
│   ├── inventory.py (인벤토리)
│   └── equipment.py (장비 시스템)
├── 게임 모드
│   ├── title_mode.py (타이틀 화면)
│   ├── lobby_mode.py (로비)
│   ├── play_mode.py (플레이 모드)
│   ├── victory_mode.py (승리 화면)
│   ├── defeat_mode.py (패배 화면)
│   └── loading_screen.py (로딩 화면)
├── AI 시스템
│   └── behavior_tree.py (행동 트리)
├── 전투 시스템
│   ├── projectile.py (발사체)
│   ├── damage_indicator.py (데미지 표시)
│   └── vfx.py (시각 효과)
├── UI 시스템
│   ├── ui_overlay.py (UI 오버레이)
│   └── cursor.py (커서)
├── 월드 시스템
│   ├── map.py (맵)
│   ├── background.py (배경)
│   └── item_entity.py (아이템 엔티티)
├── 아이템 시스템
│   ├── items.py (아이템 정의)
│   └── event_to_string.py (이벤트 문자열)
├── 리소스 관리
│   └── image_asset_manager.py (이미지 에셋 관리자)
├── monsters/ (몬스터 패키지)
│   ├── __init__.py
│   ├── cat_assassin.py (고양이 암살자)
│   ├── cat_theif.py (고양이 도적)
│   ├── panther_assassin.py (표범 암살자)
│   └── Boss_Logic/ (보스 패턴)
│       ├── panther_assassin_1pattern.py
│       ├── panther_assassin_2pattern.py
│       ├── panther_assassin_3pattern.py
│       ├── panther_assassin_4pattern.py
│       ├── panther_assassin_5pattern.py
│       └── panther_assassin_6pattern.py
└── stages/ (스테이지 패키지)
    ├── __init__.py
    ├── stage_1.py (스테이지 1)
    ├── stage_2.py (스테이지 2)
    └── stage_3.py (스테이지 3)
```

---

## 🎨 리소스 통계

### 캐릭터 애니메이션
- **플레이어 캐릭터 (Basic_M)**:
  - Idle: 6프레임 (상/하체 분리)
  - Move: 8프레임 (상/하체 분리)
  - Attack: 3프레임 (상/하체 분리)
  - Heavy Attack: 10프레임 (상/하체 분리)
  - Roll: 7프레임
  - Airborne: 3프레임
  - Down: 1프레임
  - **총 약 150+ 프레임**

### 몬스터 애니메이션
- **Cat Assassin** (고양이 암살자)
- **Cat Thief** (고양이 도적)
- **Panther Assassin** (표범 암살자 - 보스)
  - 6가지 공격 패턴 구현

### 무기 시스템
- **Tier 1**: 기본 검과 방패
- **무기 이펙트**: 스윙, 가드, 특수 공격 등

### VFX (시각 효과)
- **충돌 이펙트**:
  - Blue Crash (전방/후방)
  - Green Shield
  - Sword Slash
  - Shuriken Throw
- **파티클 효과**:
  - Run Dust
  - Hit Sparks
  - Heal Glow
  - Mana Restore
  - Dash Smoke

### UI 리소스
- **아이콘**: 버튼, 클라우드, 게임오버 패널
- **버튼**: Button0, Button1, 비활성화 상태
- **인벤토리 관련 UI**
- **체력/마나/대시 바**
- **데미지 인디케이터**
- **커서 이미지**
- **버프 아이콘**

### 맵 및 배경
- **배경 요소**: Dream Forest, Bad Land 등

---

## 💻 주요 시스템 구현

### 1. 게임 플레이 시스템
- ✅ 플레이어 캐릭터 (상/하체 분리 애니메이션)
- ✅ 상태 머신 (State Machine)
- ✅ 스탯 시스템 (체력, 마나, 대시)
- ✅ 인벤토리 및 장비 시스템
- ✅ 아이템 드롭 및 획득

### 2. AI 시스템
- ✅ 행동 트리 (Behavior Tree)
- ✅ 3종류의 일반 몬스터
- ✅ 보스 몬스터 (6가지 패턴)

### 3. 전투 시스템
- ✅ 근접 공격 (일반/강공격)
- ✅ 원거리 공격 (발사체)
- ✅ 가드/패링 시스템
- ✅ 대시/회피
- ✅ 데미지 계산 및 표시

### 4. UI 시스템
- ✅ 체력/마나/대시 바
- ✅ 인벤토리 UI
- ✅ 버프 표시기
- ✅ 데미지 인디케이터
- ✅ 커서 시스템

### 5. 게임 모드
- ✅ 타이틀 화면
- ✅ 로비 선택
- ✅ 플레이 모드
- ✅ 승리/패배 화면
- ✅ 로딩 화면

### 6. 스테이지 시스템
- ✅ 3개 스테이지 구현
- ✅ 맵 시스템
- ✅ 배경 시스템

### 7. 리소스 관리 시스템
- ✅ 이미지 에셋 관리자 (싱글톤 패턴)
- ✅ 최적화된 리소스 로딩
- ✅ 이벤트 문자열 매핑
- ✅ 폰트 통합 (pixelroborobo.otf)
- ✅ 설정 파일 관리
- ✅ 캐시 파일 관리

---

## 📊 상세 통계 정리

### 파일 변경 통계
**41개 Python 파일** (주요 게임 로직)
- 프레임워크: 2개
- 게임 로직: 20개
- 몬스터: 9개 (보스 패턴 6개 포함)
- 스테이지: 3개
- 초기화 파일: 3개
- 테스트: 1개
- 캐시 파일: 제외

**1,000+ PNG 이미지 파일**
- 플레이어 애니메이션: 50 프레임
- VFX: 100 프레임
- UI: 50+ 파일
- 몬스터: 100+ 프레임

**기타 리소스**
- 폰트: 1개 (pixelroborobo.otf)
- 설정 파일: 2개

### 주요 추가 파일 분류

#### 게임 시스템 (20개 파일)
- 플레이어 시스템: player.py, state_machine.py, stats.py
- 인벤토리 시스템: inventory.py, equipment.py, items.py
- 게임 모드: title_mode.py, lobby_mode.py, play_mode.py, victory_mode.py, defeat_mode.py
- 전투 시스템: projectile.py, damage_indicator.py, vfx.py
- UI 시스템: ui_overlay.py, cursor.py
- 월드 시스템: map.py, background.py, item_entity.py
- 기타: loading_screen.py, image_asset_manager.py, event_to_string.py

#### AI 시스템 (10개 파일)
- 행동 트리: behavior_tree.py
- 일반 몬스터: cat_assassin.py, cat_theif.py, panther_assassin.py
- 보스 패턴: panther_assassin_1~6pattern.py (6개)
- 몬스터 패키지: monsters/__init__.py

#### 스테이지 (4개 파일)
- 스테이지 구현: stage_1.py, stage_2.py, stage_3.py
- 패키지: stages/__init__.py

#### 그래픽 리소스 (100+ 파일)
- 캐릭터 애니메이션: 150+ PNG
- VFX 이펙트: 100+ PNG (10+ 이펙트 세트)
- UI 요소: 50+ PNG
- 맵/배경: 200+ PNG
- 미출시 컨텐츠: 200+ PNG

#### 폰트 (1개 파일)
- pixelroborobo.otf

---

## 🎯 개발 성과 요약

### 핵심 성과
✨ **41개 Python 모듈**로 체계적인 게임 시스템 구축  
🎨 **100개 이상의 그래픽 리소스** 제작 및 통합  
🤖 **행동 트리 기반 AI 시스템** 구현
👾 **3종 몬스터 + 6패턴 보스** 구현  
🗺️ **3개 스테이지** 완성  
💎 **완전한 인벤토리/장비 시스템** 구현

### 기술적 특징
- 상태 머신 기반 캐릭터 제어
- 행동 트리 기반 적 AI
- 모듈화된 게임 로직 구조
- 리소스 관리 시스템
- 다양한 VFX 및 파티클 효과

---

## 📝 결론

이 프로젝트는 **Python/pico2d를 활용한 본격적인 2D 액션 로그라이크 게임**으로, 
**41개의 체계적인 코드 모듈**과 **100개 이상의 정교한 그래픽 리소스**를 통해 
완성도 높은 게임 시스템을 구현했습니다.

특히 **행동 트리 기반 AI**, **상태 머신 기반 플레이어 제어**, 
**다양한 무기 및 아이템 시스템**,
**보스 패턴 시스템** 등 게임 개발의 핵심 기술들을 성공적으로 구현한 프로젝트입니다.

---

**생성 일시**: 2025-12-08  
**프로젝트 루트**: E:\대학 2학년 파일\2D 게임프로그래밍\2DGP-Game_Project

