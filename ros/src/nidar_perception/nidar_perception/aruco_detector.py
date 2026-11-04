#!/usr/bin/env python3
import rclpy
from rclpy.node import Node


class ArucoDetector(Node):
    def __init__(self):
        super().__init__("aruco_detector")
        self.get_logger().info("aruco_detector started (stub) - TODO: detect ArUco launchpad marker")


def main(args=None):
    rclpy.init(args=args)
    node = ArucoDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
