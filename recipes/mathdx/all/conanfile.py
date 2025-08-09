import os
import textwrap
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.8"


class MathDxConan(ConanFile):
    name = "mathdx"
    description = "NVIDIA Math Device Extensions (MathDx) libraries."
    license = "DocumentRef-LICENSE.txt:LicenseRef-MathDx-Software-License-Agreement"
    homepage = "https://docs.nvidia.com/cuda/cublasdx/"
    topics = ("cuda", "mathdx", "cuda-kernel", "blas", "cublas", "cufft", "cusolver", "nvcomp", "linear-algebra", "fft")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "cublasdx": [True, False],
        "cufftdx": [True, False],
        "curanddx": [True, False],
        "cusolverdx": [True, False],
        "nvcompdx": [True, False],
    }
    default_options = {
        "cublasdx": True,
        "cufftdx": True,
        "curanddx": True,
        "cusolverdx": True,
        "nvcompdx": True,
    }

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    @property
    def _cuda_version(self):
        return self.dependencies["cudart"].ref.version

    @property
    def _min_cuda_version(self):
        if self.options.cusolverdx or self.options.nvcompdx:
            return "12.6.3"
        if self.options.cublasdx or self.options.curanddx:
            return "11.4"
        return "11.0"

    @property
    def _header_only(self):
        return not self.options.cusolverdx and not self.options.nvcompdx

    @property
    def _use_fatbin(self):
        return self._cuda_version >= "12.8"

    def configure(self):
        if self._header_only:
            self.package_type = "header-library"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        if self.info.options.cusolverdx or self.info.options.nvcompdx:
            # Export a pre-built static library
            del self.info.settings.compiler
            del self.info.settings.build_type
        else:
            # cublasdx, cufftdx and curanddx are header-only
            self.info.settings.clear()

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version} >=11.4]", transitive_headers=True, transitive_libs=True)
        self.requires("cutlass/[>=3.9.0]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if not self._header_only and not self._use_fatbin:
            if self.settings.os != "Linux" and self.settings.arch != "x86_64":
                raise ConanInvalidConfiguration("Only x86_64 Linux is supported for CUDA version < 12.8 due to a lack of .fatbin support")
        self._utils.validate_cuda_settings(self)
        self._utils.check_min_cuda_architecture(self, 70)
        if self._cuda_version < self._min_cuda_version:
            raise ConanInvalidConfiguration(f"cudart {self._min_cuda_version} or higher is required")

        compiler_version = Version(self.settings.compiler.version)
        if self.settings.compiler == "gcc" and compiler_version < "7":
            raise ConanInvalidConfiguration(f"{self.name} requires GCC >= 7")
        if self.settings.compiler == "clang" and compiler_version < "9":
            raise ConanInvalidConfiguration(f"{self.name} requires Clang >= 9")
        check_min_cppstd(self, 17)

    @property
    def _source_path(self):
        return next(Path(self.source_folder).rglob("LICENSE.txt")).parent

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        rmdir(self, self._source_path / "doc")
        rmdir(self, self._source_path / "example")
        rmdir(self, self._source_path / "external")
        rmdir(self, self._source_path / "lib" / "cmake")

    def package(self):
        copy(self, "LICENSE.txt", self._source_path, os.path.join(self.package_folder, "licenses"))
        for name in ["cublasdx", "cufftdx", "curanddx", "cusolverdx", "nvcompdx", "commondx"]:
            if self.options.get_safe(name) or name == "commondx":
                copy(self, f"{name}.hpp", os.path.join(self._source_path, "include"), os.path.join(self.package_folder, "include"))
                copy(self, "*", os.path.join(self._source_path, "include", name), os.path.join(self.package_folder, "include", name))
                if self._use_fatbin:
                    copy(self, f"lib{name}.fatbin", os.path.join(self._source_path, "lib"), os.path.join(self.package_folder, "lib"))
                else:
                    copy(self, f"lib{name}.a", os.path.join(self._source_path, "lib"), os.path.join(self.package_folder, "lib"))

        if self.options.cufftdx:
            copy(self, "*", os.path.join(self._source_path, "src", "cufftdx"), os.path.join(self.package_folder, "share", "cufftdx", "src"))

        if self._use_fatbin:
            fatbin_content = ["get_filename_component(PACKAGE_PREFIX_DIR ${CMAKE_CURRENT_LIST_DIR}/../../ ABSOLUTE)\n"]
            fatbin_content.append(textwrap.dedent("""
                if(NOT TARGET cufftdx::cufftdx_separate_twiddles_lut)
                    if(NOT DEFINED cufftdx_SEPARATE_TWIDDLES_CUDA_ARCHITECTURES OR cufftdx_SEPARATE_TWIDDLES_CUDA_ARCHITECTURES STREQUAL "")
                        set(cufftdx_SEPARATE_TWIDDLES_CUDA_ARCHITECTURES ${CMAKE_CUDA_ARCHITECTURES})
                    endif()

                    set(cufftdx_SEPARATE_TWIDDLES_SRCS "${PACKAGE_PREFIX_DIR}/share/cufftdx/src/lut.cu")
                    add_library(cufftdx_separate_twiddles_lut OBJECT EXCLUDE_FROM_ALL ${cufftdx_SEPARATE_TWIDDLES_SRCS})
                    add_library(cufftdx::cufftdx_separate_twiddles_lut ALIAS cufftdx_separate_twiddles_lut)
                    set_target_properties(cufftdx_separate_twiddles_lut
                        PROPERTIES
                            CUDA_SEPARABLE_COMPILATION ON
                            CUDA_ARCHITECTURES "${cufftdx_SEPARATE_TWIDDLES_CUDA_ARCHITECTURES}"
                    )
                    target_compile_definitions(cufftdx_separate_twiddles_lut PUBLIC CUFFTDX_USE_SEPARATE_TWIDDLES)
                    target_link_libraries(cufftdx_separate_twiddles_lut PUBLIC cufftdx::cufftdx)
                endif()
            """))
            if self.options.cusolverdx:
                fatbin_content.append(self._generate_cmake_fatbin_targets(
                    "cusolverdx", "lib/libcusolverdx.fatbin", aliases=[
                        "cusolverdx::cusolverdx_fatbin",
                        "mathdx::cusolverdx_fatbin",
                        "cusolverdx::cusolverdx",
                        "mathdx::cusolverdx",
                    ]
                ))
            if self.options.nvcompdx:
                fatbin_content.append(self._generate_cmake_fatbin_targets(
                    "nvcompdx", "lib/libnvcompdx.fatbin", aliases=[
                        "nvcompdx::nvcompdx_fatbin",
                        "mathdx::nvcompdx_fatbin",
                        "nvcompdx::nvcompdx",
                        "mathdx::nvcompdx",
                    ]
                ))
            save(self, os.path.join(self.package_folder, "share", "conan", "mathdx_fatbin_targets.cmake"), "\n".join(fatbin_content))

    def _generate_cmake_fatbin_targets(self, name, fatbin_rel_path, aliases=None, extra=None, add_to_aggregate=True):
        body = textwrap.dedent(f"""
            add_library({name}_fatbin INTERFACE)
            set({name}_FATBIN "${{PACKAGE_PREFIX_DIR}}/{fatbin_rel_path}")
            target_link_options({name}_fatbin INTERFACE $<DEVICE_LINK:${{{name}_FATBIN}} -dlto>)
            target_link_libraries({name}_fatbin INTERFACE commondx::commondx)
        """)
        if aliases:
            body += "".join(f"add_library({alias} ALIAS {name}_fatbin)\n" for alias in aliases)
        if extra:
            body += extra + "\n"
        if add_to_aggregate:
            body += f"target_link_libraries(mathdx::mathdx INTERFACE {name}_fatbin)\n"
        return f"if(NOT TARGET {name}_fatbin){textwrap.indent(body, '    ')}endif()\n"

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "mathdx")
        self.cpp_info.set_property("cmake_target_name", "mathdx::mathdx")

        self.cpp_info.components["commondx"].set_property("cmake_target_name", "commondx::commondx")
        self.cpp_info.components["commondx"].set_property("cmake_target_aliases", ["mathdx::commondx"])
        self.cpp_info.components["commondx"].libs = []
        self.cpp_info.components["commondx"].libdirs = []
        self.cpp_info.components["commondx"].requires = ["cudart::cudart_", "cutlass::cutlass"]

        if self.options.cublasdx:
            self.cpp_info.components["cublasdx"].set_property("cmake_target_name", "cublasdx::cublasdx")
            self.cpp_info.components["cublasdx"].set_property("cmake_target_aliases", ["mathdx::cublasdx"])
            self.cpp_info.components["cublasdx"].libs = []
            self.cpp_info.components["cublasdx"].libdirs = []
            self.cpp_info.components["cublasdx"].requires = ["commondx"]

        if self.options.cufftdx:
            self.cpp_info.components["cufftdx"].set_property("cmake_target_name", "cufftdx::cufftdx")
            self.cpp_info.components["cufftdx"].set_property("cmake_target_aliases", ["mathdx::cufftdx"])
            self.cpp_info.components["cufftdx"].libs = []
            self.cpp_info.components["cufftdx"].libdirs = []
            self.cpp_info.components["cufftdx"].srcdirs = ["share/cufftdx/src"]
            self.cpp_info.components["cufftdx"].requires = ["commondx"]

        if self.options.curanddx:
            self.cpp_info.components["curanddx"].set_property("cmake_target_name", "curanddx::curanddx")
            self.cpp_info.components["curanddx"].set_property("cmake_target_aliases", ["mathdx::curanddx"])
            self.cpp_info.components["curanddx"].libs = []
            self.cpp_info.components["curanddx"].libdirs = []
            self.cpp_info.components["curanddx"].requires = ["commondx"]

        if self.options.cusolverdx and not self._use_fatbin:
            self.cpp_info.components["cusolverdx"].set_property("cmake_target_name", "cusolverdx::cusolverdx")
            self.cpp_info.components["cusolverdx"].set_property("cmake_target_aliases", ["mathdx::cusolverdx"])
            self.cpp_info.components["cusolverdx"].libs = ["cusolverdx"]
            self.cpp_info.components["cusolverdx"].requires = ["commondx"]

        if self.options.nvcompdx and not self._use_fatbin:
            self.cpp_info.components["nvcompdx"].set_property("cmake_target_name", "nvcompdx::nvcompdx")
            self.cpp_info.components["nvcompdx"].set_property("cmake_target_aliases", ["mathdx::nvcompdx"])
            self.cpp_info.components["nvcompdx"].libs = ["nvcompdx"]
            self.cpp_info.components["nvcompdx"].requires = ["commondx"]

        if self._use_fatbin:
            self.cpp_info.builddirs = ["share/conan"]
            self.cpp_info.set_property("cmake_build_modules", ["share/conan/mathdx_fatbin_targets.cmake"])
