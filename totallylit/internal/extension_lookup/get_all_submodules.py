def get_all_submodules(package_toplevel_module):
    import importlib
    import pkgutil

    def iterate_modules(package_paths, full_path):
        for path in package_paths:
            for importer, name, _ in pkgutil.iter_modules([path]):
                sub_module_path = path + "/" + name
                full_module_name = f"{full_path}.{name}"

                # If it's a package, recurse
                if importer.find_spec(full_module_name).submodule_search_locations:
                    yield from iterate_modules([sub_module_path], full_module_name)
                yield full_module_name

    imported_package = importlib.import_module(package_toplevel_module)

    # Check if the imported package has a _path attribute, and use that if it does
    # This is the case when import_module returns a _NamespacePath
    package_path = (
        imported_package._path
        if hasattr(imported_package, "_path")
        else [imported_package.__path__[0]]
    )

    return iterate_modules(package_path, package_toplevel_module)
