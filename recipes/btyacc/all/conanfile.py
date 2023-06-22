# TODO: verify the Conan v2 migration

import functools
import os
import textwrap

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

required_conan_version = ">=1.43.0"


class BtyaccConan(ConanFile):
    name = "btyacc"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ChrisDodd/btyacc"
    description = "Backtracking yacc"
    topics = ("yacc", "parser")
    license = "Unlicense"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }
    generators = "cmake"
    exports_sources = "CMakeLists.txt"
    no_copy_source = True

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        root = self._source_subfolder
        get_args = self.conan_data["sources"][self.version]
        tools.get(**get_args, destination=root, strip_root=True)

    @functools.lru_cache(1)
    def generate(self):
        cmake = CMake(self)
        cmake.configure()
        return cmake

    def build(self):
        self._configure_cmake().build()

    @property
    def _variables(self):
        return os.path.join("bin", "conan-official-btyacc-variables.cmake")

    def package(self):
        self.copy("README", "licenses", self._source_subfolder)
        self.copy("README.BYACC", "licenses", self._source_subfolder)
        self._configure_cmake().install()
        tools.rmdir(os.path.join(self.package_folder, "share"))
        variables = os.path.join(self.package_folder, self._variables)
        content = textwrap.dedent(
            """\
            set(BTYACC_EXECUTABLE "${CMAKE_CURRENT_LIST_DIR}/btyacc")
            if(NOT EXISTS "${BTYACC_EXECUTABLE}")
              set(BTYACC_EXECUTABLE "${BTYACC_EXECUTABLE}.exe")
            endif()
        """
        )
        tools.save(variables, content)

    def package_info(self):
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bindir}")
        self.env_info.PATH.append(bindir)
        self.cpp_info.build_modules["cmake"] = [self._variables]
        self.cpp_info.build_modules["cmake_find_package"] = [self._variables]
        self.cpp_info.build_modules["cmake_find_package_multi"] = [self._variables]
        self.cpp_info.builddirs = ["bin"]
