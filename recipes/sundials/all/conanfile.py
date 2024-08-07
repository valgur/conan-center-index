from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, mkdir, rmdir
from conan.tools.scm import Version
import glob
import os
import shutil

required_conan_version = ">=1.53.0"


class SundialsConan(ConanFile):
    name = "sundials"
    license = "BSD-3-Clause"
    description = ("SUNDIALS is a family of software packages implemented"
                   " with the goal of providing robust time integrators "
                   "and nonlinear solvers that can easily be incorporated"
                   "into existing simulation codes.")
    topics = ("integrators", "ode", "non-linear solvers")
    homepage = "https://github.com/LLNL/sundials"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_arkode": [True, False],
        "build_cvode": [True, False],
        "build_cvodes": [True, False],
        "build_ida": [True, False],
        "build_idas": [True, False],
        "build_kinsol": [True, False],
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
    }

    short_paths = True

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # https://github.com/LLNL/sundials/blob/v7.1.1/cmake/SUNDIALSConfig.cmake.in
        # TODO: add support for optional dependencies:
        # - openmp #22360
        # - openmpi #18980
        # - suitesparse-klu #23547
        # - cuda
        # - adiak
        # - caliper
        # - ginkgo
        # - kokkos
        # - mkl
        # - raja
        pass

    def build_requirements(self):
        if Version(self.version) >= "7.0":
            self.tool_requires("cmake/[>=3.18 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_STATIC_LIBS"] = not self.options.shared
        tc.variables["BUILD_ARKODE"] = self.options.build_arkode
        tc.variables["BUILD_CVODE"] = self.options.build_cvode
        tc.variables["BUILD_CVODES"] = self.options.build_cvodes
        tc.variables["BUILD_IDA"] = self.options.build_ida
        tc.variables["BUILD_IDAS"] = self.options.build_idas
        tc.variables["BUILD_KINSOL"] = self.options.build_kinsol
        tc.variables["EXAMPLES_ENABLE_C"] = False
        tc.variables["EXAMPLES_INSTALL"] = False
        if Version(self.version) <= "5.4.0":
            tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()
        VirtualBuildEnv(self).generate()

    def build(self):
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
        suffix = ""
        if Version(self.version) >= "7.0" and self.settings.os == "Windows":
            suffix = "_shared" if self.options.shared else "_static"
        self.cpp_info.components["sundials_nvecmanyvector"].libs = ["sundials_nvecmanyvector" + suffix]
        self.cpp_info.components["sundials_nvecserial"].libs = ["sundials_nvecserial" + suffix]
        self.cpp_info.components["sundials_sunlinsolband"].libs = ["sundials_sunlinsolband" + suffix]
        self.cpp_info.components["sundials_sunlinsolband"].requires = ["sundials_sunmatrixband" + suffix]
        self.cpp_info.components["sundials_sunlinsoldense"].libs = ["sundials_sunlinsoldense" + suffix]
        self.cpp_info.components["sundials_sunlinsoldense"].requires = ["sundials_sunmatrixdense" + suffix]
        self.cpp_info.components["sundials_sunlinsolpcg"].libs = ["sundials_sunlinsolpcg" + suffix]
        self.cpp_info.components["sundials_sunlinsolspbcgs"].libs = ["sundials_sunlinsolspbcgs" + suffix]
        self.cpp_info.components["sundials_sunlinsolspfgmr"].libs = ["sundials_sunlinsolspfgmr" + suffix]
        self.cpp_info.components["sundials_sunlinsolspgmr"].libs = ["sundials_sunlinsolspgmr" + suffix]
        self.cpp_info.components["sundials_sunlinsolsptfqmr"].libs = ["sundials_sunlinsolsptfqmr" + suffix]
        self.cpp_info.components["sundials_sunmatrixband"].libs = ["sundials_sunmatrixband" + suffix]
        self.cpp_info.components["sundials_sunmatrixdense"].libs = ["sundials_sunmatrixdense" + suffix]
        self.cpp_info.components["sundials_sunmatrixsparse"].libs = ["sundials_sunmatrixsparse" + suffix]
        self.cpp_info.components["sundials_sunnonlinsolfixedpoint"].libs = ["sundials_sunnonlinsolfixedpoint" + suffix]
        self.cpp_info.components["sundials_sunnonlinsolnewton"].libs = ["sundials_sunnonlinsolnewton" + suffix]
        if self.options.build_arkode:
            self.cpp_info.components["sundials_arkode"].libs = ["sundials_arkode" + suffix]
        if self.options.build_cvode:
            self.cpp_info.components["sundials_cvode"].libs = ["sundials_cvode" + suffix]
        if self.options.build_cvodes:
            self.cpp_info.components["sundials_cvodes"].libs = ["sundials_cvodes" + suffix]
        if self.options.build_ida:
            self.cpp_info.components["sundials_ida"].libs = ["sundials_ida" + suffix]
        if self.options.build_idas:
            self.cpp_info.components["sundials_idas"].libs = ["sundials_idas" + suffix]
        if self.options.build_kinsol:
            self.cpp_info.components["sundials_kinsol"].libs = ["sundials_kinsol" + suffix]

        core_lib = None
        if Version(self.version) >= "7.0":
            core_lib = "sundials_core"
        elif Version(self.version) >= "5.8.0":
            core_lib = "sundials_generic"

        if core_lib:
            for name, component in self.cpp_info.components.items():
                component.requires.append(core_lib)
            self.cpp_info.components[core_lib].libs = [core_lib + suffix]

        if self.settings.os in ["Linux", "FreeBSD"]:
            for _, component in self.cpp_info.components.items():
                component.system_libs.append("m")
