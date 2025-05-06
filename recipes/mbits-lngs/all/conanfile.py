import os
import textwrap

from conan import ConanFile
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class MBitsLngsConan(ConanFile):
    name = "mbits-lngs"
    description = "Language strings support"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mbits-os/lngs"
    topics = ("gettext", "locale",)
    settings = "os", "arch", "compiler", "build_type"
    package_type = "static-library"
    options = {
        "fPIC": [True, False],
        "apps": [True, False],
    }
    default_options = {
        "fPIC": True,
        "apps": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("fmt/[>=8 <11]")
        self.requires("mbits-utfconv/[^1.0.3]")
        self.requires("mbits-diags/[^0.9.6]")
        self.requires("mbits-mstch/[^1.0.4]")
        self.requires("mbits-args/[^0.12.3]")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # CPack support is not needed by Conan and prepare_pack.cmake breaks when can_run() is False
        replace_in_file(self, "CMakeLists.txt", "include(prepare_pack)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LNGS_TESTING"] = False
        tc.variables["LNGS_LITE"] = False
        tc.variables["LNGS_LINKED_RESOURCES"] = True
        tc.variables["LNGS_NO_PKG_CONFIG"] = True
        tc.variables["LNGS_APP"] = self.options.apps
        if cross_building(self):
            tc.variables["LNGS_REBUILD_RESOURCES"] = False
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _cmake_install_base_path(self):
        return os.path.join("lib", "cmake")

    @property
    def _cmake_targets_module_file(self):
        return os.path.join(self._cmake_install_base_path, "mbits-lngs-targets.cmake")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, self._cmake_install_base_path))

        # Provide relocatable mbits::lngs target and Mbitslngs_LNGS_EXECUTABLE cache variable
        save(self, os.path.join(self.package_folder, self._cmake_targets_module_file),
            textwrap.dedent(f"""\
                if(NOT TARGET mbits::lngs)
                find_program(LNGS_PROGRAM lngs)
                get_filename_component(LNGS_PROGRAM "${{LNGS_PROGRAM}}" ABSOLUTE)
                set(Mbitslngs_LNGS_EXECUTABLE ${{LNGS_PROGRAM}} CACHE FILEPATH "The lngs tool")
                add_executable(mbits::lngs IMPORTED)
                set_property(TARGET mbits::lngs PROPERTY IMPORTED_LOCATION ${{Mbitslngs_LNGS_EXECUTABLE}})
                endif()
        """))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "mbits-lngs")
        self.cpp_info.set_property("cmake_target_name", "mbits::liblngs")
        self.cpp_info.libs = ["lngs"]
        self.cpp_info.builddirs = [self._cmake_install_base_path]
        self.cpp_info.set_property("cmake_build_modules", [self._cmake_targets_module_file])
