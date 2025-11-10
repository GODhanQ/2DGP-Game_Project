# Add project root to sys.path so imports work when running from tools/
import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from game_logic.map import Map

room_path = os.path.join(project_root, 'resources', 'Room.txt')
print('Testing Room file at:', room_path)

m = Map(tile_size=48)
m.load_from_room_txt(room_path)
print('width,height:', m.width, m.height)

world = {k: [] for k in ['ground', 'upper_ground', 'walls', 'effects_back', 'effects_front', 'ui', 'cursor']}
m.build_into_world(world, tile_size=48, origin=(0, 0))
for k in ['ground', 'upper_ground', 'walls']:
    print(f"layer {k}: {len(world.get(k, []))} entities")

# print first 8 rows of parsed ground layer (raw rows) for inspection
print('\nSample parsed ground rows (first 12 rows):')
for i, row in enumerate(m.layers.get('ground', [])[:12]):
    print(i, row)

# count non-zero tokens per row
print('\nNon-zero counts per ground row:')
for i, row in enumerate(m.layers.get('ground', [])):
    nz = sum(1 for v in row if v != 0)
    print(i, nz)

# show sample entities before change
print('\nSample ground entities (before):')
for i, ent in enumerate(world['ground'][:5]):
    print(i, 'tile_id=', getattr(ent, 'tile_id', None), 'size=', getattr(ent, 'size', None), 'x=', getattr(ent, 'x', None), 'y=', getattr(ent, 'y', None), 'grid=', getattr(ent, '_grid_col', None), getattr(ent, '_grid_row', None))

# change tile size at runtime
new_size = 64
print(f'\nApplying new tile size: {new_size} via Map.set_tile_size(...)')
m.set_tile_size(new_size, world=world, origin=(0,0))

# show sample entities after change
print('\nSample ground entities (after):')
for i, ent in enumerate(world['ground'][:5]):
    print(i, 'tile_id=', getattr(ent, 'tile_id', None), 'size=', getattr(ent, 'size', None), 'x=', getattr(ent, 'x', None), 'y=', getattr(ent, 'y', None), 'grid=', getattr(ent, '_grid_col', None), getattr(ent, '_grid_row', None))

print('\nDone')
