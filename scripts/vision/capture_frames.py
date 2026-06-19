#!/usr/bin/env python3
"""Capture training frames from the robot camera.

Saves JPEG frames at an interval while you scatter toys, foam, hair, and
trash around the floor the robot will actually clean. Works with any camera
OpenCV can open, including the Kinect's color stream once libfreenect2's
v4l2 bridge or a UVC camera is in place.

Usage:
    python scripts/vision/capture_frames.py --out datasets/floor/images --seconds 120
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="datasets/floor/images", help="Output directory")
    parser.add_argument("--device", type=int, default=0, help="OpenCV camera index")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between frames")
    parser.add_argument("--seconds", type=float, default=120.0, help="Total capture time")
    args = parser.parse_args()

    try:
        import cv2
    except ImportError:
        print("install OpenCV first: pip install opencv-python")
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(args.device)
    if not cap.isOpened():
        print(f"cannot open camera {args.device}")
        return 1

    start = time.time()
    count = 0
    try:
        while time.time() - start < args.seconds:
            ok, frame = cap.read()
            if ok:
                path = out / f"frame_{int(time.time() * 1000)}.jpg"
                cv2.imwrite(str(path), frame)
                count += 1
                print(f"saved {path}")
            time.sleep(args.interval)
    finally:
        cap.release()
    print(f"captured {count} frames into {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
