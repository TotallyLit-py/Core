from io import TextIOWrapper as __TextIOWrapper
from sys import stdout as __stdout


def find_package_submodules(
    package_pattern: str,
    submodule_prefix: str,
    submodule_pattern: str,
    ignore_packages: list[str] = [],
    verbose: bool = True,
    print_to: __TextIOWrapper = __stdout,
) -> list[str]:
    from .find_packages import find_packages

    packages = find_packages(package_pattern)
    if not packages:
        return []

    import re

    from .get_all_submodules import get_all_submodules

    submodules: list[str] = []

    for package in packages:
        if package.key in ignore_packages:
            continue

        package_pattern_match = re.match(package_pattern, package.key)
        if (
            package_pattern_match
            and package_pattern_match.groups()
            and len(package_pattern_match.groups()) == 1
            and package_pattern_match.group(1)
        ):
            package_toplevel_module = submodule_prefix + package_pattern_match.group(1)

            try:
                for submodule_name in get_all_submodules(package_toplevel_module):
                    if re.match(submodule_pattern, submodule_name):
                        submodules.append(submodule_name)
                    if verbose and print_to:
                        print_to.write(
                            f"[totallylit] Found submodule {submodule_name}\n"
                        )
            except ModuleNotFoundError:
                if verbose and print_to:
                    print_to.write(
                        "[totallylit] Could not import package "
                        + f"{package_toplevel_module}\n"
                    )
    return submodules
