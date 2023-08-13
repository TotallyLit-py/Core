from pkg_resources import Distribution as __Distribution


def find_packages(name_pattern: str) -> list[__Distribution]:
    import re

    import pkg_resources

    return [
        package
        for package in pkg_resources.working_set
        if re.match(name_pattern, package.key)
    ]
