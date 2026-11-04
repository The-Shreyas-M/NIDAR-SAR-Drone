#!/usr/bin/env python3
import rclpy
from rclpy.node import Node


class GcsNode(Node):
    def __init__(self):
        super().__init__("gcs_node")
        self.get_logger().info("gcs_node started (stub) - TODO: map receiver + planner")


def main(args=None):
    rclpy.init(args=args)
    node = GcsNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
