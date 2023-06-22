# TODO: verify the Conan v2 migration

import os

from conan import ConanFile, conan_version
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.android import android_abi
from conan.tools.apple import (
    XCRun,
    fix_apple_shared_install_name,
    is_apple_os,
    to_apple_arch,
)
from conan.tools.build import (
    build_jobs,
    can_run,
    check_min_cppstd,
    cross_building,
    default_cppstd,
    stdcpp_library,
    valid_min_cppstd,
)
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
from conan.tools.env import (
    Environment,
    VirtualBuildEnv,
    VirtualRunEnv,
)
from conan.tools.files import (
    apply_conandata_patches,
    chdir,
    collect_libs,
    copy,
    download,
    export_conandata_patches,
    get,
    load,
    mkdir,
    patch,
    patches,
    rename,
    replace_in_file,
    rm,
    rmdir,
    save,
    symlinks,
    unzip,
)
from conan.tools.gnu import (
    Autotools,
    AutotoolsDeps,
    AutotoolsToolchain,
    PkgConfig,
    PkgConfigDeps,
)
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import (
    MSBuild,
    MSBuildDeps,
    MSBuildToolchain,
    NMakeDeps,
    NMakeToolchain,
    VCVars,
    check_min_vs,
    is_msvc,
    is_msvc_static_runtime,
    msvc_runtime_flag,
    unix_path,
    unix_path_package_info_legacy,
    vs_layout,
)
from conan.tools.microsoft.visual import vs_ide_version
from conan.tools.scm import Version
from conan.tools.system import package_manager
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
import os
import textwrap


class IgnitionCmakeConan(ConanFile):
    name = "ignition-cmake"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/gazebosim/gz-cmake"
    description = "A set of CMake modules that are used by the C++-based Ignition projects."
    topics = ("ignition", "robotics", "cmake")
    settings = "os", "compiler", "build_type", "arch"
    exports_sources = "CMakeLists.txt", "patches/**"

    @property
    def _module_file_rel_path(self):
        return os.path.join("lib", "cmake", f"conan-official-{self.name}-variables.cmake")

    def package_id(self):
        self.info.header_only()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_INSTALL_DATAROOTDIR"] = "lib"
        tc.variables["SKIP_component_name"] = False
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst="licenses", src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        version_major = Version(self.version).major
        cmake_config_files_dir = os.path.join(
            self.package_folder, "lib", "cmake", f"ignition-cmake{version_major}"
        )
        files = os.listdir(cmake_config_files_dir)

        # retain the special config file for utilities target provided by ignition-cmake
        # removing it from the list
        files.remove(f"ignition-cmake{version_major}-utilities-targets.cmake")

        # remove all other xxx.cmake files from the list
        for file in files:
            if file.endswith(".cmake"):
                os.remove(os.path.join(cmake_config_files_dir, file))

        # add version information for downstream dependencies consuming ign-cmake through cmake_find_package generators
        self._create_cmake_module_variables(
            os.path.join(self.package_folder, self._module_file_rel_path), Version(self.version)
        )

    @staticmethod
    def _create_cmake_module_variables(module_file, version):
        # the version info is needed by downstream ignition-dependencies
        content = textwrap.dedent(
            """\
            set(ignition-cmake{major}_VERSION_MAJOR {major})
            set(ignition-cmake{major}_VERSION_MINOR {minor})
            set(ignition-cmake{major}_VERSION_PATCH {patch})
            set(ignition-cmake{major}_VERSION_STRING "{major}.{minor}.{patch}")
        """.format(
                major=version.major, minor=version.minor, patch=version.patch
            )
        )
        save(self, module_file, content)

    def package_info(self):
        version_major = Version(self.version).major
        ign_cmake_component = f"ignition-cmake{version_major}"
        base_module_path = os.path.join(self.package_folder, "lib", "cmake", ign_cmake_component)
        ign_cmake_file = os.path.join(base_module_path, f"cmake{version_major}", "IgnCMake.cmake")
        utils_targets_file = os.path.join(base_module_path, f"{ign_cmake_component}-utilities-targets.cmake")

        self.cpp_info.names["cmake_find_package"] = ign_cmake_component
        self.cpp_info.names["cmake_find_package_multi"] = ign_cmake_component
        self.cpp_info.names["cmake_paths"] = ign_cmake_component

        self.cpp_info.components[ign_cmake_component].names["cmake_find_package"] = ign_cmake_component
        self.cpp_info.components[ign_cmake_component].names["cmake_find_package_multi"] = ign_cmake_component
        self.cpp_info.components[ign_cmake_component].names["cmake_paths"] = ign_cmake_component
        self.cpp_info.components[ign_cmake_component].builddirs.append(
            os.path.join(base_module_path, f"cmake{version_major}")
        )

        self.cpp_info.components[ign_cmake_component].build_modules["cmake_find_package"] = [
            self._module_file_rel_path,
            ign_cmake_file,
        ]
        self.cpp_info.components[ign_cmake_component].build_modules["cmake_find_package_multi"] = [
            self._module_file_rel_path,
            ign_cmake_file,
        ]
        self.cpp_info.components[ign_cmake_component].build_modules["cmake_paths"] = [
            self._module_file_rel_path,
            ign_cmake_file,
        ]

        self.cpp_info.components["utilities"].names["cmake_find_package"] = "utilities"
        self.cpp_info.components["utilities"].names["cmake_find_package_multi"] = "utilities"
        self.cpp_info.components["utilities"].names["cmake_paths"] = "utilities"
        self.cpp_info.components["utilities"].includedirs.append(f"include/ignition/cmake{version_major}")

        self.cpp_info.set_property("cmake_build_modules", [self._module_file_rel_path, ign_cmake_file])
        self.cpp_info.components["utilities"].build_modules["cmake_find_package"] = [
            self._module_file_rel_path,
            ign_cmake_file,
            utils_targets_file,
        ]
        self.cpp_info.components["utilities"].build_modules["cmake_find_package_multi"] = [
            self._module_file_rel_path,
            ign_cmake_file,
            utils_targets_file,
        ]
        self.cpp_info.components["utilities"].build_modules["cmake_paths"] = [
            self._module_file_rel_path,
            ign_cmake_file,
            utils_targets_file,
        ]
