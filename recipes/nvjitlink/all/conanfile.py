import os
from functools import cached_property

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvJitLinkConan(ConanFile):
    name = "nvjitlink"
    description = "nvJitLink: NVIDIA compiler library for JIT LTO functionality"
    license = "DocumentRef-LICENSE:LicenseRef-NVIDIA-CUDA-Toolkit-EULA"
    homepage = "https://docs.nvidia.com/cuda/nvjitlink/"
    topics = ("cuda", "jit", "linker", "lto")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "cmake_alias": [True, False],
        "use_stubs": [True, False],
    }
    default_options = {
        "shared": False,
        "cmake_alias": True,
        "use_stubs": False,
    }

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self, enable_private=True)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.use_stubs

    def configure(self):
        if not self.options.shared or self.settings.os == "Windows":
            self.options.rm_safe("use_stubs")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda.version
        del self.info.settings.cuda.architectures
        self.info.settings.rm_safe("cmake_alias")
        self.info.settings.rm_safe("use_stubs")

    def requirements(self):
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("nvptxcompiler", transitive_headers=True)

    def validate(self):
        self.cuda.validate_package("libnvjitlink")

    def build(self):
        self.cuda.download_package("libnvjitlink")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*", os.path.join(self.source_folder, "src"), os.path.join(self.package_folder, "share", "nvjitlink", "src"))
        if self.settings.os == "Linux":
            if self.options.shared:
                copy(self, "*.so*", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
                copy(self, "*.so*", os.path.join(self.source_folder, "lib", "stubs"), os.path.join(self.package_folder, "lib", "stubs"))
            else:
                copy(self, "*_static.a", os.path.join(self.source_folder, "lib"), os.path.join(self.package_folder, "lib"))
        else:
            if self.options.shared:
                copy(self, "nvJitLink*.dll", os.path.join(self.source_folder, "bin"), os.path.join(self.package_folder, "bin"))
                copy(self, "nvJitLink.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))
            else:
                copy(self, "nvJitLink_static.lib", os.path.join(self.source_folder, "lib", "x64"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        suffix = "" if self.options.shared else "_static"
        self.cpp_info.set_property("pkg_config_name", f"nvjitlink-{self.cuda.version}")
        self.cpp_info.set_property("cmake_target_name", f"CUDA::nvJitLink{suffix}")
        if self.options.get_safe("cmake_alias"):
            alias_suffix = "_static" if self.options.shared else ""
            self.cpp_info.set_property("cmake_target_aliases", [f"CUDA::nvJitLink{alias_suffix}"])
        self.cpp_info.libs = [f"nvJitLink{suffix}"]
        self.cpp_info.srcdirs = ["share/nvjitlink/src"]
        if self.options.get_safe("use_stubs"):
            self.cpp_info.libdirs = ["lib/stubs", "lib"]
        self.cpp_info.requires = ["cudart::cudart_", "nvptxcompiler::nvptxcompiler"]
        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.system_libs = ["rt", "pthread", "m", "dl"]
