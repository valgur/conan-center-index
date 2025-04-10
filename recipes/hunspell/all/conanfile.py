import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class HunspellConan(ConanFile):
    name = "hunspell"
    description = "Hunspell is a free spell checker and morphological analyzer library"
    license = "LGPL-2.1-or-later OR GPL-2.0-or-later OR MPL-1.1"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://hunspell.github.io/"
    topics = ("spell", "spell-check")

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
    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)
        # TODO: Remove once PR is merged: https://github.com/hunspell/hunspell/pull/704/
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # NOTE: The source contains a pre-configured hunvisapi.h and it would
        #       prevent no_copy_source and building without patches.
        h = os.path.join(self.source_folder, "src", "hunspell", "hunvisapi.h")
        os.remove(h)

    def validate(self):
        check_min_cppstd(self, 11)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CONAN_hunspell_VERSION"] = self.version
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "COPYING*",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"),
             keep_path=False)
        copy(self, "license.hunspell",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"),
             keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["hunspell"]
        if not self.options.shared:
            self.cpp_info.defines = ["HUNSPELL_STATIC"]
