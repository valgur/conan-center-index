#! /usr/bin/python

# Generate a modules.json file from VTK source directly.
# This file is also generated by VTK cmake during the build,
# but only for the modules that were actually built.

# This recipe needs to know all the module information,
# so this information has to be gathered and stored with the recipe
# when new versions of VTK are added to this recipe.

import argparse
import json
from pathlib import Path

# Based on https://gitlab.kitware.com/vtk/vtk/-/blob/v9.3.1/CMake/vtkModule.cmake?ref_type=tags#L262-266
OPTIONS = {
    "implementable",
    "exclude_wrap",
    "third_party",
    "include_marshal",
}
SINGLE_VALUE = {
    "library_name",
    "name",
    "kit",
    "spdx_download_location",
    "spdx_custom_license_file",
    "spdx_custom_license_name",
    # Moved from MULTI_VALUE
    "spdx_license_identifier",
    "description",
}
MULTI_VALUE = {
    "groups",
    "depends",  # if one of these is no, then this module will not be built
    "private_depends",  # if one of these is no, then this module will not be built
    "optional_depends",  # if one of these is no, does not stop the module from building
    "order_depends",
    "test_depends",
    "test_optional_depends",
    "test_labels",
    "condition",
    "implements",
    "license_files",
    "spdx_copyright_text",
}

def parse_vtk_module(path):
    with open(path, "r", encoding="utf8") as f:
        lines = f.readlines()
    module = {}
    key = None
    values = []
    for line in lines:
        if line.startswith("#") or line == "\n":
            continue
        if line.startswith("  "):
            values.append(line.strip())
        else:
            if key is None and values:
                raise RuntimeError("Unexpected values without any key")
            if key is not None:
                module[key] = values
            key = line.strip().lower()
            values = []
    if key is not None:
        module[key] = values
    for key, values in list(module.items()):
        if key in OPTIONS:
            module[key] = True
        elif key in SINGLE_VALUE:
            if len(values) != 1:
                raise RuntimeError(f"Expected single value for {key}, got {values}")
            module[key] = values[0]
        elif key in MULTI_VALUE:
            module[key] = values
    return module


def find_vtk_modules(root, name="vtk.module", exclude=("Examples", "Testing")):
    root = Path(root)
    for path in root.rglob(name):
        rel_path = path.relative_to(root)
        if not str(rel_path).startswith(exclude):
            yield path


def load_vtk_module_details(root):
    modules = {}
    for path in find_vtk_modules(root, "vtk.module"):
        module_info = parse_vtk_module(path)
        module_info["path"] = str(path.parent.relative_to(root))
        name = module_info["name"]
        del module_info["name"]
        modules[name] = module_info
    return modules

def load_vtk_kit_details(root):
    kits = {}
    for path in find_vtk_modules(root, "vtk.kit"):
        kit_info = parse_vtk_module(path)
        kit_info["path"] = str(path.parent.relative_to(root))
        name = kit_info["name"]
        del kit_info["name"]
        kits[name] = kit_info
    return kits

def load_vtk_info(root):
    return {
        "modules": load_vtk_module_details(root),
        "kits": load_vtk_kit_details(root),
    }

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Conan VTK Recipe Helper for adding new VTK versions to recipe - tool for extracting module information from VTK source",
    )
    parser.add_argument("source_path")
    args = parser.parse_args(argv)
    info = load_vtk_info(args.source_path)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
