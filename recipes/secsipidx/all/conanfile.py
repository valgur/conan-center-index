import os

from conan import ConanFile
from conan.tools.files import copy, export_conandata_patches, get, mkdir, replace_in_file
from conan.tools.layout import basic_layout

required_conan_version = ">=2.0"


class SecSIPIdXConan(ConanFile):
    name = "secsipidx"
    description = "Secure SIP Identity Extensions - IETF STIR/SHAKEN"
    license = "BSD-3-Clause-Clear"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/asipto/secsipidx"
    topics = ("sip", "telephony")
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

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("go/[~1.16]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # https://github.com/asipto/secsipidx/pull/26
        replace_in_file(self, os.path.join(self.source_folder, "csecsipid", "Makefile"),
                        "LIBVERSIONMAJOR", "LIBVERMAJ")

    def generate(self):
        pass

    def build(self):
        target = "libso" if self.options.shared else "liba"
        self.run(f"make {target}", cwd=os.path.join(self.source_folder, "csecsipid"))

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        target = "install-libso" if self.options.shared else "install-liba"
        mkdir(self, os.path.join(self.package_folder, "lib"))
        self.run(f"make {target} PREFIX={self.package_folder}", cwd=os.path.join(self.source_folder, "csecsipid"))
        copy(self, "*.h", os.path.join(self.source_folder, "csecsipid"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "secsipid-1")
        self.cpp_info.libs = ["secsipid"]
