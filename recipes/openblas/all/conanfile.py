import io
import os
import shutil
import tempfile

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, copy, get, load, rmdir, collect_libs, mkdir
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=1.55.0"


class OpenblasConan(ConanFile):
    name = "openblas"
    description = "An optimized BLAS library based on GotoBLAS2 1.13 BSD version"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.openblas.net"
    topics = ("blas", "lapack")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_thread": [True, False],
        "use_openmp": [True, False],
        "dynamic_arch": [True, False],
        "with_avx512": [True, False],
        "build_lapack": [True, False],
        "use_fortran": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "use_thread": False,
        "use_openmp": True,
        "dynamic_arch": False,
        "with_avx512": False,
        "build_lapack": True,
        "use_fortran": True,
    }
    short_paths = True

    @property
    def _fortran_compiler(self):
        return self.conf.get("tools.build:compiler_executables", default={}).get("fortran")

    def _get_fortran_compiler_id(self):
        # Capture Fortran compiler ID using CMake
        run_cmd = f"cmake {self.recipe_folder} --log-level=NOTICE -DCMAKE_Fortran_COMPILER={self._fortran_compiler}"
        with tempfile.TemporaryDirectory() as tmpdir:
            self.run(run_cmd, io.StringIO(), cwd=tmpdir)
            compiler_id = load(self, os.path.join(tmpdir, "FORTRAN_COMPILER")).strip()
        return compiler_id

    def _fortran_runtime(self, fortran_id):
        if fortran_id.startswith("GNU"):
            if self.settings.compiler == "gcc":
                # Compiler vs. gfortran runtime ver.: 5,6: 3, 7: 4, >=8: 5
                if Version(self.settings.compiler.version) >= "5":
                    return "gfortran"
            if self.settings.compiler == "clang":
                if Version(self.settings.compiler.version) >= "9":
                    return "gfortran"  # Runtime version gfortran5
        self.output.warning(
            f"Unable to select runtime for Fortran {fortran_id} "
            f"and C++ {self.settings.compiler} {self.settings.compiler.version}")
        return None

    @property
    def _cmake_generator(self):
        conf_generator = self.conf.get("tools.cmake.cmaketoolchain:generator")
        if self.settings.os == "Windows" and self.options.build_lapack:
            if not conf_generator or "Visual Studio" in conf_generator:
                return "Ninja"
        return None

    def export(self):
        mkdir(self, os.path.join(self.export_folder, "conan_fortran"))
        shutil.copy(os.path.join(self.recipe_folder, "fortran_helper.cmake"),
                    os.path.join(self.export_folder, "conan_fortran", "CMakeLists.txt"))

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

    def package_id(self):
        if self.info.options.build_lapack:
            if self.info.options.use_fortran and self._fortran_compiler:
                self.info.options.use_fortran = self._get_fortran_compiler_id()
        else:
            del self.info.options.use_fortran

    def requirements(self):
        if self.options.build_lapack and self.options.use_fortran and not self._fortran_compiler:
            # Propagate libgfortran dependency in addition to the tool_requires()
            self.requires("gcc/13.2.0", headers=False, libs=True)
        if self.options.use_openmp and self.settings.compiler in ["clang", "apple-clang"]:
            self.requires("llvm-openmp/17.0.4")

    def validate(self):
        if cross_building(self, skip_x64_x86=True):
            raise ConanInvalidConfiguration("Cross-building not implemented")

        if self.options.use_thread and self.options.use_openmp:
            raise ConanInvalidConfiguration("Both 'use_thread=True' and 'use_openmp=True' are not allowed")

        if self.settings.os == "Windows" and self.options.build_lapack and self.options.use_openmp:
            # In OpenBLAS cmake/system.cmake: Disable -fopenmp for LAPACK Fortran codes on Windows
            self.output.warning("OpenMP is disabled on LAPACK targets on Windows")

        if self.options.build_lapack and not self.options.use_fortran and Version(self.version) < "0.3.21":
            raise ConanInvalidConfiguration("Building LAPACK requires a Fortran compiler")

    def build_requirements(self):
        if self.options.build_lapack and self.options.use_fortran and not self._fortran_compiler:
            # Use gfortran from GCC
            self.tool_requires("gcc/<host_version>")
        if self._cmake_generator == "Ninja":
            self.tool_requires("ninja/1.11.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        generator = self._cmake_generator
        if generator == "Ninja":
            self.output.warning(
                "The Visual Studio generator is not compatible with OpenBLAS "
                "when building LAPACK. Overriding generator to 'Ninja'")
        tc = CMakeToolchain(self, generator=generator)

        tc.variables["BUILD_WITHOUT_LAPACK"] = not self.options.build_lapack
        tc.variables["NOFORTRAN"] = not self.options.build_lapack or not self.options.use_fortran
        tc.variables["C_LAPACK"] = self.options.build_lapack and not self.options.use_fortran

        tc.variables["DYNAMIC_ARCH"] = self.options.dynamic_arch
        tc.variables["USE_THREAD"] = self.options.use_thread
        tc.variables["USE_OPENMP"] = self.options.use_openmp

        # Required for safe concurrent calls to OpenBLAS routines
        tc.variables["USE_LOCKING"] = not self.options.use_thread

        # don't, may lie to consumer, /MD or /MT is managed by conan
        tc.variables["MSVC_STATIC_CRT"] = False

        tc.variables["NO_AVX512"] = not self.options.with_avx512

        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        # CMake config file:
        # - OpenBLAS always has one and only one of these components: openmp, pthread or serial.
        # - Whether this component is requested or not, official CMake imported target is always OpenBLAS::OpenBLAS
        self.cpp_info.set_property("cmake_file_name", "OpenBLAS")
        self.cpp_info.set_property("cmake_target_name", "OpenBLAS::OpenBLAS")
        self.cpp_info.set_property("pkg_config_name", "openblas")

        component_name = "serial"
        if self.options.use_thread:
            component_name = "pthread"
        elif self.options.use_openmp:
            component_name = "openmp"
        component = self.cpp_info.components[component_name]

        component.set_property("pkg_config_name", "openblas")

        # Target cannot be named pthread -> causes failed linking
        component.set_property("cmake_target_name", "OpenBLAS::" + component_name)
        component.includedirs.append(os.path.join("include", "openblas"))
        component.libs = collect_libs(self)
        if self.settings.os in ["Linux", "FreeBSD"]:
            component.system_libs.append("m")
            if self.options.use_thread:
                component.system_libs.append("pthread")

        if self.options.use_openmp:
            if is_msvc(self):
                openmp_flags = ["-openmp"]
            elif self.settings.compiler in ("gcc", "clang"):
                openmp_flags = ["-fopenmp"]
            elif self.settings.compiler == "apple-clang":
                openmp_flags = ["-Xpreprocessor", "-fopenmp"]
            else:
                openmp_flags = []
            component.exelinkflags = openmp_flags
            component.sharedlinkflags = openmp_flags
            if self.settings.compiler in ["clang", "apple-clang"]:
                component.requires.append("llvm-openmp::llvm-openmp")

        if self.options.build_lapack and self.options.use_fortran:
            if self._fortran_compiler:
                fortran_id = self._get_fortran_compiler_id()
                fortran_rt = self._fortran_runtime(fortran_id)
                if fortran_rt:
                    component.system_libs += ["dl", fortran_rt]
            else:
                component.requires.append("gcc::gfortran")

        # TODO: Remove env_info in conan v2
        self.output.info(f"Setting OpenBLAS_HOME environment variable: {self.package_folder}")
        self.env_info.OpenBLAS_HOME = self.package_folder
        self.runenv_info.define_path("OpenBLAS_HOME", self.package_folder)

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.names["cmake_find_package"] = "OpenBLAS"
        self.cpp_info.names["cmake_find_package_multi"] = "OpenBLAS"
        component.names["cmake_find_package"] = component_name
        component.names["cmake_find_package_multi"] = component_name
