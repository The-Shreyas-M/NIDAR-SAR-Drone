#!/usr/bin/python3
"""bag_to_csv.py - dump /imx500/detections from a ROS 2 bag into a CSV.

Usage: python3 bag_to_csv.py <bag_dir> [output.csv]

One row per detection (not per message):
  t_sec, frame_stamp, n_dets_in_msg, class_id, score, x, y, w, h
Run on the Pi where ROS 2 + vision_msgs are installed.
"""
import csv
import os
import sys

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bag = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(bag, "detections.csv")

    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=bag, storage_id="mcap"),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr",
            output_serialization_format="cdr",
        ),
    )
    topic_types = {t.name: t.type for t in reader.get_all_topics_and_types()}
    if "/imx500/detections" not in topic_types:
        print(f"no /imx500/detections in bag (have: {list(topic_types)})", file=sys.stderr)
        return 1
    msg_cls = get_message(topic_types["/imx500/detections"])

    rows = 0
    msgs = 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_sec", "frame_stamp", "n_dets_in_msg",
                    "class_id", "score", "x", "y", "w", "h"])
        while reader.has_next():
            topic, data, stamp = reader.read_next()
            if topic != "/imx500/detections":
                continue
            msgs += 1
            msg = deserialize_message(data, msg_cls)
            t = stamp / 1e9
            n = len(msg.detections)
            for d in msg.detections:
                cx = d.bbox.center.position.x
                cy = d.bbox.center.position.y
                sx, sy = d.bbox.size_x, d.bbox.size_y
                for r in d.results:
                    w.writerow([f"{t:.6f}",
                                f"{msg.header.stamp.sec}.{msg.header.stamp.nanosec:09d}",
                                n, r.hypothesis.class_id,
                                f"{r.hypothesis.score:.4f}",
                                f"{cx - sx / 2:.1f}", f"{cy - sy / 2:.1f}",
                                f"{sx:.1f}", f"{sy:.1f}"])
                    rows += 1
    print(f"messages={msgs} detection_rows={rows} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
