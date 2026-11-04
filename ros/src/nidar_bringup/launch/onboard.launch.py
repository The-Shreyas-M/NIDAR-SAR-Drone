from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    mavros_launch = os.path.join(
        get_package_share_directory("mavros"), "launch", "apm.launch"
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("fcu_url", default_value="/dev/ttyAMA0:921600"),

        # MAVROS (ArduPilot) - FC via UART
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(mavros_launch),
            launch_arguments={
                "fcu_url": LaunchConfiguration("fcu_url"),
                "gcs_url": "udp://@",
            }.items(),
        ),

        # Camera (IMX500 human detection publisher)
        Node(
            package="nidar_camera",
            executable="imx500_detector",
            name="imx500_detector",
            output="screen",
        ),

        # Frame publisher for video stream to GCS
        Node(
            package="nidar_camera",
            executable="imx500_video_publisher",
            name="imx500_video_publisher",
            parameters=[{"width": 640, "height": 480, "fps": 20.0}],
            output="screen",
        ),

        # LiDAR driver (RPLidar C1)
        Node(
            package="lgdx_rplidar_c1",
            executable="rplidar_c1_node",
            name="rplidar_c1_node",
            parameters=[{
                "serial_port": "/dev/ttyUSB0",
                "serial_baudrate": 460800,
                "frame_id": "laser",
                "inverted": False,
                "angle_compensate": True,
            }],
            output="screen",
        ),

        # EKF (robot_localization) - fuse IMU + odometry
        Node(
            package="robot_localization",
            executable="ekf_node",
            name="ekf_filter_node",
            parameters=["config/ekf.yaml"],
            output="screen",
        ),

        # SLAM (slam_toolbox async)
        Node(
            package="slam_toolbox",
            executable="async_slam_toolbox_node",
            name="slam_toolbox",
            parameters=["config/slam_toolbox.yaml"],
            output="screen",
        ),

        # ArUco landing pad detector
        Node(
            package="nidar_perception",
            executable="aruco_detector",
            name="aruco_detector",
            parameters=[{"marker_size": 0.3, "marker_id": 0}],
            output="screen",
        ),

        # Person detection + distance fusion
        Node(
            package="nidar_perception",
            executable="person_fusion",
            name="person_fusion",
            output="screen",
        ),

        # Offboard control / mission state machine
        Node(
            package="nidar_navigation",
            executable="mission_manager",
            name="mission_manager",
            output="screen",
        ),
    ])
