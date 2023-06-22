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
required_conan_version = ">=1.33.0"


class S2let(ConanFile):
    name = "s2let"
    license = "GPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/astro-informatics/s2let"
    description = "Fast wavelets on the sphere"
    settings = "os", "arch", "compiler", "build_type"
    topics = ("physics", "astrophysics", "radio interferometry")
    options = {
        "fPIC": [True, False],
        "with_cfitsio": [True, False],
    }
    default_options = {
        "fPIC": True,
        "with_cfitsio": False,
    }
    generators = "cmake", "cmake_find_package"
    exports_sources = ["CMakeLists.txt"]

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx

    def requirements(self):
        self.requires("astro-informatics-so3/1.3.4")
        if self.options.with_cfitsio:
            self.requires("cfitsio/3.490")

    def validate(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("S2LET requires C99 support for complex numbers.")

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder
        )

    @property
    def _cmake(self):
        if not hasattr(self, "_cmake_instance"):
            self._cmake_instance = CMake(self)
            self._cmake_instance.definitions["BUILD_TESTING"] = False
            self._cmake_instance.definitions["cfitsio"] = self.options.with_cfitsio
            self._cmake_instance.configure(build_folder=self._build_subfolder)
        return self._cmake_instance

    def build(self):
        self._cmake.build()

    def package(self):
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)
        self._cmake.install()

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "s2let"
        self.cpp_info.names["cmake_find_package_multi"] = "s2let"
        self.cpp_info.libs = ["s2let"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["m"]
