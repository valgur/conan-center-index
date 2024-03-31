import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm

required_conan_version = ">=1.53.0"


class SuiteSparseConan(ConanFile):
    name = "suitesparse"
    description = "SuiteSparse: a suite of sparse matrix algorithms"
    license = ""
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://people.engr.tamu.edu/davis/suitesparse.html"
    topics = ("graph-algorithms", "mathematics", "sparse-matrix",
              "csparse", "spqr", "umfpack", "klu", "cholmod", "graphblas", "colamd")

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

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("openblas/0.3.26")
        self.requires("llvm-openmp/17.0.6")
        self.requires("suitesparse-graphblas/9.1.0")
        # TODO: unvendor metis

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.22 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        venv = VirtualBuildEnv(self)
        venv.generate()

        tc = CMakeToolchain(self)
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.variables["SUITESPARSE_DEMOS"] = False
        tc.variables["SUITESPARSE_USE_STRICT"] = True  # don't allow implicit dependencies
        tc.variables["SUITESPARSE_USE_OPENMP"] = True
        tc.variables["SUITESPARSE_USE_CUDA"] = False  # TODO
        tc.variables["SUITESPARSE_CUDA_ARCHITECTURES"] = "all"  # TODO
        tc.variables["BLA_VENDOR"] = "OpenBLAS"
        tc.variables["SUITESPARSE_USE_SYSTEM_AMD"] = False  # use vendored AMD
        tc.variables["SUITESPARSE_USE_SYSTEM_BTF"] = False  # use vendored BTF
        tc.variables["SUITESPARSE_USE_SYSTEM_CAMD"] = False  # use vendored CAMD
        tc.variables["SUITESPARSE_USE_SYSTEM_CCOLAMD"] = False  # use vendored CCOLAMD
        tc.variables["SUITESPARSE_USE_SYSTEM_CHOLMOD"] = False  # use vendored CHOLMOD
        tc.variables["SUITESPARSE_USE_SYSTEM_COLAMD"] = False  # use vendored COLAMD
        tc.variables["SUITESPARSE_USE_SYSTEM_GRAPHBLAS"] = True
        tc.variables["SUITESPARSE_USE_SYSTEM_SUITESPARSE_CONFIG"] = False
        tc.variables["SUITESPARSE_USE_FORTRAN"] = False  # Fortran sources are translated to C instead
        tc.variables["CHOLMOD_GPL"] = True  # TODO: make configurable
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("suitesparse-graphblas", "cmake_target_name", "GraphBLAS")
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        # rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        # rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        # Unofficial targets
        self.cpp_info.set_property("cmake_file_name", "SuiteSparse")
        self.cpp_info.set_property("cmake_target_name", "SuiteSparse::SuiteSparse")
        self.cpp_info.set_property("pkg_config_name", "SuiteSparse")

        def _add_component(name, lib, version, requires, cmake_target=None):
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", cmake_target or f"SuiteSparse::{name}")
            component.set_property("pkg_config_name", name)
            component.set_property("component_version", version)
            component.libs = [lib]
            component.requires = ["openblas::openblas", "llvm-openmp::llvm-openmp"]
            component.requires += requires
            component.includedirs.append(os.path.join("include", "suitesparse"))

            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs.extend(["m", "pthread", "dl"])

        _add_component("AMD", "amd", "3.3.2", ["SuiteSparse_config"])

        # BTF: Software package for permuting a matrix into block upper triangular form in SuiteSparse
        _add_component("BTF", "btf", "2.3.2", [])

        # CAMD: Routines for permuting sparse matrices prior to factorization in SuiteSparse
        _add_component("CAMD", "camd", "3.3.2", ["SuiteSparse_config"])

        # CCOLAMD: Routines for column approximate minimum degree ordering algorithm in SuiteSparse
        _add_component("CCOLAMD", "ccolamd", "3.3.3", ["SuiteSparse_config"])

        # CHOLMOD: Routines for factorizing sparse symmetric positive definite matrices in SuiteSparse
        _add_component("CHOLMOD", "cholmod", "5.2.1", ["SuiteSparse_config", "AMD", "COLAMD"])

        # COLAMD: Routines for column approximate minimum degree ordering algorithm in SuiteSparse
        _add_component("COLAMD", "colamd", "3.3.3", ["SuiteSparse_config"])

        # CXSparse: Direct methods for sparse linear systems for real and complex matrices in SuiteSparse
        _add_component("CXSparse", "cxsparse", "4.4.0", ["SuiteSparse_config"])

        # KLU: Routines for solving sparse linear systems of equations in SuiteSparse
        _add_component("KLU", "klu", "2.3.3", ["SuiteSparse_config", "AMD", "COLAMD", "BTF"])

        # KLU_CHOLMOD: Routines for sample ordering for KLU in SuiteSparse
        _add_component("KLU_CHOLMOD", "klu_cholmod", "2.3.3", ["KLU", "BTF", "CHOLMOD"])

        # LAGraph: Library plus test harness for collecting algorithms that use GraphBLAS
        _add_component("LAGraph", "lagraph", "1.1.3", ["suitesparse-graphblas::suitesparse-graphblas"])
        self.cpp_info.components["LAGraph"].defines.append("LG_DLL")

        # LDL: A sparse LDL' factorization and solve package in SuiteSparse
        _add_component("LDL", "ldl", "3.3.2", ["AMD", "SuiteSparse_config"])

        # ParU: Routines for solving sparse linear system via parallel multifrontal LU factorization algorithms in SuiteSparse
        _add_component("ParU", "paru", "0.1.3", ["SuiteSparse_config", "UMFPACK"])

        # RBio: MATLAB Toolbox for reading/writing sparse matrices in Rutherford/Boeing format in SuiteSparse
        _add_component("RBio", "rbio", "4.3.2", ["SuiteSparse_config"])

        # SPEX: Software package for SParse EXact algebra in SuiteSparse
        # Also includes spexpython library not listed here
        _add_component("SPEX", "spex", "3.1.0", ["SuiteSparse_config", "AMD", "COLAMD"])

        # SPQR: Multithreaded, multifrontal, rank-revealing sparse QR factorization method in SuiteSparse
        _add_component("SPQR", "spqr", "4.3.3", ["SuiteSparse_config", "CHOLMOD"])

        # SuiteSparse_config: Configuration for SuiteSparse
        _add_component("SuiteSparse_config", "suitesparseconfig", self.version, [], cmake_target="SuiteSparse::SuiteSparseConfig")

        # SuiteSparse_Mongoose: Graph partitioning library in SuiteSparse
        _add_component("SuiteSparse_Mongoose", "suitesparse_mongoose", "3.3.3", ["SuiteSparse_config"], cmake_target="SuiteSparse::Mongoose")

        # UMFPACK: Routines solving sparse linear systems via LU factorization in SuiteSparse
        _add_component("UMFPACK", "umfpack", "6.3.3", ["SuiteSparse_config", "AMD"])
