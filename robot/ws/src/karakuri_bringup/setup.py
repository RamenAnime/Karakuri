from setuptools import setup

package_name = "karakuri_bringup"

setup(
    name=package_name,
    version="0.8.2",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/simulation.launch.py", "launch/hardware.launch.py"]),
        (f"share/{package_name}/config", ["config/controllers.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="KARAKURI Maintainers",
    maintainer_email="maintainer@example.com",
    description="KARAKURI bringup launch package.",
    license="MIT",
)
