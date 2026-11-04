#!/usr/bin/python3
"""imx500_video_publisher - publish IMX500 camera frames as ROS 2 messages.

Publishes sensor_msgs/msg/CompressedImage (JPEG) on /imx500/image_raw/compressed
so the frames land in a rosbag and can be replayed/exported by anyone.

The camera is exclusive: stop `imx500_detector` first (and vice versa).

Usage:
  source /opt/ros/lyrical/setup.bash
  python3 imx500_video_publisher.py [--width 640] [--height 480] [--fps 20]
                                    [--quality 80] [--topic /imx500/image_raw/compressed]
"""
import argparse
import time

import cv2
import rclpy
from picamera2 import Picamera2
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage


class IMX500VideoPublisher(Node):
    def __init__(self, args):
        super().__init__("imx500_video_publisher")
        self.args = args
        self.pub = self.create_publisher(CompressedImage, args.topic, 10)
        self.picam2 = Picamera2()

        cfg = None
        for make in (
            lambda: self.picam2.create_video_configuration(
                main={"size": (args.width, args.height), "format": "RGB888"},
                controls={"FrameRate": args.fps},
                buffer_count=4,
            ),
            lambda: self.picam2.create_preview_configuration(
                main={"size": (args.width, args.height), "format": "RGB888"},
                buffer_count=4,
            ),
        ):
            try:
                cfg = make()
                break
            except Exception as exc:  # control not supported by this sensor
                self.get_logger().warn(f"config attempt failed: {exc}")
        if cfg is None:
            raise RuntimeError("could not configure IMX500 camera")
        self.picam2.configure(cfg)
        self.picam2.start()
        time.sleep(1.0)

        self.frames = 0
        self.t0 = time.time()
        self.get_logger().info(
            f"publishing {args.width}x{args.height} @ ~{args.fps}fps "
            f"jpeg q={args.quality} -> {args.topic}"
        )

    def publish_frame(self):
        arr = self.picam2.capture_array("main")
        if arr is None:
            return
        # picamera2 "RGB888" on this pipeline yields BGR-ordered bytes, which is
        # what cv2.imencode expects. Swapping channels here turns people blue.
        bgr = arr
        ok, buf = cv2.imencode(
            ".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), self.args.quality]
        )
        if not ok:
            return
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imx500"
        msg.format = "jpeg"
        msg.data = buf.tobytes()
        self.pub.publish(msg)
        self.frames += 1
        if self.frames % 100 == 0:
            dt = max(time.time() - self.t0, 1e-6)
            self.get_logger().info(f"frames={self.frames} ({self.frames / dt:.1f} fps)")

    def shutdown(self):
        try:
            self.picam2.stop()
        except Exception:
            pass
        dt = max(time.time() - self.t0, 1e-6)
        self.get_logger().info(
            f"stopped: {self.frames} frames in {dt:.1f}s ({self.frames / dt:.1f} fps)"
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--quality", type=int, default=80)
    ap.add_argument("--topic", default="/imx500/image_raw/compressed")
    args, ros_args = ap.parse_known_args()

    rclpy.init(args=ros_args)
    node = None
    try:
        node = IMX500VideoPublisher(args)
        period = 1.0 / max(args.fps, 1)
        while rclpy.ok():
            start = time.time()
            node.publish_frame()
            rclpy.spin_once(node, timeout_sec=0.0)
            elapsed = time.time() - start
            if elapsed < period:
                time.sleep(period - elapsed)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.shutdown()
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
