import io
import os
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NanopbConan(ConanFile):
    name = "nanopb"
    description = ("Nanopb is a small code-size Protocol Buffers implementation in ansi C. "
                   "It is especially suitable for use in microcontrollers, but fits any memory restricted system.")
    license = "Zlib"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://jpa.kapsi.fi/nanopb/"
    topics = ("protocol-buffers", "protobuf", "microcontrollers")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @cached_property
    def _python_version(self):
        output = io.StringIO()
        self.run("python --version", stdout=output)
        return Version(output.getvalue().strip().split()[1])

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.cache_variables["nanopb_MSVC_STATIC_RUNTIME"] = is_msvc_static_runtime(self)
        tc.generate()

    @property
    def _site_packages_dir(self):
        v = self._python_version
        return os.path.join(self.package_folder, "lib", f"python{v.major}.{v.minor}", "site-packages")

    def build(self):
        cmake = CMake(self)
        cmake.configure(variables={"nanopb_PYTHON_INSTDIR_OVERRIDE": self._site_packages_dir})
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

        pkgs = " ".join([
            # protobuf v6 is too new for nanopb v0.4.9.1
            f"protobuf==5.*",
            "grpcio-tools",
        ])
        self.run(f'python -m pip install {pkgs} --target="{self._site_packages_dir}"')
        for path in Path(self._site_packages_dir).iterdir():
            if path.name.endswith(".dist-info"):
                rmdir(self, path)
        rm(self, "*.pyc", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nanopb")
        self.cpp_info.set_property("cmake_target_name", "nanopb::protobuf-nanopb")
        self.cpp_info.set_property("cmake_target_aliases", ["nanopb::protobuf-nanopb-static"])
        self.cpp_info.libs = ["protobuf-nanopb"]
        self.cpp_info.includedirs = [os.path.join("include", "nanopb")]

        site_packages_dir = str(next(Path(self.package_folder, "lib").glob("python*")).joinpath("site-packages"))
        self.buildenv_info.prepend_path("PYTHONPATH", site_packages_dir)
        self.runenv_info.prepend_path("PYTHONPATH",  site_packages_dir)
        self.cpp_info.bindirs.append(os.path.join(site_packages_dir, "bin"))
