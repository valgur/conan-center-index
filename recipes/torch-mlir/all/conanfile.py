import json
import os
import re
import textwrap
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import check_min_cstd, check_min_cppstd, can_run, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class TorchMlirConan(ConanFile):
    name = "torch-mlir"
    description = "The Torch-MLIR project aims to provide first class support from the PyTorch ecosystem to the MLIR ecosystem."
    license = "Apache-2.0 WITH LLVM-exception OR BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/llvm/torch-mlir"
    topics = ("compiler", "pytorch", "mlir")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "onnx_c_importer": [True, False],
    }
    default_options = {
        "onnx_c_importer": False,
    }

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("stablehlo/[^1.6]")
        self.requires("llvm-core/[>=19]", run=can_run(self), options={"utils": can_run(self)})
        self.requires("mlir/[>=19]", transitive_headers=True, transitive_libs=True,
                      run=can_run(self), options={"tools": can_run(self), "install_aggregate_objects": True})
        if self.options.onnx_c_importer:
            self.requires("onnx/[^1.13]")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.settings.get_safe("compiler.cstd"):
            check_min_cstd(self, 11)

    def build_requirements(self):
        if not can_run(self):
            self.requires("llvm-core/<host_version>", options={"utils": True})
            self.requires("mlir/<host_version>", options={"tools": True, "install_aggregate_objects": True})

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        save(self, "python/CMakeLists.txt", "")
        save(self, "test/CMakeLists.txt", "")
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 17)", "")
        replace_in_file(self, "CMakeLists.txt", "add_custom_target(check-torch-mlir-all)", "")
        replace_in_file(self, "CMakeLists.txt", "add_dependencies(check-torch-mlir-all check-torch-mlir)", "")

    def generate(self):
        if can_run(self):
            venv = VirtualRunEnv(self)
            venv.generate(scope="build")

        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_torch-mlir_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["TORCH_MLIR_ENABLE_ONNX_C_IMPORTER"] = self.options.onnx_c_importer
        tc.cache_variables["TORCH_MLIR_USE_EXTERNAL_STABLEHLO"] = True
        tc.cache_variables["TORCH_MLIR_ENABLE_STABLEHLO"] = True
        tc.cache_variables["MLIR_ENABLE_BINDINGS_PYTHON"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        if Version(self.dependencies["stablehlo"].ref.version) >= "1.9":
            replace_in_file(self, os.path.join(self.source_folder, "lib", "InitAll.cpp"),
                            '#include "stablehlo/transforms/Passes.h"',
                            '#include "stablehlo/transforms/Passes.h"'
                            '#include "stablehlo/transforms/optimization/Passes.h"')
        cmake = CMake(self)
        self._configure_and_extract_build_info(cmake)
        cmake.build()

    def _configure_and_extract_build_info(self, cmake, **configure_kwargs):
        exclude_patterns = [
            "CONAN_LIB.*",
            "llvm-core.*",
            ".*_DEPS_TARGET",
        ]
        save(self, Path(self.build_folder) / "CMakeGraphVizOptions.cmake", textwrap.dedent(f"""
            set(GRAPHVIZ_EXECUTABLES OFF)
            set(GRAPHVIZ_MODULE_LIBS OFF)
            set(GRAPHVIZ_OBJECT_LIBS OFF)
            set(GRAPHVIZ_IGNORE_TARGETS "{';'.join(exclude_patterns)}")
        """))
        graphviz_args = configure_kwargs.pop("cli_args", []) + [f"--graphviz={self._graphviz_file}"]
        cmake.configure(**configure_kwargs, cli_args=graphviz_args)
        self._write_build_info("_conan_build_info.json")
        self._validate_components(self._build_info["components"])

    @property
    def _graphviz_file(self):
        return Path(self.build_folder) / f"{self.name}.dot"

    @cached_property
    def _build_info(self):
        return {
            "components": components_from_dotfile(self._graphviz_file.read_text()),
        }

    def _validate_components(self, components):
        for component, info in components.items():
            for req in info["requires"]:
                if "::" in req:
                    dep = req.split("::", 1)[0]
                    if dep not in self.dependencies.direct_host:
                        raise ConanException(f"Unexpected dependency for {component}: {req}")

    @property
    def _cmake_module_path(self):
        return Path("lib") / "cmake" / self.name

    @property
    def _package_build_info_file(self):
        return Path(self.package_folder) / self._cmake_module_path / "conan_build_info.json"

    def _write_build_info(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._build_info, indent=2))

    def _read_build_info(self) -> dict:
        return json.loads(self._package_build_info_file.read_text())

    @cached_property
    def _obj_dir(self):
        return Path(self.package_folder) / "lib" / f"objects-{self.settings.build_type}"

    @cached_property
    def _obj_libs(self):
        return {d.name.replace("obj.", ""): sorted(d.glob("*.o")) for d in self._obj_dir.iterdir() if d.is_dir()}

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        self._write_build_info(self._package_build_info_file)

        cmake_dir = Path(self.package_folder) / self._cmake_module_path
        self._write_export_executables_cmake(cmake_dir / "conan_add_executable_targets.cmake")
        self._write_export_objects_cmake(cmake_dir / "conan_add_object_targets.cmake")

    def _write_export_executables_cmake(self, cmake_file_path):
        bin_dir = Path(self.package_folder, "bin")
        content = 'get_filename_component(_IMPORT_PREFIX "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)\n\n'
        content += "\n".join(
            f"if(NOT TARGET {x.stem})\n"
            f"  add_executable({x.stem} IMPORTED)\n"
            f'  set_target_properties({x.stem} PROPERTIES IMPORTED_LOCATION "${{_IMPORT_PREFIX}}/bin/{x.name}")\n'
            "endif()\n"
            for x in sorted(bin_dir.iterdir()) if x.suffix not in {".dll", ".pdb"}
        )
        save(self, cmake_file_path, content)

    def _write_export_objects_cmake(self, cmake_file_path):
        build_type_upper = str(self.settings.build_type).upper()
        components = self._build_info["components"]
        content = [
            "include_guard()\n",
            'get_filename_component(_IMPORT_PREFIX "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)\n',
        ]
        for name, object_files in self._obj_libs.items():
            content.append(f"add_library(obj.{name} OBJECT IMPORTED)")
            content.append(f"set_property(TARGET obj.{name} APPEND PROPERTY IMPORTED_CONFIGURATIONS {build_type_upper})")
            formatted_obj_files = ";".join("${_IMPORT_PREFIX}/" + str(o.relative_to(self.package_folder)).replace("\\", "/") for o in object_files)
            content.append(f'set_property(TARGET obj.{name} APPEND PROPERTY IMPORTED_OBJECTS_{build_type_upper} "{formatted_obj_files}")')
            deps = ";".join(r for r in components[name]["requires"] if r.startswith("MLIR"))
            content.append(textwrap.dedent(f"""\
                set_target_properties({name} PROPERTIES
                    MLIR_AGGREGATE_DEP_LIBS_IMPORTED "{deps}"
                    MLIR_AGGREGATE_OBJECT_LIB_IMPORTED "obj.{name}"
                )"""))
            content.append("\n")
        save(self, cmake_file_path, "\n".join(content))

    def package_info(self):
        build_info = self._read_build_info()
        components = build_info["components"]
        for name, data in components.items():
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", name)
            component.libs = [name]
            component.resdirs = ["share"]
            component.requires = data["requires"]
            component.system_libs = data["system_libs"]
            if name == "TorchMLIRCAPI" and stdcpp_library(self):
                component.system_libs.append(stdcpp_library(self))

        found_libs = set(collect_libs(self))
        component_libs = set(sum((c.libs for _, c in self.cpp_info.components.items()), []))
        if component_libs - found_libs:
            self.output.warning(f"Some component libraries were not found in lib/: {component_libs - found_libs}")
        if found_libs - component_libs:
            self.output.warning(f"Some libraries were not declared as components: {found_libs - component_libs}")

        self.cpp_info.builddirs.append(self._cmake_module_path)
        self.cpp_info.set_property("cmake_build_modules", [
            self._cmake_module_path / "conan_add_executable_targets.cmake",
            self._cmake_module_path / "conan_add_object_targets.cmake",
        ])

        if self.options.onnx_c_importer:
            self.cpp_info.components["_executables"].requires = ["onnx::onnx"]

def parse_dotfile(dotfile, label_replacements=None):
    """
    Load the dependency graph defined by the nodes and edges in a dotfile.
    """
    label_replacements = label_replacements or {}
    labels = {}
    for node, label in re.findall(r'^\s*"(node\d+)"\s*\[\s*label\s*=\s*"(.+?)"', dotfile, re.MULTILINE):
        labels[node] = label_replacements.get(label, label)
    components = {l: [] for l in labels.values()}
    for src, dst in re.findall(r'^\s*"(node\d+)"\s*->\s*"(node\d+)"', dotfile, re.MULTILINE):
        components[labels[src]].append(labels[dst])
    return components


def components_from_dotfile(dotfile):
    """
    Parse the dotfile generated by the
    [cmake --graphviz](https://cmake.org/cmake/help/latest/module/CMakeGraphVizOptions.html)
    option to generate the list of available LLVM CMake targets and their inter-component dependencies.

    In future a [CPS](https://cps-org.github.io/cps/index.html) format could be used, or generated directly
    by the LLVM build system
    """
    known_system_libs = {"dl", "m", "pthread", "rt"}
    components = {}
    for component, deps in parse_dotfile(dotfile).items():
        if not component.startswith("TorchMLIR") or component.endswith("Sources"):
            continue
        requires = []
        system_libs = []
        for dep in deps:
            if dep.startswith("LLVM"):
                dep = f"llvm-core::{dep}"
            if dep.startswith("MLIR"):
                dep = f"mlir::{dep}"
            if dep.startswith("Stablehlo") or dep in {"ChloOps"}:
                dep = f"stablehlo::{dep}"
            if dep in known_system_libs:
                system_libs.append(dep)
            else:
                requires.append(dep)
        components[component] = {
            "requires": requires,
            "system_libs": system_libs,
        }
    return components
