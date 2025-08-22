import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class HiGHSConan(ConanFile):
    name = "highs"
    description = "high performance serial and parallel solver for large scale sparse linear optimization problems"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.highs.dev/"
    topics = ("simplex", "interior point", "solver", "linear", "programming")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
        "with_cuda": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": False,
        "with_cuda": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.with_cuda:
            del self.settings.cuda

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib-ng/[^2.0]")
        if self.options.with_cuda:
            self._utils.cuda_requires(self, "cudart")
            self._utils.cuda_requires(self, "cublas")
            self._utils.cuda_requires(self, "cusparse")

    def validate(self):
        if self.options.with_cuda:
            self._utils.validate_cuda_settings(self)

    def build_requirements(self):
        if self.options.with_cuda:
            self.tool_requires("cmake/[>=3.25]")
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Don't embed the build-time directories in the installed library RPATH
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_CXX_EXE"] = self.options.tools
        tc.variables["CUPDLP_GPU"] = self.options.with_cuda
        tc.variables["FAST_BUILD"] = True
        tc.variables["BUILD_TESTING"] = False
        tc.variables["PYTHON"] = False
        tc.variables["FORTRAN"] = False
        tc.variables["CSHARP"] = False
        tc.variables["EXP"] = False
        tc.variables["BUILD_EXAMPLES"] = False
        tc.variables["JULIA"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self.options.with_cuda:
            nvcc_tc = self._utils.NvccToolchain(self)
            nvcc_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "highs")

        self.cpp_info.components["highs_"].set_property("cmake_target_name", "highs::highs")
        self.cpp_info.components["highs_"].set_property("pkg_config_name", "highs")
        self.cpp_info.components["highs_"].libs = ["highs"]
        self.cpp_info.components["highs_"].includedirs.append("include/highs")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["highs_"].system_libs = ["m", "pthread"]
        self.cpp_info.components["highs_"].requires = ["zlib-ng::zlib-ng"]

        if self.options.with_cuda:
            self.cpp_info.components["cudalin"].set_property("cmake_target_name", "highs::cudalin")
            self.cpp_info.components["cudalin"].set_property("pkg_config_name", "highs_cudalin")
            self.cpp_info.components["cudalin"].libs = ["cudalin"]
            self.cpp_info.components["cudalin"].requires = ["cudart::cudart_", "cublas::cublas_", "cusparse::cusparse"]
            self.cpp_info.components["highs_"].requires.append("cudalin")
