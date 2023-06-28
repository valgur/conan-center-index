# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class SimpleWebSocketServerConan(ConanFile):
    name = "simple-websocket-server"
    description = (
        "A very simple, fast, multithreaded, platform independent WebSocket (WS) "
        "and WebSocket Secure (WSS) server and client library."
    )
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.com/eidheim/Simple-WebSocket-Server"
    topics = ("websocket", "socket", "server", "client", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "use_asio_standalone": [True, False],
    }
    default_options = {
        "use_asio_standalone": True,
    }
    no_copy_source = True

    def configure(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, "11")

    def layout(self):
        basic_layout(self, src_folder="src")

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

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        if (
            Version(self.version) <= "2.0.1"
            and "asio" in self.dependencies
            and Version(self.dependencies["asio"].ref.version) >= "1.18.0"
        ):
            raise ConanInvalidConfiguration("simple-websocket-server versions <=2.0.1 require asio < 1.18.0")
        elif (
            Version(self.version) <= "2.0.1"
            and "boost" in self.dependencies
            and Version(self.dependencies["boost"].ref.version) >= "1.74.0"
        ):
            raise ConanInvalidConfiguration("simple-websocket-server versions <=2.0.1 require boost < 1.74.0")

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        copy(
            self,
            pattern="*.hpp",
            dst=os.path.join("include", "simple-websocket-server"),
            src=self.source_folder,
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if self.options.use_asio_standalone:
            self.cpp_info.defines.append("USE_STANDALONE_ASIO")
