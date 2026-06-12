# Fusion naming (all names, one system)

KARAKURI is the umbrella project. Each Japanese name maps to one subsystem. You do not pick one name; you use all of them.

| Codename | Japanese | Ring | Path | Role |
|----------|----------|------|------|------|
| **KODAMA** | 木霊 | 0 | `core/` | Immutable guardian: STOP, watchdog, permissions |
| **KAGE** | 影 | 1 | `mutable/` | Shadow body: self-rewriting playbooks and code |
| **MIRAI** | 未来 | 2 | `sandbox/` | Future experiments before they go live |
| **TSUKUMO** | 付喪 | - | `memory/` | Awakening memory: audit, cache, trust, queues |
| **RAIKO** | 雷光 | - | `karakuri/research/` | Fast allowlisted web research |
| **SHIKAI** | 視界 | 3 | `robot/shikai/` | Vision: YOLO classes, camera topics |
| **MUSUBI** | 結 | 3 | `robot/musubi/` | Binding: pick toy, place in box |
| **HANE** | 羽 | 3 | `robot/hane/` | Feather: vacuum foam, hair, crumbs |
| **SENRAI** | 千来 | - | `memory/web/` | Many arrivals: search queue and fetch cache |
| **KARAKURI** | 絡繰 | all | repo root | Clockwork whole: the living machine |

## CLI by subsystem

```powershell
# KODAMA core
karakuri doctor
karakuri stop
karakuri run --once

# RAIKO / SENRAI web
karakuri research query "ROS2 floor pick and place"
karakuri research run --once

# KAGE / MIRAI promotion
karakuri promote --dry-run
karakuri promote --canary sandbox/canary/example_playbook.yaml
```

## Python bridge

```python
from karakuri.robot import load_mission_config

mission = load_mission_config()
# SHIKAI, MUSUBI, HANE configs merged
```

## Display name

Set in `.env`:

```env
KARAKURI_DISPLAY_NAME=KARAKURI
```

For docs you can write: **KARAKURI fusion stack (KODAMA · KAGE · RAIKO · SHIKAI · MUSUBI · HANE · MIRAI · TSUKUMO · SENRAI)**
