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

required_conan_version = ">=1.33.0"


class LibProtobufMutatorConan(ConanFile):
    name = "libprotobuf-mutator"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/libprotobuf-mutator"
    description = "A library to randomly mutate protobuffers."
    topics = ("test", "fuzzing", "protobuf")
    settings = "os", "compiler", "build_type", "arch"

    def requirements(self):
        self.requires("protobuf/3.17.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def validate(self):
        if self.settings.compiler != "clang":
            raise ConanInvalidConfiguration("Only clang allowed")
        if self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("Requires either compiler.libcxx=libstdc++11")
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)

    def _patch_sources(self):
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            """include_directories(${PROTOBUF_INCLUDE_DIRS})""",
            """include_directories(${protobuf_INCLUDE_DIRS})""",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            """set(CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake/external)""",
            """# (disabled by conan) set(CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake/external)""",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            """add_subdirectory(examples EXCLUDE_FROM_ALL)""",
            """# (disabled by conan) add_subdirectory(examples EXCLUDE_FROM_ALL)""",
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LIB_PROTO_MUTATOR_TESTING"] = "OFF"
        tc.variables["LIB_PROTO_MUTATOR_DOWNLOAD_PROTOBUF"] = "OFF"
        tc.variables["LIB_PROTO_MUTATOR_WITH_ASAN"] = "OFF"
        tc.variables["LIB_PROTO_MUTATOR_FUZZER_LIBRARIES"] = ""
        # todo: check option(LIB_PROTO_MUTATOR_MSVC_STATIC_RUNTIME "Link static runtime libraries" ON)
        if is_msvc(self):
            # Should be added because of
            # https://docs.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-initonceexecuteonce
            tc.preprocessor_definitions["_WIN32_WINNT"] = "0x0600"
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "OFF"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "libprotobuf-mutator"
        self.cpp_info.names["cmake_find_package_multi"] = "libprotobuf-mutator"

        self.cpp_info.libs = ["protobuf-mutator-libfuzzer", "protobuf-mutator"]
        self.cpp_info.includedirs.append(os.path.join("include", "libprotobuf-mutator"))
