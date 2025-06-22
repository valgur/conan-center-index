import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class XbyakRiscvConan(ConanFile):
    name = "xbyak_riscv"
    description = "Xbyak_riscv is a C++ header library that enables dynamically to assemble RISC-V instructions."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/herumi/xbyak_riscv"
    topics = ("jit", "assembler", "risc-v", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True
    options = {
        "vector_extensions": [True, False],
    }
    default_options = {
        "vector_extensions": False,
    }

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "COPYRIGHT", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "xbyak_riscv"), os.path.join(self.package_folder, "include", "xbyak_riscv"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "xbyak_riscv")
        self.cpp_info.set_property("cmake_target_name", "xbyak_riscv::xbyak_riscv")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if self.options.vector_extensions:
            self.cpp_info.defines.append("XBYAK_RISCV_V")
