from io import TextIOWrapper as __TextIOWrapper
from sys import stdout as __stdout
from typing import Callable as __Callable


# TODO: extract the typing/.pyi bits to simplify this function
#
# Also: add some tests for this, specifically.
# I'm not passionate about spending lots of time on tests (due to time constraints)
# but this deserved them.
#
def load_globals(
    package_pattern: str,
    submodule_prefix: str,
    submodule_pattern: str,
    pyi_output_file: str = None,
    verbose: bool = True,
    ignore_packages: list[str] = [],
    sys_module_name: str = None,
    print_to: __TextIOWrapper = __stdout,
    exclude_variable_patterns: list[str] = [r"^__.*", r"^[A-Z].*"],
    include_variable_patterns: list[str] = [],
    pyi_template: str = "",
) -> None:
    from .find_package_submodules import find_package_submodules

    extension_submodule_names = find_package_submodules(
        package_pattern,
        submodule_prefix,
        submodule_pattern,
        ignore_packages=ignore_packages,
        verbose=verbose,
        print_to=print_to,
    )

    if not extension_submodule_names:
        return

    import importlib
    import re
    import sys
    from typing import get_type_hints

    pyi_imports = set()
    pyi_contents: str = pyi_template
    class_name_occurrences: dict[str, int] = {}

    def extract_types(type_str: str) -> list[str]:
        # Regex to match anything inside square brackets, allowing for nested brackets
        matches = re.findall(r"\[([^]]+)]", type_str)
        # Split by commas but only those outside of nested brackets
        split_types = re.split(r",\s*(?![^[]*\])", matches[-1])
        return split_types

    def type_hint_without_namespaces(type_str: str, class_name_occurrences: dict):
        # Extract anything inside square brackets
        matches = re.findall(r"\[([^]]+)]", type_str)

        if matches:
            # Split by commas outside of nested brackets
            split_types = re.split(r",\s*(?![^[]*\])", matches[-1])
            simple_types = []
            for type_ in split_types:
                class_name = type_.rsplit(".", 1)[-1]
                occurrence_count = class_name_occurrences.get(class_name, 0) + 1
                class_name_occurrences[class_name] = occurrence_count
                alias_name = (
                    class_name
                    if occurrence_count == 1
                    else f"{class_name}{occurrence_count}"
                )
                simple_types.append(alias_name)
            # Replace the original type hint with the simple class names
            return type_str.replace(matches[-1], ", ".join(simple_types))

        return type_str.rsplit(".", 1)[-1]

    for submodule_name in extension_submodule_names:
        submodule = importlib.import_module(submodule_name)
        submodule_type_hints = get_type_hints(submodule)
        for key, value in submodule.__dict__.items():
            should_exclude = any(
                re.match(pattern, key) for pattern in exclude_variable_patterns
            )
            should_include = any(
                re.match(pattern, key) for pattern in include_variable_patterns
            )
            if should_exclude or (include_variable_patterns and not should_include):
                continue

            if sys_module_name:
                print(f"sys.modules[{sys_module_name}][{key}] = {value}")
                setattr(sys.modules[sys_module_name], key, value)

            if pyi_output_file:
                variable_type_hint = str(submodule_type_hints.get(key))

                # Hack - run this first because it increments the class occurrence counts
                simple_type_hint = type_hint_without_namespaces(
                    variable_type_hint, class_name_occurrences
                )

                discovered_types = extract_types(variable_type_hint)
                for discovered_type in discovered_types:
                    module_name, class_name = discovered_type.rsplit(".", 1)
                    occurrence_count = class_name_occurrences.get(class_name, 1)
                    alias_name = (
                        class_name
                        if occurrence_count == 1
                        else f"{class_name}{occurrence_count}"
                    )
                    if class_name == alias_name:
                        pyi_imports.add(f"from {module_name} import {class_name}")
                    else:
                        pyi_imports.add(
                            f"from {module_name} import {class_name} as {alias_name}"
                        )

                pyi_contents += f"{key}: {simple_type_hint}\n"

    pyi_import_contents: str = "\n".join(sorted(pyi_imports))
    pyi_contents = f"{pyi_import_contents}\n\n{pyi_contents}"

    if pyi_output_file:
        with open(pyi_output_file, "w") as pyi_file:
            pyi_file.write(pyi_contents)
        if verbose:
            print_to.write(
                f"Wrote pyi file '{pyi_output_file}' with contents:\n'{pyi_contents}'\n"
            )
