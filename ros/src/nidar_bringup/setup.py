from setuptools import find_packages, setup

package_name = "nidar_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", [
            "launch/onboard.launch.py",
            "launch/gcs.launch.py",
        ]),
        ("share/" + package_name + "/config", [
            "config/onboard_params.yaml",
        ]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="user",
    maintainer_email="user@localhost",
    description="NIDAR bringup",
    license="Apache-2.0",
)
