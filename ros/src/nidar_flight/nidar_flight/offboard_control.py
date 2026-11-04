#!/usr/bin/env python3
import rclpy
from rclpy.node import Node


class OffboardControl(Node):
    def __init__(self):
        super().__init__("offboard_control")
        self.get_logger().info("offboard_control started (stub) - TODO: send setpoints to MAVROS")


def main(args=None):
    rclpy.init(args=args)
    node = OffboardControl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
