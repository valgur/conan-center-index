import json
import os
import re
import textwrap
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import check_min_cstd, check_min_cppstd, can_run
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class StableHLOConan(ConanFile):
    name = "stablehlo"
    description = (
        "StableHLO is an operation set for high-level operations (HLO) in machine learning (ML) models. "
        "Essentially, it's a portability layer between different ML frameworks and ML compilers: "
        "ML frameworks that produce StableHLO programs are compatible with ML compilers that consume StableHLO programs."
    )
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/openxla/stablehlo"
    topics = ("machine-learning", "hlo", "compiler", "mlir", "onnx", "jax", "tensorflow")
    # FIXME: shared build fails with linker errors
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    @property
    def _llvm_version(self):
        # The library is very tightly coupled to the LLVM version.
        if Version(self.version) < "1.7.0":
            return "[~19.1]"
        return "[~20.1]"

    def requirements(self):
        self.requires(f"llvm-core/{self._llvm_version}", transitive_headers=True, transitive_libs=True)
        self.requires(f"mlir/{self._llvm_version}", transitive_headers=True, transitive_libs=True, options={"tools": can_run(self)})

    def validate(self):
        check_min_cppstd(self, 17)
        if self.settings.get_safe("compiler.cstd"):
            check_min_cstd(self, 11)

    def build_requirements(self):
        if not can_run(self):
            self.tool_requires("mlir/<host_version>", options={"tools": True})

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 17)", "")

    def generate(self):
        if can_run(self):
            venv = VirtualRunEnv(self)
            venv.generate(scope="build")

        tc = CMakeToolchain(self)
        tc.cache_variables["LLVM_ENABLE_LLD"] = self.settings.compiler in ["clang", "apple-clang"]
        tc.cache_variables["STABLEHLO_ENABLE_BINDINGS_PYTHON"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("llvm-core::LLVMFileCheck", "cmake_target_name", "FileCheck")
        deps.generate()

    def build(self):
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

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        self._write_build_info(self._package_build_info_file)

        # The CMake project does not install anything besides the library files.
        # Copy the missing artifacts based on the Bazel project.

        # Header files
        copy(self, "*.h", os.path.join(self.source_folder, "stablehlo"), os.path.join(self.package_folder, "include", "stablehlo"))
        copy(self, "*.h.inc", os.path.join(self.build_folder, "stablehlo"), os.path.join(self.package_folder, "include", "stablehlo"))

        # TableGen (.td) files
        copy(self, "*.td", os.path.join(self.source_folder, "stablehlo"), os.path.join(self.package_folder, "share", "td", "stablehlo"))

        # Tools
        copy(self, "*", os.path.join(self.build_folder, "bin"), os.path.join(self.package_folder, "bin"))

        # Python source files
        # TODO: enable if python bindings are enabled
        # copy(self, "*.py",
        #      os.path.join(self.source_folder, "stablehlo", "integrations", "python"),
        #      os.path.join(self.package_folder, "python", "stablehlo"))
        # copy(self, "_*_ops_gen.py",
        #      os.path.join(self.build_folder, "stablehlo"),
        #      os.path.join(self.package_folder, "python", "stablehlo"))

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

        found_libs = set(collect_libs(self))
        component_libs = set(sum((c.libs for _, c in self.cpp_info.components.items()), []))
        if component_libs - found_libs:
            self.output.warning(f"Some component libraries were not found in lib/: {component_libs - found_libs}")
        if found_libs - component_libs:
            self.output.warning(f"Some libraries were not declared as components: {found_libs - component_libs}")


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
    label_replacements = {"FileCheck": "LLVMFileCheck"}
    components = {}
    for component, deps in parse_dotfile(dotfile, label_replacements).items():
        if component.startswith("LLVM") or component.startswith("MLIR") or "::" in component or component in known_system_libs:
            continue
        requires = []
        system_libs = []
        for dep in deps:
            if dep.startswith("LLVM"):
                dep = f"llvm-core::{dep}"
            if dep.startswith("MLIR"):
                dep = f"mlir::{dep}"
            if dep in known_system_libs:
                system_libs.append(dep)
            else:
                requires.append(dep)
        components[component] = {
            "requires": requires,
            "system_libs": system_libs,
        }
    return components
