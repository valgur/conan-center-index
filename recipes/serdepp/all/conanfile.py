# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class SerdeppConan(ConanFile):
    name = "serdepp"
    description = "c++ serialize and deserialize adaptor library like rust serde.rs"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/injae/serdepp"
    topics = ("yaml", "toml", "serialization", "json", "reflection", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_nlohmann_json": [True, False],
        "with_rapidjson": [True, False],
        "with_fmt": [True, False],
        "with_toml11": [True, False],
        "with_yamlcpp": [True, False],
    }
    default_options = {
        "with_nlohmann_json": True,
        "with_rapidjson": True,
        "with_fmt": True,
        "with_toml11": True,
        "with_yamlcpp": True,
    }
    no_copy_source = True

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "7",
            "Visual Studio": "17",
            "clang": "5",
            "apple-clang": "10",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("nameof/0.10.1")
        self.requires("magic_enum/0.7.3")
        if self.options.with_toml11:
            self.requires("toml11/3.7.0")
        if self.options.with_yamlcpp:
            self.requires("yaml-cpp/0.7.0")
        if self.options.with_rapidjson:
            self.requires("rapidjson/1.1.0")
        if self.options.with_fmt:
            self.requires("fmt/8.1.1")
        if self.options.with_nlohmann_json:
            self.requires("nlohmann_json/3.10.5")

    def package_id(self):
        self.info.clear()

    def validate(self):
        compiler = self.settings.compiler
        if compiler.get_safe("cppstd"):
            check_min_cppstd(self, "17")
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)

        if not minimum_version:
            self.output.warn(
                f"{self.name} requires C++17. Your compiler is unknown. Assuming it supports C++17."
            )
        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(f"{self.name} requires a compiler that supports at least C++17")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        s = lambda x: os.path.join(self.source_folder, x)
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        include = os.path.join("include", "serdepp")
        copy(self, "*.hpp", dst=include, src=s(include))
        attribute = os.path.join(include, "attribute")
        copy(self, "*.hpp", dst=attribute, src=s(attribute))
        adaptor = os.path.join(include, "adaptor")
        copy(self, "reflection.hpp", dst=adaptor, src=s(adaptor))
        copy(self, "sstream.hpp", dst=adaptor, src=s(adaptor))
        if self.options.with_toml11:
            copy(self, "toml11.hpp", dst=adaptor, src=s(adaptor))
        if self.options.with_yamlcpp:
            copy(self, "yaml-cpp.hpp", dst=adaptor, src=s(adaptor))
        if self.options.with_rapidjson:
            copy(self, "rapidjson.hpp", dst=adaptor, src=s(adaptor))
        if self.options.with_fmt:
            copy(self, "fmt.hpp", dst=adaptor, src=s(adaptor))
        if self.options.with_nlohmann_json:
            copy(self, "nlohmann_json.hpp", dst=adaptor, src=s(adaptor))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
