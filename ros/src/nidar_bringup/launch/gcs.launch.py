from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="nidar_gcs",
            executable="gcs_node",
            name="gcs_node",
            output="screen",
        ),
    ])
