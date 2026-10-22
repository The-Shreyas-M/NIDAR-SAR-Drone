#!/usr/bin/python3
"""bag_to_video.py - rebuild an .mp4 from a bag's CompressedImage topic.

Usage: python3 bag_to_video.py <bag_dir> [out.mp4] [--topic T]

Reads JPEG frames from the bag in time order and writes them out with
cv2.VideoWriter, so teammates can go bag -> video deterministically.
"""
import argparse
import os
import sys

import cv2
import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

DEFAULT_TOPIC = "/imx500/image_raw/compressed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bag")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--topic", default=DEFAULT_TOPIC)
    ap.add_argument("--fps", type=float, default=0.0,
                    help="0 = derive from bag timestamps")
    a = ap.parse_args()

    out = a.out or os.path.join(a.bag, "video.mp4")

    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=a.bag, storage_id="mcap"),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr",
            output_serialization_format="cdr",
        ),
    )
    types = {t.name: t.type for t in reader.get_all_topics_and_types()}
    if a.topic not in types:
        print(f"no {a.topic} in bag. topics: {list(types)}", file=sys.stderr)
        return 1
    cls = get_message(types[a.topic])

    frames = []
    stamps = []
    while reader.has_next():
        topic, data, stamp = reader.read_next()
        if topic != a.topic:
            continue
        msg = deserialize_message(data, cls)
        buf = np.frombuffer(msg.data, dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if img is None:
            continue
        frames.append(img)
        stamps.append(stamp / 1e9)

    if not frames:
        print("no decodable frames", file=sys.stderr)
        return 1

    if a.fps > 0:
        fps = a.fps
    else:
        span = max(stamps[-1] - stamps[0], 1e-6)
        fps = (len(frames) - 1) / span if len(frames) > 1 else 20.0
    fps = max(1.0, min(fps, 60.0))

    h, w = frames[0].shape[:2]
    vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for f in frames:
        if f.shape[1] != w or f.shape[0] != h:
            f = cv2.resize(f, (w, h))
        vw.write(f)
    vw.release()

    print(f"frames={len(frames)} fps={fps:.2f} {w}x{h} -> {out} "
          f"({os.path.getsize(out)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
