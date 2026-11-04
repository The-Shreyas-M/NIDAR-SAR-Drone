from setuptools import find_packages, setup

package_name = "nidar_camera"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="user",
    maintainer_email="user@localhost",
    description="NIDAR IMX500 camera",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "imx500_detector = nidar_camera.imx500_detector:main",
            "imx500_video_publisher = nidar_camera.imx500_video_publisher:main",
        ],
    },
)
