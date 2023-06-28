import os
import textwrap

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import get, copy, save
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class HanaConan(ConanFile):
    name = "hana"
    description = (
        "Hana is a header-only library for C++ metaprogramming suited for "
        "computations on both types and values."
    )
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://boostorg.github.io/hana/"
    topics = ("metaprogramming", "boost", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True
    deprecated = "boost"

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "5",
            "Visual Studio": "14",
            "clang": "3.4",
            "apple-clang": "3.4",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, "14")
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if not minimum_version:
            self.output.warning(
                f"{self.name} {self.version} requires C++14. Your compiler is unknown. "
                "Assuming it supports C++14."
            )
        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.name} {self.version} requires C++14, which your compiler does not support."
            )

        raise ConanInvalidConfiguration(f"{self.ref} is deprecated of Boost. Please, use boost package.")

    def source(self):
        get(**self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.md", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(
            self,
            "*.hpp",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )
        self._create_cmake_module_alias_targets(
            self,
            os.path.join(self.package_folder, self._module_file_rel_path),
            {
                "hana": "hana::hana",
            },
        )

    @staticmethod
    def _create_cmake_module_alias_targets(conanfile, module_file, targets):
        content = ""
        for alias, aliased in targets.items():
            content += textwrap.dedent(f"""\
                if(TARGET {aliased} AND NOT TARGET {alias})
                    add_library({alias} INTERFACE IMPORTED)
                    set_property(TARGET {alias} PROPERTY INTERFACE_LINK_LIBRARIES {aliased})
                endif()
            """)
        save(conanfile, module_file, content)

    @property
    def _module_subfolder(self):
        return os.path.join("lib", "cmake")

    @property
    def _module_file_rel_path(self):
        return os.path.join(self._module_subfolder, "conan-official-{}-targets.cmake".format(self.name))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.builddirs.append(self._module_subfolder)

        self.cpp_info.set_property("cmake_file_name", "Hana")
        self.cpp_info.set_property("cmake_target_name", "hana")
        self.cpp_info.set_property("pkg_config_name", "hana")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "Hana"
        self.cpp_info.filenames["cmake_find_package_multi"] = "Hana"
        self.cpp_info.names["cmake_find_package"] = "hana"
        self.cpp_info.names["cmake_find_package_multi"] = "hana"
        self.cpp_info.build_modules["cmake_find_package"] = [self._module_file_rel_path]
        self.cpp_info.build_modules["cmake_find_package_multi"] = [self._module_file_rel_path]
