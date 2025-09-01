import glob
import os
import shutil
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class SundialsConan(ConanFile):
    name = "sundials"
    license = "BSD-3-Clause"
    description = ("SUNDIALS is a family of software packages implemented with the goal of providing robust time integrators"
                   " and nonlinear solvers that can easily be incorporated into existing simulation codes.")
    topics = ("integrators", "ode", "non-linear-solvers")
    homepage = "https://github.com/LLNL/sundials"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_arkode": [True, False],
        "build_cvode": [True, False],
        "build_cvodes": [True, False],
        "build_ida": [True, False],
        "build_idas": [True, False],
        "build_kinsol": [True, False],
        "with_cuda": [True, False],
        "with_ginkgo": [True, False],
        "with_klu": [True, False],
        "with_lapack": [True, False],
        "with_mpi": [True, False],
        "with_openmp": [True, False],
        "index_size": [32, 64],
        "precision": ["single", "double", "extended"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_arkode": True,
        "build_cvode": True,
        "build_cvodes": True,
        "build_ida": True,
        "build_idas": True,
        "build_kinsol": True,
        "with_cuda": False,
        "with_ginkgo": False,
        "with_klu": True,
        "with_lapack": True,
        "with_mpi": False,
        "with_openmp": True,
        "index_size": 64,
        "precision": "double",
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        elif Version(self.version) < "6.0":
            del self.options.with_ginkgo
        if not self.options.with_cuda:
            del self.settings.cuda
        if not self.options.with_cuda and not self.options.with_mpi:
            self.languages = ["C"]

    def package_id(self):
        # Ginkgo is only used in an INTERFACE component
        self.info.options.rm_safe("with_ginkgo")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Used in public headers:
        # - caliper: sundials/sundials_profiler.h
        # - cuda: sunmemory/sunmemory_cuda.h, nvector/nvector_cuda.h
        # - ginkgo: sunmatrix/sunmatrix_ginkgo.hpp, sunlinsol/sunlinsol_ginkgo.hpp
        # - klu: sunlinsol/sunlinsol_klu.h
        # - mpi: sundials/sundials_types.h, sundials/priv/sundials_mpi_errors_impl.h
        if self.options.get_safe("with_ginkgo"):
            self.requires("ginkgo/1.8.0", transitive_headers=True, transitive_libs=True)
        if self.options.with_klu:
            self.requires("suitesparse-klu/[^2.3.5]", transitive_headers=True, transitive_libs=True)
        if self.options.with_lapack:
            self.requires("openblas/[>=0.3.28 <1]")
        if self.options.with_mpi:
            self.requires("openmpi/[^4.1.6]", transitive_headers=True, transitive_libs=True, options={"enable_cxx": True})
        if self.options.with_openmp:
            self.requires("openmp/system")
        if self.options.with_cuda:
            self.cuda.requires("cudart")
            if self.options.index_size == 32:
                self.cuda.requires("cusparse")
                self.cuda.requires("cusolver")

    def validate(self):
        if self.options.with_klu and self.options.precision != "double":
            # https://github.com/LLNL/sundials/blob/v7.1.1/cmake/tpl/SundialsKLU.cmake#L40
            raise ConanInvalidConfiguration("-o sundials/*:with_klu=True is only compatible with -o sundials/*:precision=double")
        if self.options.precision == "extended":
            # https://github.com/LLNL/sundials/blob/v7.1.1/cmake/tpl/SundialsGinkgo.cmake#L57
            # https://github.com/LLNL/sundials/blob/v7.1.1/cmake/tpl/SundialsLapack.cmake#L40
            for opt in ["with_cuda", "with_ginkgo", "with_lapack"]:
                if self.options.get_safe(opt):
                    raise ConanInvalidConfiguration(f"-o sundials/*:{opt}=True is not compatible with -o sundials/*:precision=extended")
        if self.options.with_mpi and not self.dependencies["openmpi"].options.enable_cxx:
            raise ConanInvalidConfiguration("-o openmpi/*:enable_cxx=True is required for -o sundials/*:with_mpi=True")
        if self.options.with_cuda:
            self.cuda.validate_settings()

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18 <5]")
        if self.options.with_cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "examples/CMakeLists.txt", "")

    @property
    def _ginkgo_backends(self):
        if not self.options.get_safe("with_ginkgo"):
            return []
        backends = ["REF"]
        if self.dependencies["ginkgo"].options.cuda:
            backends.append("CUDA")
        if self.dependencies["ginkgo"].options.openmp:
            backends.append("OMP")
        return backends

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_Fortran_COMPILER"] = ""
        tc.variables["EXAMPLES_ENABLE_C"] = False
        tc.variables["EXAMPLES_ENABLE_CXX"] = False
        tc.variables["EXAMPLES_INSTALL"] = False
        tc.variables["BUILD_BENCHMARKS"] = False
        tc.variables["SUNDIALS_TEST_UNITTESTS"] = False
        tc.cache_variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)

        # https://github.com/LLNL/sundials/blob/v7.1.1/cmake/SundialsBuildOptionsPre.cmake
        tc.variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.variables["SUNDIALS_INDEX_SIZE"] = self.options.index_size
        tc.variables["SUNDIALS_PRECISION"] = str(self.options.precision).upper()
        tc.variables["BUILD_ARKODE"] = self.options.build_arkode
        tc.variables["BUILD_CVODE"] = self.options.build_cvode
        tc.variables["BUILD_CVODES"] = self.options.build_cvodes
        tc.variables["BUILD_IDA"] = self.options.build_ida
        tc.variables["BUILD_IDAS"] = self.options.build_idas
        tc.variables["BUILD_KINSOL"] = self.options.build_kinsol

        # https://github.com/LLNL/sundials/blob/v7.1.1/cmake/SundialsTPLOptions.cmake
        tc.variables["ENABLE_MPI"] = self.options.with_mpi
        tc.variables["ENABLE_OPENMP"] = self.options.with_openmp
        tc.variables["ENABLE_CUDA"] = self.options.with_cuda
        tc.variables["ENABLE_HIP"] = False
        tc.variables["ENABLE_SYCL"] = False
        tc.variables["ENABLE_LAPACK"] = self.options.with_lapack
        tc.variables["LAPACK_WORKS"] = True
        tc.variables["ENABLE_GINKGO"] = self.options.get_safe("with_ginkgo", False)
        tc.variables["SUNDIALS_GINKGO_BACKENDS"] = ";".join(self._ginkgo_backends)
        tc.variables["GINKGO_WORKS"] = True
        tc.variables["ENABLE_MAGMA"] = False
        tc.variables["ENABLE_SUPERLUDIST"] = False
        tc.variables["ENABLE_SUPERLUMT"] = False
        tc.variables["ENABLE_KLU"] = self.options.with_klu
        tc.variables["KLU_WORKS"] = True
        tc.variables["ENABLE_HYPRE"] = False
        tc.variables["ENABLE_PETSC"] = False
        tc.variables["ENABLE_RAJA"] = False
        tc.variables["ENABLE_TRILINOS"] = False
        tc.variables["ENABLE_XBRAID"] = False
        tc.variables["ENABLE_ONEMKL"] = False
        tc.variables["ENABLE_CALIPER"] = False
        tc.variables["ENABLE_ADIAK"] = False
        tc.variables["ENABLE_KOKKOS"] = False

        # https://github.com/LLNL/sundials/blob/v7.1.1/cmake/SundialsBuildOptionsPost.cmake
        tc.variables["BUILD_SUNMATRIX_CUSPARSE"] = self.options.get_safe("with_cuda", False) and self.options.index_size == 32
        tc.variables["BUILD_SUNLINSOL_CUSOLVERSP"] = self.options.get_safe("with_cuda", False) and self.options.index_size == 32

        # Configure default LAPACK naming conventions for OpenBLAS.
        # Needed to avoid a Fortran compiler requirement to detect the correct name mangling scheme.
        # https://github.com/LLNL/sundials/blob/v7.1.1/cmake/SundialsSetupCompilers.cmake#L269-L360
        tc.variables["SUNDIALS_LAPACK_CASE"] = "lower"
        tc.variables["SUNDIALS_LAPACK_UNDERSCORES"] = "one"

        if self.options.with_cuda:
            tc.cache_variables["CMAKE_CUDA_ARCHITECTURES"] = str(self.settings.cuda.architectures).replace(",", ";")

        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("suitesparse-klu", "cmake_target_name", "SUNDIALS::KLU")
        deps.generate()

        if self.options.with_cuda:
            cuda_tc = self.cuda.CudaToolchain()
            cuda_tc.generate()

    def _patch_sources(self):
        if self.options.get_safe("with_ginkgo"):
            replace_in_file(self, os.path.join(self.source_folder, "cmake", "tpl", "SundialsGinkgo.cmake"),
                            "NO_DEFAULT_PATH", "")
        if self.options.with_mpi:
            replace_in_file(self, os.path.join(self.source_folder, "cmake", "tpl", "SundialsMPI.cmake"),
                            "find_package(MPI 2.0.0 REQUIRED)", "find_package(MPI REQUIRED)")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        if self.settings.os == "Windows" and self.options.shared:
            mkdir(self, os.path.join(self.package_folder, "bin"))
            for dll_path in glob.glob(os.path.join(self.package_folder, "lib", "*.dll")):
                shutil.move(dll_path, os.path.join(self.package_folder, "bin", os.path.basename(dll_path)))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        # https://github.com/LLNL/sundials/blob/v7.1.1/cmake/SUNDIALSConfig.cmake.in
        if Version(self.version) >= "5.8.0":
            self.cpp_info.set_property("cmake_file_name", "SUNDIALS")

        suffix = ""
        if Version(self.version) >= "7.0" and self.settings.os == "Windows":
            suffix = "_shared" if self.options.shared else "_static"

        core_lib = None
        if Version(self.version) >= "7.0":
            core_lib = "core"
        elif Version(self.version) >= "5.8.0":
            core_lib = "generic"

        def _add_lib(name, requires=None, system_libs=None, interface=False):
            if Version(self.version) >= "5.8.0":
                component = self.cpp_info.components[name]
                component.set_property("cmake_target_name", f"SUNDIALS::{name}")
                component.set_property("cmake_target_aliases", [f"SUNDIALS::{name}_{'shared' if self.options.shared else 'static'}"])
            else:
                # For backward compatibility with old recipe versions
                component = self.cpp_info.components[f"sundials_{name}"]
                requires = [f"sundials_{r}" if "::" not in r else r for r in requires or []]
            if not interface:
                component.libs = [f"sundials_{name}{suffix}"]
            component.requires = requires or []
            component.system_libs = system_libs or []
            if core_lib and name != core_lib:
                component.requires.append(core_lib)
            if self.settings.os in ["Linux", "FreeBSD"]:
                component.system_libs.append("m")

        if core_lib:
            _add_lib(core_lib)
            if self.options.with_mpi:
                self.cpp_info.components[core_lib].requires.append("openmpi::openmpi")

        if self.options.build_arkode:
            _add_lib("arkode")
        if self.options.build_cvode:
            _add_lib("cvode")
        if self.options.build_cvodes:
            _add_lib("cvodes")
        if self.options.build_ida:
            _add_lib("ida")
        if self.options.build_idas:
            _add_lib("idas")
        if self.options.build_kinsol:
            _add_lib("kinsol")

        _add_lib("nvecserial")
        if self.options.with_mpi:
            _add_lib("nvecmanyvector", requires=["openmpi::openmpi"])
        if self.options.with_openmp:
            _add_lib("nvecopenmp", requires=["openmp::openmp"])

        _add_lib("sunmatrixband")
        _add_lib("sunmatrixdense")
        _add_lib("sunmatrixsparse")
        if self.options.get_safe("with_ginkgo"):
            _add_lib("sunmatrixginkgo", interface=True, requires=["ginkgo::ginkgo"])

        _add_lib("sunlinsolband", requires=["sunmatrixband"])
        _add_lib("sunlinsoldense", requires=["sunmatrixdense"])
        _add_lib("sunlinsolpcg")
        _add_lib("sunlinsolspbcgs")
        _add_lib("sunlinsolspfgmr")
        _add_lib("sunlinsolspgmr")
        _add_lib("sunlinsolsptfqmr")
        if self.options.get_safe("with_ginkgo"):
            _add_lib("sunmatrixginkgo", interface=True, requires=["ginkgo::ginkgo"])
            _add_lib("sunlinsolginkgo", interface=True, requires=["ginkgo::ginkgo"])
        if self.options.with_klu:
            _add_lib("sunlinsolklu", requires=["sunmatrixsparse", "suitesparse-klu::suitesparse-klu"])
        if self.options.with_lapack:
            _add_lib("sunlinsollapackband", requires=["sunmatrixband", "openblas::openblas"])
            _add_lib("sunlinsollapackdense", requires=["sunmatrixdense", "openblas::openblas"])

        _add_lib("sunnonlinsolfixedpoint")
        _add_lib("sunnonlinsolnewton")

        if self.options.with_cuda:
            _add_lib("nveccuda", requires=["cudart::cudart_"])
            if self.options.index_size == 32:
                _add_lib("sunmatrixcusparse", requires=["cusparse::cusparse"])
                _add_lib("sunlinsolcusolversp", requires=["sunmatrixcusparse", "cusolver::cusolver_"])
