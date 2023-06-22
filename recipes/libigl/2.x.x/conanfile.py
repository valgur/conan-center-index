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


class LibiglConan(ConanFile):
    name = "libigl"
    description = "Simple C++ geometry processing library"
    topics = ("geometry", "matrices", "algorithms")
    url = "https://github.com/conan-io/conan-center-index"
    exports_sources = ["CMakeLists.txt", "patches/**"]
    homepage = "https://libigl.github.io/"
    license = "MPL-2.0"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "header_only": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "header_only": True,
        "fPIC": True,
    }
    generators = "cmake", "cmake_find_package"
    requires = "eigen/3.3.9"
    _cmake = None

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    @property
    def _minimum_cpp_standard(self):
        return 14

    @property
    def _minimum_compilers_version(self):
        return {
            "Visual Studio": "16",
            "gcc": "6",
            "clang": "3.4",
            "apple-clang": "5.1",
        }

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            tools.check_min_cppstd(self, self._minimum_cpp_standard)
        min_version = self._minimum_compilers_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warn(
                "{} recipe lacks information about the {} compiler support.".format(
                    self.name, self.settings.compiler
                )
            )
        else:
            if tools.Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    "{} requires C++{} support. The current compiler {} {} does not support it.".format(
                        self.name,
                        self._minimum_cpp_standard,
                        self.settings.compiler,
                        self.settings.compiler.version,
                    )
                )
        if (
            self.settings.compiler == "Visual Studio"
            and "MT" in self.settings.compiler.runtime
            and not self.options.header_only
        ):
            raise ConanInvalidConfiguration("Visual Studio build with MT runtime is not supported")
        if "arm" in self.settings.arch or "x86" is self.settings.arch:
            raise ConanInvalidConfiguration(
                "Not available for arm. Requested arch: {}".format(self.settings.arch)
            )

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.header_only:
            del self.options.fPIC

    def _patch_sources(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder
        )

    def generate(self):
        if not self._cmake:
            self._cmake = CMake(self, parallel=False)
            tc.variables["LIBIGL_EXPORT_TARGETS"] = True
            tc.variables["LIBIGL_USE_STATIC_LIBRARY"] = not self.options.header_only

            # All these dependencies are needed to build the examples or the tests
            tc.variables["LIBIGL_BUILD_TUTORIALS"] = "OFF"
            tc.variables["LIBIGL_BUILD_TESTS"] = "OFF"
            tc.variables["LIBIGL_BUILD_PYTHON"] = "OFF"

            tc.variables["LIBIGL_WITH_CGAL"] = False
            tc.variables["LIBIGL_WITH_COMISO"] = False
            tc.variables["LIBIGL_WITH_CORK"] = False
            tc.variables["LIBIGL_WITH_EMBREE"] = False
            tc.variables["LIBIGL_WITH_MATLAB"] = False
            tc.variables["LIBIGL_WITH_MOSEK"] = False
            tc.variables["LIBIGL_WITH_OPENGL"] = False
            tc.variables["LIBIGL_WITH_OPENGL_GLFW"] = False
            tc.variables["LIBIGL_WITH_OPENGL_GLFW_IMGUI"] = False
            tc.variables["LIBIGL_WITH_PNG"] = False
            tc.variables["LIBIGL_WITH_TETGEN"] = False
            tc.variables["LIBIGL_WITH_TRIANGLE"] = False
            tc.variables["LIBIGL_WITH_XML"] = False
            tc.variables["LIBIGL_WITH_PYTHON"] = "OFF"
            tc.variables["LIBIGL_WITH_PREDICATES"] = False
        return self._cmake

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        self.copy("LICENSE.GPL", dst="licenses", src=self._source_subfolder)
        self.copy("LICENSE.MPL2", dst="licenses", src=self._source_subfolder)

        tools.rmdir(os.path.join(self.package_folder, "share"))
        if not self.options.header_only:
            tools.remove_files_by_mask(self.package_folder, "*.c")
            tools.remove_files_by_mask(self.package_folder, "*.cpp")

    def package_id(self):
        if self.options.header_only:
            self.info.header_only()

    def package_info(self):
        self.cpp_info.filenames["cmake_find_package"] = "libigl"
        self.cpp_info.filenames["cmake_find_package_multi"] = "libigl"
        self.cpp_info.names["cmake_find_package"] = "igl"
        self.cpp_info.names["cmake_find_package_multi"] = "igl"

        self.cpp_info.components["igl_common"].names["cmake_find_package"] = "common"
        self.cpp_info.components["igl_common"].names["cmake_find_package_multi"] = "common"
        self.cpp_info.components["igl_common"].libs = []
        self.cpp_info.components["igl_common"].requires = ["eigen::eigen"]
        if self.settings.os == "Linux":
            self.cpp_info.components["igl_common"].system_libs = ["pthread"]

        self.cpp_info.components["igl_core"].names["cmake_find_package"] = "core"
        self.cpp_info.components["igl_core"].names["cmake_find_package_multi"] = "core"
        self.cpp_info.components["igl_core"].requires = ["igl_common"]
        if not self.options.header_only:
            self.cpp_info.components["igl_core"].libs = ["igl"]
            self.cpp_info.components["igl_core"].defines.append("IGL_STATIC_LIBRARY")
