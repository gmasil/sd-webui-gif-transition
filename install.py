"""Script to install requirements on webui startup"""

import os

import launch
import pkg_resources

req_file: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt")


def is_installed(package_name: str, package_version: None | str = None) -> bool:
    """Check if package is installed, optionally verify correct version"""
    try:
        installed_version: str = pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return False
    return package_version in (None, installed_version)


# install requirements
with open(req_file, encoding="utf-8") as file:
    for requirement in file:
        requirement = requirement.strip()
        split: list[str] = requirement.split("==")
        lib = split[0].strip()
        version: None | str = split[1].strip() if len(split) > 1 else None
        if not is_installed(lib, version):
            launch.run_pip(f"install {requirement}", f"sd-webui-gif-transition requirement: {requirement}")
