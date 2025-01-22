import os
import textwrap

from conan import ConanFile
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import get, copy, save, rmdir

required_conan_version = ">=1.53.0"


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
        "apps": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("fmt/10.2.1")
        self.requires("mbits-utfconv/1.0.3")
        self.requires("mbits-diags/0.9.6")
        self.requires("mbits-mstch/1.0.4")
        self.requires("mbits-args/0.12.3")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

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
        copy(
            self,
            pattern="LICENSE",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, self._cmake_install_base_path))


        # Provide relocatable mbits::lngs target and Mbitslngs_LNGS_EXECUTABLE cache variable
        # TODO: some of the following logic might be disabled when conan will
        #       allow to create executable imported targets in package_info()
        module_folder_depth = len(os.path.normpath(self._cmake_install_base_path).split(os.path.sep))
        lngs_rel_path = "{}bin/{}".format("".join(["../"] * module_folder_depth), "lngs")
        save(self, os.path.join(self.package_folder, self._cmake_targets_module_file),
             textwrap.dedent(
                    f"""\
                if(NOT TARGET mbits::lngs)
                    if(CMAKE_CROSSCOMPILING)
                        find_program(LNGS_PROGRAM lngs PATHS ENV PATH NO_DEFAULT_PATH)
                    endif()
                    if(NOT LNGS_PROGRAM)
                        set(LNGS_PROGRAM "${{CMAKE_CURRENT_LIST_DIR}}/{lngs_rel_path}")
                    endif()
                    get_filename_component(LNGS_PROGRAM "${{LNGS_PROGRAM}}" ABSOLUTE)
                    set(Mbitslngs_LNGS_EXECUTABLE ${{LNGS_PROGRAM}} CACHE FILEPATH "The lngs tool")
                    add_executable(mbits::lngs IMPORTED)
                    set_property(TARGET mbits::lngs PROPERTY IMPORTED_LOCATION ${{Mbitslngs_LNGS_EXECUTABLE}})
                endif()
            """)
        )

    def package_info(self):
        self.cpp_info.builddirs = [self._cmake_install_base_path ]
        self.cpp_info.set_property("cmake_build_modules", [self._cmake_targets_module_file])
        self.cpp_info.set_property("cmake_file_name", "mbits-lngs")

        comp = self.cpp_info.components["liblngs"]
        comp.set_property("cmake_target_name", "mbits::liblngs")
        comp.libs = ["lngs"]
