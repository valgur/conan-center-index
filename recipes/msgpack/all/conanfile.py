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
import os


class MsgpackConan(ConanFile):
    name = "msgpack"
    description = "The official C++ library for MessagePack"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/msgpack/msgpack-c"
    topics = ("message-pack", "serialization")
    license = "BSL-1.0"
    exports_sources = "CMakeLists.txt"
    generators = "cmake"
    settings = "os", "arch", "build_type", "compiler"
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
        "c_api": [True, False],
        "cpp_api": [True, False],
        "with_boost": [True, False],
        "header_only": [True, False],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
        "c_api": True,
        "cpp_api": True,
        "with_boost": False,
        "header_only": False,
    }
    deprecated = "msgpack-c or msgpack-cxx"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        # Deprecate header_only option
        if self.options.header_only:
            self.options.c_api = False
            self.options.cpp_api = True
            self.output.warn("header_only option is deprecated, prefer c_api=False and cpp_api=True")
        del self.options.header_only

        if not self.options.c_api and not self.options.cpp_api:
            raise ConanInvalidConfiguration("You must enable at least c_api or cpp_api.")
        if self.options.c_api:
            if self.options.shared:
                del self.options.fPIC
            del self.settings.compiler.libcxx
            del self.settings.compiler.cppstd
        else:
            del self.options.shared
            del self.options.fPIC
        if not self.options.cpp_api:
            del self.options.with_boost
        if self.options.get_safe("with_boost"):
            self.options["boost"].header_only = False
            self.options["boost"].without_chrono = False
            self.options["boost"].without_context = False
            self.options["boost"].without_system = False
            self.options["boost"].without_timer = False

    def requirements(self):
        if self.options.get_safe("with_boost"):
            self.requires("boost/1.74.0")

    def package_id(self):
        del self.info.options.with_boost
        if not self.options.c_api:
            self.info.header_only()

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = "msgpack-c-cpp-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["MSGPACK_ENABLE_SHARED"] = self.options.shared
        tc.variables["MSGPACK_ENABLE_STATIC"] = not self.options.shared
        tc.variables["MSGPACK_ENABLE_CXX"] = self.options.cpp_api
        tc.variables["MSGPACK_BOOST"] = self.options.get_safe("with_boost", False)
        tc.variables["MSGPACK_32BIT"] = self.settings.arch == "x86"
        tc.variables["MSGPACK_BUILD_EXAMPLES"] = False
        tc.variables["MSGPACK_BUILD_TESTS"] = False
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def build(self):
        if self.options.get_safe("with_boost") and (
            self.options["boost"].header_only
            or self.options["boost"].without_chrono
            or self.options["boost"].without_context
            or self.options["boost"].without_system
            or self.options["boost"].without_timer
        ):
            raise ConanInvalidConfiguration(
                "msgpack with boost requires the following boost components: chrono, context, system and timer."
            )
        if self.options.c_api:
            cmake = self._configure_cmake()
            cmake.build()

    def package(self):
        self.copy("LICENSE_1_0.txt", dst="licenses", src=self._source_subfolder)
        if self.options.c_api:
            cmake = self._configure_cmake()
            cmake.install()
            tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
            tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        else:
            self.copy("*.h", dst="include", src=os.path.join(self._source_subfolder, "include"))
            self.copy("*.hpp", dst="include", src=os.path.join(self._source_subfolder, "include"))

    def package_info(self):
        # TODO: CMake imported targets shouldn't be namespaced (waiting implementation of https://github.com/conan-io/conan/issues/7615)
        if self.options.c_api:
            self.cpp_info.components["msgpackc"].names["cmake_find_package"] = "msgpackc"
            self.cpp_info.components["msgpackc"].names["cmake_find_package_multi"] = "msgpackc"
            self.cpp_info.components["msgpackc"].libs = tools.collect_libs(self)
        if self.options.cpp_api:
            self.cpp_info.components["msgpackc-cxx"].names["cmake_find_package"] = "msgpackc-cxx"
            self.cpp_info.components["msgpackc-cxx"].names["cmake_find_package_multi"] = "msgpackc-cxx"
            if self.options.with_boost:
                self.cpp_info.components["msgpackc-cxx"].defines = ["MSGPACK_USE_BOOST"]
                self.cpp_info.components["msgpackc-cxx"].requires = ["boost::boost"]
