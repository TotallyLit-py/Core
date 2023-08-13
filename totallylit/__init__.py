from .internal.extension_lookup.load_globals import load_globals as __load_globals

print(f"Loading __init__ file: {__file__}")

__load_globals(
    package_pattern=r"^totallylit-(.*)",
    submodule_prefix="_totallylit.extensions.",
    submodule_pattern=r"^_totallylit\.extensions\..*\.globals",
    pyi_output_file=f"{__file__}i",
    ignore_packages=["totallylit-core"],
)

print("Loaded.")
