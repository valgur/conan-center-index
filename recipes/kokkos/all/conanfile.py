import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class KokkosConan(ConanFile):
    name = "kokkos"
    description = "Kokkos Core implements a programming model for writing performance portable applications targeting all major HPC platforms."
    license = "Apache-2.0 WITH LLVM-exception"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/kokkos/kokkos"
    topics = ("hpc", "parallel", "cuda", "hip", "sycl", "hpx", "openmp")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "backend": ["cuda", "hip", "openacc", "openmptarget", "sycl", None],
        "enable_openmp": [True, False],
        "enable_serial": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "backend": None,
        "enable_openmp": False,
        "enable_serial": True,
    }

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        # https://kokkos.org/kokkos-core-wiki/requirements.html
        return {
            "apple-clang": "8.0",
            "clang": "8.0.0",
            "gcc": "8.2.0",
            "msvc": "192.9",
            "Visual Studio": "16",
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
        # Kokkos uses an unreleased version of mdspan
        # self.requires("mdspan/0.7.0", transitive_headers=True, transitive_libs=True)
        if self.options.enable_openmp or self.options.backend == "openmptarget":
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)

        def lazy_lt_semver(v1, v2):
            return all(int(p1) < int(p2) for p1, p2 in zip(str(v1).split("."), str(v2).split(".")))

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and lazy_lt_semver(Version(self.settings.compiler.version), minimum_version):
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        # https://github.com/kokkos/kokkos/blob/develop/cmake/kokkos_enable_options.cmake
        tc.variables["Kokkos_ENABLE_MDSPAN_EXTERNAL"] = False
        tc.variables["KOKKOS_ENABLE_OPENACC"] = self.options.backend == "openacc"
        tc.variables["Kokkos_ENABLE_CUDA"] = self.options.backend == "cuda"
        tc.variables["Kokkos_ENABLE_HIP"] = self.options.backend == "hip"
        tc.variables["Kokkos_ENABLE_OPENMPTARGET"] = self.options.backend == "openmptarget"
        tc.variables["Kokkos_ENABLE_SYCL"] = self.options.backend == "sycl"
        tc.variables["KOKKOS_ENABLE_SERIAL"] = self.options.enable_serial
        tc.variables["Kokkos_ENABLE_OPENMP"] = self.options.enable_openmp
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        VirtualBuildEnv(self).generate()

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

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Kokkos")
        self.cpp_info.set_property("cmake_target_name", "Kokkos::kokkos")

        # TODO:
        # Kokkos::CUDA
        # Kokkos::LIBDL
        # Kokkos::kokkoscore
        # Kokkos::kokkoscontainers
        # Kokkos::kokkosalgorithms
        # Kokkos::kokkossimd
        # Kokkos::kokkos

        self.cpp_info.libs = [
            "kokkoscontainers",
            "kokkoscore",
            "kokkossimd",
        ]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["pthread", "dl"])

        # To export additional CMake variables, such as upper-case variables otherwise set by the project's *-config.cmake,
        # you can copy or save a .cmake file under <prefix>/lib/cmake/ with content like
        #     set(XYZ_VERSION ${${CMAKE_FIND_PACKAGE_NAME}_VERSION})
        #     set(XYZ_INCLUDE_DIRS ${${CMAKE_FIND_PACKAGE_NAME}_INCLUDE_DIRS})
        #     ...
        # and set the following fields:
        # self.cpp_info.builddirs.append(os.path.join("lib", "cmake"))
        # cmake_module = os.path.join("lib", "cmake", "conan-official-variables.cmake")
        # self.cpp_info.set_property("cmake_build_modules", [cmake_module])
