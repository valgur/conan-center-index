import os
from pathlib import Path

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class LibclcConan(ConanFile):
    name = "libclc"
    description = "An implementation of the library requirements of the OpenCL C programming language"
    package_type = "static-library"
    license = "Apache-2.0 WITH LLVM-exception AND (NCSA OR MIT)"
    topics = ("llvm", "compiler")
    homepage = "https://libclc.llvm.org/"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "amdgpu": [True, False],
        "nvptx": [True, False],
    }
    default_options = {
        "amdgpu": True,
        "nvptx": True,
    }

    no_copy_source = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"llvm-core/{self.version}", options={
            "target_AMDGPU": self.options.amdgpu,
            "target_NVPTX": self.options.nvptx,
        })

    def _is_compatible_compiler(self):
        llvm_major = Version(self.version).major.value
        if self.settings.compiler == "clang":
            return Version(self.settings.compiler.version) >= llvm_major
        elif self.settings.compiler == "apple-clang":
            compiler_version = Version(self.settings.compiler.version)
            if compiler_version >= "16.3":
                return llvm_major <= 19
            if compiler_version >= "16.0":
                return llvm_major <= 17
            if compiler_version >= "15.0":
                return llvm_major <= 16
        return False

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20 <5]")
        self.tool_requires("ninja/[>=1.10.2 <2]")
        # Also requires Python during build
        if not self._is_compatible_compiler():
            self.tool_requires("llvm-core/<host_version>", options={
                "target_AMDGPU": self.options.amdgpu,
                "target_NVPTX": self.options.nvptx,
            })
            self.tool_requires(f"clang/{self.version}")

    def validate_build(self):
        check_min_cppstd(self, 17)

    def source(self):
        sources = self.conan_data["sources"][self.version]
        get(self, **sources["libclc"], destination="libclc", strip_root=True)
        get(self, **sources["cmake"], destination="cmake", strip_root=True)

    def _get_tool(self, package, tool):
        tool_path = str(Path(self.dependencies.build[package].package_folder, "bin", tool)).replace("\\", "/")
        if self.settings.os == "Windows":
            tool_path += ".exe"
        return tool_path

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        tc.cache_variables["CMAKE_VERBOSE_MAKEFILE"] = "ON"
        if "clang" in self.dependencies.build:
            tc.cache_variables["LLVM_TOOL_clang"] = self._get_tool("clang", "clang")
            for tool in ["llvm-as", "llvm-link", "opt"]:
                tc.cache_variables[f"LLVM_TOOL_{tool}"] = self._get_tool("llvm-core", tool)
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="libclc")
        cmake.build()

    def package(self):
        copy(self, "LICENSE.TXT", os.path.join(self.source_folder, "libclc"), os.path.join(self.package_folder, "licenses"))
        copy(self, "CREDITS.TXT", os.path.join(self.source_folder, "libclc"), os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_path", "libclc")
        # share/clc contains the generated *.bc LLVM IR files
        self.cpp_info.set_property("pkg_config_custom_content", f"libexecdir={os.path.join(self.package_folder, 'share', 'clc')}")
        self.cpp_info.libdirs = [os.path.join("share", "clc")]
