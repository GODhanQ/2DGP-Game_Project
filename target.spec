# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# 바이너리 수집
binaries = []

# 프로젝트 폴더의 sdl2_dlls 디렉토리에서 DLL 찾기
project_dir = os.path.dirname(os.path.abspath(SPEC))
sdl2_dlls_dir = os.path.join(project_dir, 'sdl2_dlls')

if os.path.exists(sdl2_dlls_dir):
    print(f"\n[SDL2 DLL] sdl2_dlls 폴더에서 검색: {sdl2_dlls_dir}")
    dll_count = 0
    for file in os.listdir(sdl2_dlls_dir):
        if file.endswith('.dll'):
            dll_path = os.path.join(sdl2_dlls_dir, file)
            # DLL을 루트(.)와 sdl2dll 폴더 모두에 추가
            binaries.append((dll_path, '.'))
            binaries.append((dll_path, 'sdl2dll'))
            print(f"[SDL2 DLL] 추가: {file} (. 와 sdl2dll 폴더)")
            dll_count += 1
    if dll_count > 0:
        print(f"[SDL2 DLL] 총 {dll_count}개의 DLL 파일 포함됨\n")
    else:
        print("[SDL2 DLL] 경고: sdl2_dlls 폴더가 비어있습니다!\n")
else:
    print(f"\n[SDL2 DLL] 경고: {sdl2_dlls_dir} 폴더를 찾을 수 없습니다!")
    print("[SDL2 DLL] 다음 명령어로 SDL2 DLL을 설치하세요:")
    print("[SDL2 DLL]   python setup_sdl2.py\n")

# pico2d 데이터 및 바이너리 수집
try:
    pico2d_datas = collect_data_files('pico2d', include_py_files=True)
    pico2d_binaries = collect_dynamic_libs('pico2d')
    binaries += pico2d_binaries
    print(f"[pico2d] {len(pico2d_datas)}개의 데이터 파일 수집")
    print(f"[pico2d] {len(pico2d_binaries)}개의 바이너리 수집")
except Exception as e:
    print(f"[pico2d] 수집 중 오류: {e}")
    pico2d_datas = []

# pico2d 모듈 전체를 datas에 추가
try:
    import pico2d
    pico2d_module_path = os.path.dirname(pico2d.__file__)
    pico2d_datas.append((pico2d_module_path, 'pico2d'))
    print(f"[pico2d] 모듈 전체 포함: {pico2d_module_path}")
except ImportError as e:
    print(f"[pico2d] 경고: pico2d 모듈 경로를 찾을 수 없습니다: {e}")

# sdl2dll 모듈의 경로 찾기 및 완전히 포함
try:
    import sdl2dll
    sdl2dll_path = os.path.dirname(sdl2dll.__file__)
    # sdl2dll 모듈 전체를 datas에 추가
    datas_temp = [(sdl2dll_path, 'sdl2dll')]
    print(f"[sdl2dll] 경로: {sdl2dll_path}")
    print(f"[sdl2dll] 모듈 전체 포함")
except ImportError as e:
    print(f"[sdl2dll] 경고: sdl2dll 모듈을 찾을 수 없습니다: {e}")
    sdl2dll_path = None
    datas_temp = []

# SDL2 관련 데이터 수집
try:
    sdl2_datas = collect_data_files('sdl2')
except Exception as e:
    print(f"[SDL2] 데이터 수집 중 오류: {e}")
    sdl2_datas = []

# PIL/Pillow 서브모듈 수집
pillow_submodules = collect_submodules('PIL')

# SDL2 서브모듈 수집
sdl2_submodules = collect_submodules('sdl2')

# 게임 실행을 위해 필요한 데이터 파일들 수집 (먼저 초기화)
datas = [
    ('resources', 'resources'),  # resources 폴더 전체 포함
]

# pico2d, SDL2 데이터 추가
datas += pico2d_datas
datas += sdl2_datas
datas += datas_temp  # sdl2dll 모듈 전체 추가

# sdl2dll 서브모듈 수집
try:
    sdl2dll_submodules = collect_submodules('sdl2dll')
    print(f"[sdl2dll] {len(sdl2dll_submodules)}개의 서브모듈 발견")
except Exception as e:
    print(f"[sdl2dll] 서브모듈 수집 중 오류 (무시 가능): {e}")
    sdl2dll_submodules = []

# sdl2dll 데이터 파일 및 바이너리 수집
try:
    sdl2dll_datas = collect_data_files('sdl2dll')
    sdl2dll_binaries = collect_dynamic_libs('sdl2dll')
    datas += sdl2dll_datas
    binaries += sdl2dll_binaries
    print(f"[sdl2dll] {len(sdl2dll_datas)}개의 데이터 파일 발견")
    print(f"[sdl2dll] {len(sdl2dll_binaries)}개의 바이너리 파일 발견")
except Exception as e:
    print(f"[sdl2dll] 데이터 수집 중 오류 (무시 가능): {e}")

# 숨겨진 import (동적으로 로드되는 모듈들)
hiddenimports = [
    'pico2d',
    'sdl2dll',  # pico2d가 사용하는 SDL2 DLL 경로 모듈
    'PIL',
    'PIL.Image',
    'PIL._imaging',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'sdl2',
    'sdl2.ext',
    'sdl2.dll',
    'sdl2.sdlmixer',
    'sdl2.sdlimage',
    'sdl2.sdlttf',
    'sdl2.video',
    'sdl2.audio',
    'sdl2.events',
    'sdl2.surface',
    'sdl2.render',
    'sdl2.pixels',
    'sdl2.rect',
    'sdl2.rwops',
    'ctypes',
    'ctypes.util',
    'game_framework',
    'game_logic',
    'game_logic.player',
    'game_logic.cursor',
    'game_logic.inventory',
    'game_logic.ui_overlay',
    'game_logic.background',
    'game_logic.behavior_tree',
    'game_logic.damage_indicator',
    'game_logic.defeat_mode',
    'game_logic.equipment',
    'game_logic.event_to_string',
    'game_logic.image_asset_manager',
    'game_logic.item_entity',
    'game_logic.items',
    'game_logic.loading_screen',
    'game_logic.lobby_mode',
    'game_logic.map',
    'game_logic.play_mode',
    'game_logic.projectile',
    'game_logic.state_machine',
    'game_logic.stats',
    'game_logic.title_mode',
    'game_logic.vfx',
    'game_logic.victory_mode',
    'game_logic.monsters',
    'game_logic.monsters.cat_assassin',
    'game_logic.monsters.cat_theif',
    'game_logic.monsters.panther_assassin',
    'game_logic.monsters.Boss_Logic',
    'game_logic.monsters.Boss_Logic.panther_assassin_1pattern',
    'game_logic.monsters.Boss_Logic.panther_assassin_2pattern',
    'game_logic.monsters.Boss_Logic.panther_assassin_3pattern',
    'game_logic.monsters.Boss_Logic.panther_assassin_4pattern',
    'game_logic.monsters.Boss_Logic.panther_assassin_5pattern',
    'game_logic.monsters.Boss_Logic.panther_assassin_6pattern',
    'game_logic.stages',
    'game_logic.stages.stage_1',
    'game_logic.stages.stage_2',
    'game_logic.stages.stage_3',
]

# PIL, SDL2 서브모듈 추가
hiddenimports += pillow_submodules
hiddenimports += sdl2_submodules
hiddenimports += sdl2dll_submodules  # sdl2dll 서브모듈 추가

print(f"\n[빌드 정보] 총 {len(binaries)}개의 바이너리 포함")
print(f"[빌드 정보] 총 {len(datas)}개의 데이터 파일 포함")
print(f"[빌드 정보] 총 {len(hiddenimports)}개의 hidden imports 포함\n")

a = Analysis(
    ['main.py'],
    pathex=[sdl2dll_path] if sdl2dll_path else [],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'],  # 커스텀 훅 디렉토리 추가
    hooksconfig={},
    runtime_hooks=[],  # 런타임 훅 제거
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Game_2024180014',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX 압축 비활성화
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 콘솔 창 숨기기
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
