from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, get, rmdir, export_conandata_patches
import os

required_conan_version = ">=1.53.0"


class Atomic_opsConan(ConanFile):
    name = "libatomic_ops"
    description = "The atomic_ops project (Atomic memory update operations portable implementation)"
    license = "GPL-2.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ivmai/libatomic_ops"
    topics = ("fmt", "format", "iostream", "printf")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "assertions": [True, False],
        "atomic_intrinsics": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "assertions": False,
        "atomic_intrinsics": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        for option, _ in self._cmake_options_defaults:
            tc.variables["enable_{}".format(option)] = self.options.get_safe(option)
        tc.variables["install_headers"] = True
        tc.variables["build_tests"] = False
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Atomic_ops")
        self.cpp_info.set_property(
            "cmake_target_name", "Atomic_ops::atomic_ops_gpl"
        )  # workaround to not define an unofficial target

        # TODO: Remove on Conan 2.0
        self.cpp_info.names["cmake_find_package"] = "Atomic_ops"
        self.cpp_info.names["cmake_find_package_multi"] = "Atomic_ops"

        self.cpp_info.components["atomic_ops"].set_property("cmake_target_name", "Atomic_ops::atomic_ops")
        self.cpp_info.components["atomic_ops"].set_property("pkg_config_name", "atomic_ops")
        self.cpp_info.components["atomic_ops"].libs = ["atomic_ops"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["atomic_ops"].system_libs = ["pthread"]

        self.cpp_info.components["atomic_ops_gpl"].set_property(
            "cmake_target_name", "Atomic_ops::atomic_ops_gpl"
        )
        self.cpp_info.components["atomic_ops_gpl"].libs = ["atomic_ops_gpl"]
        self.cpp_info.components["atomic_ops_gpl"].requires = ["atomic_ops"]
