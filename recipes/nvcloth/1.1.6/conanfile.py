import os
import shutil

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.env import Environment
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NvclothConan(ConanFile):
    name = "nvcloth"
    description = "NvCloth is a library that provides low level access to a cloth solver designed for realtime interactive applications."
    license = "DocumentRef-license.txt:LicenseRef-Nvidia-Source-Code-License"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/NVIDIAGameWorks/NvCloth"
    topics = ("physics", "physics-engine", "physics-simulation", "game-development", "cuda")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_cuda": [True, False],
        "use_dx11": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "use_cuda": False,
        "use_dx11": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.use_cuda:
            del self.settings.cuda

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.use_cuda:
            self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.os not in ["Windows", "Linux", "FreeBSD", "Macos", "Android", "iOS"]:
            raise ConanInvalidConfiguration(f"{self.settings.os} is not supported")
        if self.settings.os in ["Windows", "Macos"] and not self.options.shared:
            raise ConanInvalidConfiguration(f"Static builds are not supported on {self.settings.os}")
        if self.settings.os in ["iOS", "Android"] and self.options.shared:
            raise ConanInvalidConfiguration(f"Shared builds are not supported on {self.settings.os}")
        check_min_cppstd(self, 11)
        if self.options.use_cuda:
            self._utils.validate_cuda_settings(self)

    def build_requirements(self):
        if self.options.use_cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        rmdir(self, "NvCloth/samples")
        # There is no reason to force consumer of PhysX public headers to use one of
        # NDEBUG or _DEBUG, since none of them relies on NDEBUG or _DEBUG
        replace_in_file(self, "PxShared/include/foundation/PxPreprocessor.h",
                        "#error Exactly one of NDEBUG and _DEBUG needs to be defined!",
                        "// #error Exactly one of NDEBUG and _DEBUG needs to be defined!")
        shutil.copy("NvCloth/include/NvCloth/Callbacks.h",
                    "NvCloth/include/NvCloth/Callbacks.h.origin")
        # Let NvccToolchain manage the CUDA architecture flags
        replace_in_file(self, "NvCloth/compiler/cmake/linux/NvCloth.cmake",
                        "-gencode arch=compute_20,code=sm_20 "
                        "-gencode arch=compute_30,code=sm_30 "
                        "-gencode arch=compute_35,code=sm_35 "
                        "-gencode arch=compute_50,code=sm_50 "
                        "-gencode arch=compute_50,code=compute_50", "")
        replace_in_file(self, "NvCloth/compiler/cmake/windows/NvCloth.cmake",
                        "-gencode arch=compute_30,code=sm_30 "
                        "-gencode arch=compute_35,code=sm_35 "
                        "-gencode arch=compute_50,code=sm_50 "
                        "-gencode arch=compute_50,code=compute_50 "
                        "-gencode arch=compute_60,code=sm_60", "")
        # Fix a typo
        replace_in_file(self, "NvCloth/src/cuda/CuSolver.cpp", "../Ps/PsSort.h", "../ps/PsSort.h")

    @property
    def _target_build_platform(self):
        return {
            "Windows": "windows",
            "Linux": "linux",
            "Macos": "mac",
            "Android": "android",
            "iOS": "ios",
        }.get(str(self.settings.os))

    def generate(self):
        tc = CMakeToolchain(self)
        if not self.options.shared:
            tc.cache_variables["PX_STATIC_LIBRARIES"] = 1
        tc.cache_variables["STATIC_WINCRT"] = is_msvc_static_runtime(self)
        tc.cache_variables["NV_CLOTH_ENABLE_CUDA"] = self.options.use_cuda
        tc.cache_variables["NV_CLOTH_ENABLE_DX11"] = self.options.use_dx11
        tc.cache_variables["TARGET_BUILD_PLATFORM"] = self._target_build_platform
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5"  # CMake 4 support
        if Version(self.version) > "1.1.6":
            raise ConanException("CMAKE_POLICY_VERSION_MINIMUM hardcoded to 3.5, check if new version supports CMake 4")
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self.options.use_cuda:
            tc = self._utils.NvccToolchain(self)
            tc.generate()

        env = Environment()
        env.define_path("GW_DEPS_ROOT", self.source_folder)
        env.vars(self).save_script("conan_build_vars")

    def _patch_sources(self):
        if self.settings.build_type == "Debug":
            shutil.copy(os.path.join(self.source_folder, "NvCloth/include/NvCloth/Callbacks.h"),
                        os.path.join(self.source_folder, "NvCloth/include/NvCloth/Callbacks.h.patched"))
            shutil.copy(os.path.join(self.source_folder, "NvCloth/include/NvCloth/Callbacks.h.origin"),
                        os.path.join(self.source_folder, "NvCloth/include/NvCloth/Callbacks.h"))

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        if self.settings.build_type == "Debug":
            shutil.copy(os.path.join(self.source_folder, "NvCloth/include/NvCloth/Callbacks.h.patched"),
                        os.path.join(self.source_folder, "NvCloth/include/NvCloth/Callbacks.h"))
        copy(self, "NvCloth/license.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder, keep_path=False)
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.source_folder, "NvCloth/include"))
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.source_folder, "NvCloth/extensions/include"))
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.source_folder, "PxShared/include"))
        copy(self, "*.a", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
        copy(self, "*.lib", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
        copy(self, "*.dylib*", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)
        copy(self, "*.dll", dst=os.path.join(self.package_folder, "bin"), src=self.build_folder, keep_path=False)
        copy(self, "*.so", dst=os.path.join(self.package_folder, "lib"), src=self.build_folder, keep_path=False)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "nvcloth")
        self.cpp_info.set_property("cmake_target_name", "nvcloth::nvcloth")

        if self.settings.build_type == "Debug":
            debug_suffix = "DEBUG"
        else:
            debug_suffix = ""

        if self.settings.os == "Windows" and self.settings.arch == "x86_64":
            arch_suffix = "_x64"
        else:
            arch_suffix = ""

        self.cpp_info.libs = [f"NvCloth{debug_suffix}{arch_suffix}"]

        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.system_libs.append("m")
