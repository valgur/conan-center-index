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


class SimpleWebSocketServerConan(ConanFile):
    name = "simple-websocket-server"
    homepage = "https://gitlab.com/eidheim/Simple-WebSocket-Server"
    description = "A very simple, fast, multithreaded, platform independent WebSocket (WS) and WebSocket Secure (WSS) server and client library."
    topics = ("websocket", "socket", "server", "client", "header-only")
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "compiler", "arch", "build_type"
    no_copy_source = True
    license = "MIT"
    options = {
        "use_asio_standalone": [True, False],
    }
    default_options = {
        "use_asio_standalone": True,
    }

    def requirements(self):
        self.requires("openssl/1.1.1q")
        # only version 2.0.2 upwards is able to build against asio 1.18.0 or higher
        if Version(self.version) <= "2.0.1":
            if self.options.use_asio_standalone:
                self.requires("asio/1.16.1")
            else:
                self.requires("boost/1.73.0")
        else:
            if self.options.use_asio_standalone:
                self.requires("asio/1.23.0")
            else:
                self.requires("boost/1.79.0")

    def configure(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, "11")

    def build(self):
        if (
            Version(self.version) <= "2.0.1"
            and "asio" in self.deps_cpp_info.deps
            and Version(self.deps_cpp_info["asio"].version) >= "1.18.0"
        ):
            raise ConanInvalidConfiguration("simple-websocket-server versions <=2.0.1 require asio < 1.18.0")
        elif (
            Version(self.version) <= "2.0.1"
            and "boost" in self.deps_cpp_info.deps
            and Version(self.deps_cpp_info["boost"].version) >= "1.74.0"
        ):
            raise ConanInvalidConfiguration("simple-websocket-server versions <=2.0.1 require boost < 1.74.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "Simple-WebSocket-Server-v" + self.version
        os.rename(extracted_dir, self.source_folder)

    def package(self):
        copy(self, pattern="LICENSE", dst="licenses", src=self.source_folder)
        copy(
            self,
            pattern="*.hpp",
            dst=os.path.join("include", "simple-websocket-server"),
            src=self.source_folder,
        )

    def package_info(self):
        if self.options.use_asio_standalone:
            self.cpp_info.defines.append("USE_STANDALONE_ASIO")

    def package_id(self):
        self.info.header_only()
