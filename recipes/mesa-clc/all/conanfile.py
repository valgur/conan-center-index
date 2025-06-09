import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.files import *
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain

required_conan_version = ">=2.1"


class MesaClcConan(ConanFile):
    name = "mesa-clc"
    description = "Mesa OpenCL C to SPIR-V compiler"
    license = "MIT"
    homepage = "https://mesa3d.org/"
    topics = ("opencl", "spirv", "compiler")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    default_options = {
        "llvm-core/*:target_AMDGPU": True,
        "llvm-core/*:target_NVPTX": True,
    }
    default_build_options = {
        "llvm-core/*:target_AMDGPU": True,
        "llvm-core/*:target_NVPTX": True,
    }

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("llvm-core/[>=19]")
        self.requires("spirv-llvm-translator/[>=19]")
        self.requires("clang/[>=19]")
        self.requires("libclc/[>=19]")
        self.requires("spirv-tools/[^1.3.239.0]")

    def validate(self):
        llvm_opts = self.dependencies["llvm-core"].options
        if not llvm_opts.target_AMDGPU and not llvm_opts.target_NVPTX:
            raise ConanInvalidConfiguration("-o llvm-core/*:target_AMDGPU=True -o llvm-core/*:target_NVPTX=True is required to build Mesa with LLVM support")

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        self.tool_requires("llvm-core/<host_version>")
        # Also uses Python during build

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "meson.build",
                        "cpp.find_library('clang-cpp', dirs : llvm_libdir, required : false)",
                        "dependency('clang-cpp', required : true)")

    def generate(self):
        tc = MesonToolchain(self)
        tc.project_options["mesa-clc"] = "enabled"
        tc.project_options["install-mesa-clc"] = True
        tc.project_options["mesa-clc-bundle-headers"] = "enabled"
        tc.project_options["llvm"] = "enabled"
        tc.project_options["shared-llvm"] = "enabled" if self.dependencies["llvm-core"].options.shared else "disabled"

        # disable everything else
        tc.project_options["auto_features"] = "disabled"
        tc.project_options["microsoft-clc"] = "disabled"
        tc.project_options["intel-clc"] = "system"
        tc.project_options["build-aco-tests"] = False
        tc.project_options["build-tests"] = False
        tc.project_options["datasources"] = ""
        tc.project_options["draw-use-llvm"] = False
        tc.project_options["dri3"] = "disabled"
        tc.project_options["egl"] = "disabled"
        tc.project_options["enable-glcpp-tests"] = False
        tc.project_options["expat"] = "disabled"
        tc.project_options["freedreno-kmds"] = ""
        tc.project_options["gallium-d3d10umd"] = False
        tc.project_options["gallium-d3d12-video"] = "disabled"
        tc.project_options["gallium-drivers"] = ""
        tc.project_options["gallium-extra-hud"] = False
        tc.project_options["gallium-omx"] = "disabled"
        tc.project_options["gallium-rusticl"] = False
        tc.project_options["gallium-va"] = "disabled"
        tc.project_options["gallium-vdpau"] = "disabled"
        tc.project_options["gbm"] = "disabled"
        tc.project_options["gles1"] = "disabled"
        tc.project_options["gles2"] = "disabled"
        tc.project_options["glvnd"] = "disabled"
        tc.project_options["glx"] = "disabled"
        tc.project_options["imagination-srv"] = False
        tc.project_options["install-intel-gpu-tests"] = False
        tc.project_options["libunwind"] = "disabled"
        tc.project_options["opencl-spirv"] = False
        tc.project_options["opengl"] = False
        tc.project_options["perfetto"] = False
        tc.project_options["platforms"] = ""
        tc.project_options["spirv-to-dxil"] = False
        tc.project_options["shader-cache"] = "disabled"
        tc.project_options["sse2"] = True
        tc.project_options["tools"] = ""
        tc.project_options["valgrind"] = "disabled"
        tc.project_options["video-codecs"] = ""
        tc.project_options["vmware-mks-stats"] = False
        tc.project_options["vulkan-beta"] = False
        tc.project_options["vulkan-drivers"] = ""
        tc.project_options["vulkan-layers"] = ""
        tc.project_options["xmlconfig"] = "disabled"
        tc.project_options["zlib"] = "disabled"
        tc.project_options["zstd"] = "disabled"
        tc.generate()

        deps = PkgConfigDeps(self)
        deps.set_property("clang::clang-cpp", "pkg_config_name", "clang-cpp")
        deps.generate()

    def build(self):
        clang_libdir = self.dependencies["clang"].cpp_info.libdirs[0].replace("\\", "/")
        replace_in_file(self, os.path.join(self.source_folder, "src/compiler/clc/meson.build"),
                        "llvm_libdir", f"'{clang_libdir}'")
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "MIT", os.path.join(self.source_folder, "licenses"), os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
