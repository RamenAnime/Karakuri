#!/usr/bin/env python3
"""Train the SHIKAI floor model and export it where the config expects it.

Label your captured frames first (Roboflow or labelImg both work) using
exactly the six classes from robot/shikai/config.yaml, export in YOLO format
with a data.yaml, then:

    pip install ultralytics
    python scripts/vision/train_yolo.py --data datasets/floor/data.yaml

The trained weights land at models/floor_objects.pt, the path SHIKAI's
config already points at. Start from yolov8n: it is small enough for a Pi.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

CLASSES = ["toy", "toy_box", "foam_bit", "hair_clump", "trash", "floor"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Path to the YOLO data.yaml")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--base", default="yolov8n.pt", help="Base weights")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        print("install ultralytics first: pip install ultralytics")
        return 1

    print(f"classes expected by SHIKAI: {CLASSES}")
    model = YOLO(args.base)
    results = model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz)
    best = Path(results.save_dir) / "weights" / "best.pt"
    target = Path("models/floor_objects.pt")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, target)
    print(f"exported {best} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
