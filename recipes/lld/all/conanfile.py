import json
import os
import re
import textwrap
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import check_min_cppstd, can_run
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class LLDConan(ConanFile):
    name = "lld"
    description = "LLD - The LLVM Linker"
    license = "Apache-2.0 WITH LLVM-exception"
    topics = ("llvm", "linker")
    homepage = "https://lld.llvm.org/"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    no_copy_source = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"llvm-core/{self.version}", transitive_headers=True, transitive_libs=True)
        self.requires("zlib-ng/[^2.0]")
        self.requires("zstd/[~1.5]")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20 <5]")
        # llvm-tblgen
        if not can_run(self):
            self.tool_requires("llvm-core/<host_version>")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        sources = self.conan_data["sources"][self.version]
        get(self, **sources["lld"], destination="lld", strip_root=True)
        get(self, **sources["cmake"], destination="cmake", strip_root=True)
        get(self, **sources["libunwind"], destination="libunwind", strip_root=True)
        # Add missing project() command
        replace_in_file(self, "lld/CMakeLists.txt",
                        'set(LLVM_SUBPROJECT_TITLE "LLD")',
                        'set(LLVM_SUBPROJECT_TITLE "LLD")\n'
                        "project(LLD CXX)")

    def generate(self):
        if can_run(self):
            # for llvm-tblgen
            VirtualRunEnv(self).generate(scope="build")

        tc = CMakeToolchain(self)
        tc.cache_variables["LLVM_INCLUDE_TESTS"] = False
        tc.cache_variables["LLVM_MAIN_SRC_DIR"] = os.path.join(self.source_folder, "lld").replace("\\", "/")
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    @property
    def _source_path(self):
        return Path(self.source_folder) / "lld"

    @property
    def _graphviz_file(self):
        return Path(self.build_folder) / "lld.dot"

    def _validate_components(self, components):
        for component, info in components.items():
            if not component.lower().startswith("lld"):
                raise ConanException(f"Unexpected component: {component}")
            for req in info["requires"]:
                if not req.lower().startswith("lld"):
                    dep = req.split("::", 1)[0]
                    if dep not in self.dependencies.direct_host:
                        raise ConanException(f"Unexpected dependency for {component}: {req}")

    @cached_property
    def _lld_build_info(self):
        return {
            "components": components_from_dotfile(self._graphviz_file.read_text()),
        }

    def _write_build_info(self, path):
        Path(path).write_text(json.dumps(self._lld_build_info, indent=2))

    def _read_build_info(self) -> dict:
        return json.loads(self._build_info_file.read_text())

    def build(self):
        cmake = CMake(self)
        graphviz_args = [f"--graphviz={self._graphviz_file}"]

        # components not exported or not of interest
        exclude_patterns = [
            "CONAN_LIB*",
            "llvm-core*",
            # The *-resource-headers targets are not exported by the official LLDConfig.cmake.
            ".+-resource-headers",
        ]
        save(self, Path(self.build_folder) / "CMakeGraphVizOptions.cmake", textwrap.dedent(f"""
            set(GRAPHVIZ_EXECUTABLES OFF)
            set(GRAPHVIZ_MODULE_LIBS OFF)
            set(GRAPHVIZ_OBJECT_LIBS OFF)
            set(GRAPHVIZ_IGNORE_TARGETS "{';'.join(exclude_patterns)}")
        """))
        cmake.configure(build_script_folder="lld", cli_args=graphviz_args)
        self._write_build_info(self._build_info_file.name)
        self._validate_components(self._lld_build_info["components"])
        cmake.build()

    @property
    def _package_path(self):
        return Path(self.package_folder)

    @property
    def _cmake_module_path(self):
        return Path("lib") / "cmake" / "lld"

    @property
    def _build_info_file(self):
        return self._package_path / self._cmake_module_path / "conan_lld_build_info.json"

    def package(self):
        copy(self, "LICENSE.TXT", self._source_path, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        # Back up original cmake files for debugging purposes
        package_folder = Path(self.package_folder)
        cmake_dir = package_folder / self._cmake_module_path
        copy(self, "*", cmake_dir, os.path.join(self.package_folder, "share", "conan", self.name, "cmake_original"))

        self._write_build_info(self._build_info_file)

        package_folder = Path(self.package_folder)
        cmake_folder = package_folder / self._cmake_module_path
        rm(self, "LLDConfigVersion.cmake", cmake_folder)
        rm(self, "LLDTargets*", cmake_folder)
        rename(self, cmake_folder / "LLDConfig.cmake", cmake_folder / "LLDConfigVars.cmake")
        replace_in_file(self, cmake_folder / "LLDConfigVars.cmake",
                        'include("${LLD_CMAKE_DIR}/LLDTargets.cmake")',
                        '# include("${LLD_CMAKE_DIR}/LLDTargets.cmake")')

        self._write_export_executables_cmake(cmake_dir / "conan_add_executable_targets.cmake")

        rmdir(self, package_folder / "share" / "man")

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

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "LLD")

        build_info = self._read_build_info()
        components = build_info["components"]
        for name, data in components.items():
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", name)
            component.libs = [name]
            component.requires = data["requires"]
            component.system_libs = data["system_libs"]
            if not self.dependencies["llvm-core"].options.rtti:
                component.cxxflags.append("/GR-" if is_msvc(self) else "-fno-rtti")

        found_libs = set(collect_libs(self))
        component_libs = set(sum((c.libs for _, c in self.cpp_info.components.items()), []))
        if component_libs - found_libs:
            self.output.warning(f"Some component libraries were not found in lib/: {component_libs - found_libs}")
        if found_libs - component_libs:
            self.output.warning(f"Some libraries were not declared as components: {found_libs - component_libs}")

        self.cpp_info.builddirs.append(self._cmake_module_path)
        self.cpp_info.set_property("cmake_build_modules", [
            self._cmake_module_path / "LLDConfigVars.cmake",
            self._cmake_module_path / "conan_add_executable_targets.cmake",
        ])


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
    known_system_libs = {
        "dl",
    }
    label_replacements = {
        "ZLIB::ZLIB": "zlib-ng::zlib-ng",
        "zstd::libzstd_shared": "zstd::zstd",
        "zstd::libzstd_static": "zstd::zstd",
    }
    components = {}
    for component, deps in parse_dotfile(dotfile, label_replacements).items():
        if not component.lower().startswith("lld"):
            continue
        requires = []
        system_libs = []
        for dep in deps:
            if dep.startswith("LLVM"):
                dep = f"llvm-core::{dep}"
            if dep in known_system_libs:
                system_libs.append(dep)
            else:
                requires.append(dep)
        components[component] = {
            "requires": requires,
            "system_libs": system_libs,
        }
    return components
