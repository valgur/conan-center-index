import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class LlamaCppConan(ConanFile):
    name = "llama-cpp"
    description = "Inference of LLaMA model in pure C/C++"
    topics = ("llama", "llm", "ai")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ggerganov/llama.cpp"
    license = "MIT"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    package_type = "library"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_examples": [True, False],
        "with_cuda": [True, False],
        "with_curl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_examples": False,
        "with_cuda": False,
        "with_curl": False,
    }

    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.with_cuda:
            del self.settings.cuda

    def validate(self):
        check_min_cppstd(self, 17)
        if self.options.with_cuda:
            self.cuda.validate_settings()
            if self.version == "b4570" and self.cuda.major >= 13:
                raise ConanInvalidConfiguration(f"{self.ref} does not support CUDA 13 or newer")

    def validate_build(self):
        if self.settings.compiler == "msvc" and "arm" in self.settings.arch:
            raise ConanInvalidConfiguration("llama-cpp does not support ARM architecture on msvc, it recommends to use clang instead")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("openmp/system")
        if self.options.with_curl:
            self.requires("libcurl/[>=7.78 <9]")
        if self.options.with_cuda:
            self.cuda.requires("cudart")
            self.cuda.requires("cublas")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()

        tc = CMakeToolchain(self)
        tc.variables["BUILD_SHARED_LIBS"] = bool(self.options.shared)
        tc.variables["LLAMA_STANDALONE"] = False
        tc.variables["LLAMA_BUILD_TESTS"] = False
        tc.variables["LLAMA_BUILD_EXAMPLES"] = self.options.get_safe("with_examples")
        tc.variables["LLAMA_CURL"] = self.options.get_safe("with_curl")
        if cross_building(self):
            tc.variables["LLAMA_NATIVE"] = False
            tc.variables["GGML_NATIVE_DEFAULT"] = False
        tc.variables["GGML_BUILD_TESTS"] = False
        # Follow with_examples when newer versions can compile examples,
        # right now it tries to add_subdirectory to a non-existent folder
        tc.variables["GGML_BUILD_EXAMPLES"] = False
        tc.variables["GGML_CUDA"] = self.options.get_safe("with_cuda")
        tc.variables["GGML_OPENMP"] = True
        tc.generate()

        if self.options.with_cuda:
            cuda_tc = self.cuda.CudaToolchain()
            cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        copy(self, "*", os.path.join(self.source_folder, "models"), os.path.join(self.package_folder, "share", self.name, "models"))
        copy(self, "*.h*", os.path.join(self.source_folder, "common"), os.path.join(self.package_folder, "include", "common"))
        copy(self, "*common*.lib", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*common*.dll", src=self.build_folder, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
        copy(self, "*common*.so", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*common*.dylib", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*common*.a", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)

    def _get_backends(self):
        results = ["cpu"]
        if is_apple_os(self):
            results.append("blas")
            results.append("metal")
        if self.options.with_cuda:
            results.append("cuda")
        return results

    def package_info(self):
        # Also exports a ggml-config.cmake file officially, but Conan is not capable of generating config aliases
        self.cpp_info.set_property("cmake_file_name", "llama")
        self.cpp_info.set_property("pkg_config_name", "llama")

        self.cpp_info.components["ggml"].set_property("cmake_target_name", "ggml::all")
        self.cpp_info.components["ggml"].libs = ["ggml"]
        self.cpp_info.components["ggml"].resdirs = ["share"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["ggml"].system_libs.append("dl")

        self.cpp_info.components["llama"].set_property("cmake_target_name", "llama")
        self.cpp_info.components["llama"].libs = ["llama"]
        self.cpp_info.components["llama"].resdirs = ["share"]
        self.cpp_info.components["llama"].requires = ["ggml"]

        self.cpp_info.components["common"].includedirs = [os.path.join("include", "common")]
        self.cpp_info.components["common"].libs = ["common"]
        self.cpp_info.components["common"].requires = ["llama"]

        if self.options.with_curl:
            self.cpp_info.components["common"].requires.append("libcurl::libcurl")
            self.cpp_info.components["common"].defines.append("LLAMA_USE_CURL")

        if is_apple_os(self):
            self.cpp_info.components["common"].frameworks.extend(["Foundation", "Accelerate", "Metal"])
        elif self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["common"].system_libs.extend(["dl", "m", "pthread", "gomp"])

        self.cpp_info.components["ggml-base"].set_property("cmake_target_name", "ggml-base")
        self.cpp_info.components["ggml-base"].libs = ["ggml-base"]
        self.cpp_info.components["ggml-base"].resdirs = ["share"]

        self.cpp_info.components["ggml"].requires = ["ggml-base"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["ggml-base"].system_libs.extend(["dl", "m", "pthread"])

        if self.options.shared:
            self.cpp_info.components["llama"].defines.append("LLAMA_SHARED")
            self.cpp_info.components["ggml-base"].defines.append("GGML_SHARED")
            self.cpp_info.components["ggml"].defines.append("GGML_SHARED")

        backends = self._get_backends()
        for backend in backends:
            self.cpp_info.components[f"ggml-{backend}"].set_property("cmake_target_name", f"ggml-{backend}")
            self.cpp_info.components[f"ggml-{backend}"].libs = [f"ggml-{backend}"]
            self.cpp_info.components[f"ggml-{backend}"].resdirs = ["share"]
            if self.options.shared:
                self.cpp_info.components[f"ggml-{backend}"].defines.append("GGML_BACKEND_SHARED")
            self.cpp_info.components["ggml"].defines.append(f"GGML_USE_{backend.upper()}")
            self.cpp_info.components["ggml"].requires.append(f"ggml-{backend}")

        self.cpp_info.components["ggml-cpu"].requires.append("openmp::openmp")

        if self.options.with_cuda:
            self.cpp_info.components["ggml-cuda"].requires.extend(["cudart::cudart_", "cublas::cublas"])

        if is_apple_os(self):
            if "blas" in backends:
                self.cpp_info.components["ggml-blas"].frameworks.append("Accelerate")
            if "metal" in backends:
                self.cpp_info.components["ggml-metal"].frameworks.extend(["Metal", "MetalKit", "Foundation", "CoreFoundation"])
