#!/usr/bin/env python3
import rclpy
from rclpy.node import Node


class PersonFusion(Node):
    def __init__(self):
        super().__init__("person_fusion")
        self.get_logger().info("person_fusion started (stub) - TODO: fuse IMX500 detections with LiDAR distance")


def main(args=None):
    rclpy.init(args=args)
    node = PersonFusion()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
