import os
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import get, copy
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class StatusCodeConan(ConanFile):
    name = "status-code"
    description = "Proposed SG14 status_code for the C++ standard"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ned14/status-code"
    topics = ("header-only", "proposal", "status", "return code")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    @property
    def _compiler_required_version(self):
        return {
            # Their README says gcc 5, but in testing only >=7 worked
            "gcc": "7",
            "clang": "3.3",
            "Visual Studio": "14",
            "apple-clang": "5",
        }

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, "11")

        min_version = self._compiler_required_version.get(str(self.settings.compiler))
        if min_version:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    "This package requires c++11 support. The current compiler does not support it."
                )
        else:
            self.output.warning(
                "This recipe has no support for the current compiler. Please consider adding it."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "Licence.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.hpp",
             src=os.path.join(self.source_folder, "include"),
             dst=os.path.join(self.package_folder, "include"))
        copy(self, "*.ipp",
             src=os.path.join(self.source_folder, "include"),
             dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        # See https://github.com/ned14/status-code/blob/38e1e862386cb38d577664fd681ef829b0e03fba/CMakeLists.txt#L126
        self.cpp_info.set_property("cmake_file_name", "status-code")
        self.cpp_info.set_property("cmake_target_name", "status-code::hl")
