#!/usr/bin/env python3
import rclpy
from rclpy.node import Node


class MissionManager(Node):
    def __init__(self):
        super().__init__("mission_manager")
        self.get_logger().info("mission_manager started (stub) - TODO: state machine (takeoff trigger, auto-land)")


def main(args=None):
    rclpy.init(args=args)
    node = MissionManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
