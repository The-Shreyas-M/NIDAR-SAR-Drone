from setuptools import find_packages, setup

package_name = "nidar_perception"

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
    description="NIDAR perception",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "aruco_detector = nidar_perception.aruco_detector:main",
            "person_fusion = nidar_perception.person_fusion:main",
        ],
    },
)
