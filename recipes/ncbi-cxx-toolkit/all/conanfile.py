import os
import re
import textwrap
from functools import cached_property
from pathlib import Path

import yaml
from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeDeps, CMakeToolchain, CMake, cmake_layout
from conan.tools.files import get, copy, rmdir
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NcbiCxxToolkit(ConanFile):
    name = "ncbi-cxx-toolkit"
    description = "NCBI C++ Toolkit -- a cross-platform application framework and a collection of libraries for working with biological data."
    license = "CC0-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://ncbi.github.io/cxx-toolkit"
    topics = ("ncbi", "biotechnology", "bioinformatics", "genbank", "gene",
              "genome", "genetic", "sequence", "alignment", "blast",
              "biological", "toolkit")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_targets": ["ANY"],
        "with_components": ["ANY"],
        "without_req": ["ANY"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_targets": "",
        "with_components": "",
        "without_req": "",
    }
    no_copy_source = True
    implements = ["auto_shared_fpic"]

    @property
    def _dependencies_filename(self):
        v = Version(self.version)
        return f"dependencies-{v.major}.{v.minor}.yml"

    @property
    def _requirements_filename(self):
        v = Version(self.version)
        return f"requirements-{v.major}.{v.minor}.yml"

    @cached_property
    def _tk_dependencies(self):
        dependencies_filepath = Path(self.recipe_folder, "dependencies", self._dependencies_filename)
        return yaml.safe_load(dependencies_filepath.read_text(encoding="utf-8"))

    @cached_property
    def _tk_requirements(self):
        requirements_filepath = Path(self.recipe_folder, "dependencies", self._requirements_filename)
        return yaml.safe_load(requirements_filepath.read_text(encoding="utf-8"))

    def _parse_option(self, data):
        items = str(data).replace(",", ";").replace(" ", ";").split(";")
        return set(filter(None, items))

    @cached_property
    def _targets(self):
        return sorted(self._parse_option(self.options.with_targets))

    @cached_property
    def _disabled_req(self):
        return sorted(self._parse_option(self.options.without_req))

    def _collect_dependencies(self, components):
        visited = set()
        queue = list(components)
        while queue:
            component = queue.pop()
            if component not in visited:
                visited.add(component)
                for dependency in self._tk_dependencies["dependencies"].get(component, []):
                    if dependency not in visited:
                        queue.append(dependency)
        return visited

    @cached_property
    def _components(self):
        components = self._parse_option(self.options.with_components)
        for t in self._targets:
            pattern = re.compile(t)
            for libraries in self._tk_dependencies["libraries"].values():
                components.update(lib for lib in libraries if pattern.match(lib))
        if not components:
            components = self._tk_dependencies["components"]
        return sorted(self._collect_dependencies(components))

    @cached_property
    def _component_targets(self):
        cts = set(self._targets)
        for component in self._components:
            cts.update(self._tk_dependencies["libraries"][component])
        return sorted(cts)

    @cached_property
    def _requirements(self):
        requirements = set()
        for target in self._component_targets:
            requirements.update(self._tk_dependencies["requirements"].get(target, []))
        return sorted(requirements)

    def _translate_req(self, key):
        if "Boost" in key:
            key = "Boost"
        if key in self._disabled_req:
            return []
        if key == "BerkeleyDB":
            return []
        if self.settings.os in self._tk_requirements["disabled"].get(key, []):
            return []
        return self._tk_requirements["requirements"].get(key, [])

    def export(self):
        copy(self, self._dependencies_filename,
            os.path.join(self.recipe_folder, "dependencies"),
            os.path.join(self.export_folder, "dependencies"))
        copy(self, self._requirements_filename,
            os.path.join(self.recipe_folder, "dependencies"),
            os.path.join(self.export_folder, "dependencies"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.output.info("Enabled components:")
        for component in self._components:
            self.output.info(f"- {component}")
        self.output.info("Dependencies:")
        for req in self._requirements:
            for pkg in self._translate_req(req):
                self.output.info(f"- {pkg}")
                self.requires(pkg)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        if "GRPC" in self._requirements:
            self.tool_requires("grpc/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, os.path.join(self.source_folder, "src", "build-system", "cmake", "unused"))
        rmdir(self, os.path.join(self.source_folder, "src", "build-system", "cmake", "modules"))
        Path(self.source_folder, "CMakeLists.txt").write_text(textwrap.dedent("""\
            cmake_minimum_required(VERSION 3.15)
            project(ncbi-cpp)
            include(src/build-system/cmake/CMake.NCBItoolkit.cmake)
            add_subdirectory(src)
        """))

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["NCBI_PTBCFG_PACKAGING"] = True
        tc.variables["NCBI_PTBCFG_ALLOW_COMPOSITE"] = self.options.shared
        tc.variables["NCBI_PTBCFG_PROJECT_LIST"] = "-app/netcache"
        tc.variables["NCBI_PTBCFG_PROJECT_COMPONENTTARGETS"] = ";".join(self._component_targets)
        tc.variables["NCBI_PTBCFG_PROJECT_TAGS"] = "-demo;-sample"
        tc.variables["NCBI_PTBCFG_PROJECT_COMPONENTS"] = ";".join(f"-{r}" for r in self._disabled_req)
        if is_msvc(self):
            tc.variables["NCBI_PTBCFG_CONFIGURATION_TYPES"] = self.settings.build_type
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    @property
    def _module_file_rel_path(self):
        return os.path.join("res", "build-system", "cmake", "CMake.NCBIpkg.conan.cmake")

    def package_info(self):
        impfile = Path(self.package_folder, "res", "ncbi-cpp-toolkit.imports")
        all_exports = set(impfile.read_text(encoding="utf-8").split())
        self.output.info("Exported components:")
        for component in self._components:
            c_libs = []
            c_reqs = []
            n_reqs = set()
            libraries = self._tk_dependencies["libraries"][component]
            for lib in libraries:
                if lib in all_exports:
                    c_libs.append(lib)
                n_reqs.update(self._tk_dependencies["requirements"].get(lib, []))
            c_reqs.extend(self._tk_dependencies["dependencies"][component])
            for req in sorted(n_reqs):
                for pkg in self._translate_req(req):
                    pkg = pkg.split("/", 1)[0]
                    ref = f"{pkg}::{pkg}"
                    c_reqs.append(ref)
            self.output.info(f"{component}:")
            self.output.info(f"- libs: {c_libs}")
            self.output.info(f"- requires: {c_reqs}")
            self.cpp_info.components[component].libs = c_libs
            self.cpp_info.components[component].requires = c_reqs

        if self.settings.os == "Windows":
            self.cpp_info.components["core"].defines.append("_UNICODE")
            self.cpp_info.components["core"].defines.append("_CRT_SECURE_NO_WARNINGS=1")
        else:
            self.cpp_info.components["core"].defines.append("_MT")
            self.cpp_info.components["core"].defines.append("_REENTRANT")
            self.cpp_info.components["core"].defines.append("_THREAD_SAFE")
            self.cpp_info.components["core"].defines.append("_FILE_OFFSET_BITS=64")
        if self.options.shared:
            self.cpp_info.components["core"].defines.append("NCBI_DLL_BUILD")
        if self.settings.build_type == "Debug":
            self.cpp_info.components["core"].defines.append("_DEBUG")

        if self.settings.os == "Windows":
            self.cpp_info.components["core"].system_libs = ["ws2_32", "dbghelp"]
        elif self.settings.os == "Linux":
            self.cpp_info.components["core"].system_libs = ["dl", "rt", "m", "pthread", "resolv"]
        elif self.settings.os == "Macos":
            self.cpp_info.components["core"].frameworks = ["ApplicationServices"]

        self.cpp_info.components["core"].builddirs.append("res")
        self.cpp_info.set_property("cmake_build_modules", [self._module_file_rel_path])
