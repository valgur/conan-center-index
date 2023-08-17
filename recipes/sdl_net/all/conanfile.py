from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
from conan.tools.scm import Version
import os

required_conan_version = ">=1.53.0"


class SdlnetConan(ConanFile):
    name = "sdl_net"
    description = "A networking library for SDL"
    license = "Zlib"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.libsdl.org/projects/SDL_net"
    topics = ("sdl2", "sdl2_net", "sdl", "net", "networking")

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

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("sdl/2.26.5")

    def validate(self):
        if Version(self.version).major != Version(self.dependencies["sdl"].ref.version).major:
            raise ConanInvalidConfiguration(f"The major versions of {self.name} and sdl must be the same")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SDL_NET_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        copy(self, "COPYING.txt",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "SDL2_net")
        self.cpp_info.set_property("cmake_target_name", "SDL2_net::SDL2_net")
        self.cpp_info.set_property("pkg_config_name", "SDL2_net")
        self.cpp_info.libs = ["SDL2_net"]
        self.cpp_info.includedirs.append(os.path.join("include", "SDL2"))

        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["ws2_32", "iphlpapi"])

        # TODO: to remove in conan v2
        self.cpp_info.names["cmake_find_package"] = "SDL2_net"
        self.cpp_info.names["cmake_find_package_multi"] = "SDL2_net"
