import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm, save, replace_in_file, rmdir
from conan.tools.gnu import PkgConfigDeps
from conan.tools.microsoft import is_msvc_static_runtime
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class Open3dConan(ConanFile):
    name = "open3d"
    description = "Open3D: A Modern Library for 3D Data Processing"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/isl-org/Open3D"
    topics = ("3d", "point-clouds", "visualization", "machine-learning", "rendering", "computer-graphics",
              "gpu", "cuda", "registration", "reconstruction", "odometry", "mesh-processing", "3d-perception")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_common_cuda_archs": [True, False],
        "gui": [True, False],
        "with_cuda": [True, False],
        "with_openmp": [True, False],
        "with_blas": [True, False],
        "with_minizip": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_common_cuda_archs": True,
        "gui": True,
        "with_cuda": False,
        "with_openmp": True,
        "with_blas": True,
        "with_minizip": True,
    }

    @property
    def _min_cppstd(self):
        # TODO: set to 17 if SYCL or CUDA is enabled
        return 14

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "7",
            "clang": "7",
            "apple-clang": "10",
            "Visual Studio": "15",
            "msvc": "191",
        }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.options["qhull"].shared = False
        self.options["qhull"].reentrant = True
        self.options["qhull"].cpp = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("assimp/5.4.1")
        self.requires("eigen/3.4.0")
        self.requires("embree3/3.13.5")
        self.requires("fmt/11.0.0")
        self.requires("glew/2.2.0")
        self.requires("glfw/3.4")
        self.requires("imgui/1.90.9")
        self.requires("jsoncpp/1.9.5")
        self.requires("libcurl/8.8.0")
        self.requires("libjpeg/9f")
        self.requires("liblzf/3.6")
        self.requires("libpng/[>=1.6 <2]")
        self.requires("msgpack-cxx/6.1.1")
        self.requires("nanoflann/1.5.2")
        self.requires("onetbb/2021.12.0")
        self.requires("openssl/[>=1.1 <4]")
        self.requires("qhull/cci.20231130")
        self.requires("stdgpu/cci.20230913")
        self.requires("tinygltf/2.9.0")
        self.requires("tinyobjloader/2.0.0-rc10")
        self.requires("zeromq/4.3.5")

        # self.requires("cutlass/2.10.0")
        # self.requires("filament/1.11.0")
        # self.requires("vtk/9.1.0")

        if self.options.with_openmp:
            self.requires("llvm-openmp/18.1.8")
        if self.options.with_blas:
            self.requires("openblas/0.3.27")
        if self.options.with_minizip:
            self.requires("minizip/1.2.13")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

        qhull = self.dependencies["qhull"].options
        if qhull.shared or not qhull.reentrant or not qhull.cpp:
            raise ConanInvalidConfiguration("qhull must be built with -o qhull/*:shared=False -o qhull/*:reentrant=True -o qhull/*:cpp=True")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20 <4]")
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/2.2.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["BUILD_UNIT_TESTS"] = False
        tc.cache_variables["BUILD_BENCHMARKS"] = False
        tc.cache_variables["BUILD_PYTHON_MODULE"] = False
        tc.cache_variables["BUILD_CUDA_MODULE"] = self.options.with_cuda
        tc.cache_variables["BUILD_COMMON_CUDA_ARCHS"] = self.options.build_common_cuda_archs
        tc.cache_variables["BUILD_ISPC_MODULE"] = False # self.options.build_ispc_module
        tc.cache_variables["BUILD_COMMON_ISPC_ISAS"] = False # self.options.build_common_ispc_isas
        tc.cache_variables["BUILD_GUI"] = self.options.gui
        tc.cache_variables["WITH_OPENMP"] = self.options.with_openmp
        tc.cache_variables["WITH_IPPICV"] = False # self.options.with_ippicv
        tc.cache_variables["ENABLE_HEADLESS_RENDERING"] = False # self.options.enable_headless_rendering
        tc.cache_variables["STATIC_WINDOWS_RUNTIME"] = is_msvc_static_runtime(self)
        tc.cache_variables["BUILD_SYCL_MODULE"] = False # self.options.build_sycl_module
        tc.cache_variables["GLIBCXX_USE_CXX11_ABI"] = self.settings.compiler.get_safe("libcxx") == "libstdc++11"
        tc.cache_variables["ENABLE_SYCL_UNIFIED_SHARED_MEMORY"] = False # self.options.enable_sycl_unified_shared_memory
        tc.cache_variables["BUILD_WEBRTC"] = False # self.options.build_webrtc
        tc.cache_variables["USE_BLAS"] = self.options.with_blas
        tc.cache_variables["USE_SYSTEM_BLAS"] = True
        tc.cache_variables["USE_SYSTEM_ASSIMP"] = True
        tc.cache_variables["USE_SYSTEM_CURL"] = True
        tc.cache_variables["USE_SYSTEM_CUTLASS"] = False
        tc.cache_variables["USE_SYSTEM_EIGEN3"] = True
        tc.cache_variables["USE_SYSTEM_EMBREE"] = True
        tc.cache_variables["USE_SYSTEM_FILAMENT"] = True
        tc.cache_variables["USE_SYSTEM_FMT"] = True
        tc.cache_variables["USE_SYSTEM_GLEW"] = True
        tc.cache_variables["USE_SYSTEM_GLFW"] = True
        tc.cache_variables["USE_SYSTEM_GOOGLETEST"] = True
        tc.cache_variables["USE_SYSTEM_IMGUI"] = True
        tc.cache_variables["USE_SYSTEM_JPEG"] = True
        tc.cache_variables["USE_SYSTEM_JSONCPP"] = True
        tc.cache_variables["USE_SYSTEM_LIBLZF"] = True
        tc.cache_variables["USE_SYSTEM_MSGPACK"] = True
        tc.cache_variables["USE_SYSTEM_NANOFLANN"] = True
        tc.cache_variables["USE_SYSTEM_OPENSSL"] = True
        tc.cache_variables["USE_SYSTEM_PNG"] = True
        tc.cache_variables["USE_SYSTEM_QHULLCPP"] = True
        tc.cache_variables["USE_SYSTEM_STDGPU"] = True
        tc.cache_variables["USE_SYSTEM_TBB"] = True
        tc.cache_variables["USE_SYSTEM_TINYGLTF"] = True
        tc.cache_variables["USE_SYSTEM_TINYOBJLOADER"] = True
        tc.cache_variables["USE_SYSTEM_VTK"] = False
        tc.cache_variables["USE_SYSTEM_ZEROMQ"] = True
        tc.cache_variables["BUILD_VTK_FROM_SOURCE"] = True
        tc.cache_variables["BUILD_FILAMENT_FROM_SOURCE"] = True
        tc.cache_variables["PREFER_OSX_HOMEBREW"] = False
        tc.cache_variables["WITH_MINIZIP"] = self.options.with_minizip
        tc.cache_variables["BUILD_LIBREALSENSE"] = False
        tc.cache_variables["USE_SYSTEM_LIBREALSENSE"] = False # self.options.with_librealsense
        tc.cache_variables["BUILD_AZURE_KINECT"] = False # self.options.build_azure_kinect
        tc.cache_variables["BUILD_TENSORFLOW_OPS"] = False
        tc.cache_variables["BUILD_PYTORCH_OPS"] = False
        tc.cache_variables["BUNDLE_OPEN3D_ML"] = False
        tc.cache_variables["DEVELOPER_BUILD"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("openblas", "cmake_file_name", "BLAS")
        deps.set_property("openblas", "cmake_find_mode", "module")
        deps.set_property("imgui", "cmake_file_name", "ImGui")
        deps.set_property("imgui", "cmake_target_name", "ImGui::ImGui")
        deps.set_property("msgpack-cxx", "cmake_file_name", "msgpack-cxx")
        deps.set_property("msgpack-cxx", "cmake_target_name", "msgpack-cxx")
        deps.set_property("qhull::libqhull_r", "cmake_target_name", "Qhull::qhull_r")
        deps.generate()

        # These are provided by OpenBLAS, but the Find modules are not created by the Conan recipe
        save(self, os.path.join(self.generators_folder, "FindLAPACK.cmake"), "set(LAPACK_FOUND TRUE)\n")
        save(self, os.path.join(self.generators_folder, "FindLAPACKE.cmake"), "set(LAPACKE_FOUND TRUE)\n")

        deps = PkgConfigDeps(self)
        deps.generate()

        VirtualBuildEnv(self).generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        # Disable -Werror
        save(self, os.path.join(self.source_folder, "cmake", "Open3DShowAndAbortOnWarning.cmake"),
             "function(open3d_show_and_abort_on_warning target)\nendfunction()\n")
        # Keep only allowed third-party dependencies.
        # The project defaults to using vendored versions if the dependencies otherwise,
        # if the dependencies are not found for any reason.
        allowed_3rdparty = ["filament", "vtk", "cutlass", "parallelstl", "uvatlas", "possionrecon"]
        for dir in Path(self.source_folder, "3rdparty").iterdir():
            if dir.is_dir() and dir.name not in allowed_3rdparty:
                rmdir(self, dir)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def open3d(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        # rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        # rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "open3d")
        self.cpp_info.set_property("cmake_target_name", "open3d::open3d")
        self.cpp_info.set_property("pkg_config_name", "open3d")

        self.cpp_info.libs = ["package_lib"]

        # If they are needed on Linux, m, pthread and dl are usually needed on FreeBSD too
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
            self.cpp_info.system_libs.append("pthread")
            self.cpp_info.system_libs.append("dl")

        # To export additional CMake variables, such as upper-case variables otherwise set by the project's *-config.cmake,
        # you can copy or save a .cmake file under <prefix>/lib/cmake/ with content like
        #     set(XYZ_VERSION ${${CMAKE_FIND_PACKAGE_NAME}_VERSION})
        #     set(XYZ_INCLUDE_DIRS ${${CMAKE_FIND_PACKAGE_NAME}_INCLUDE_DIRS})
        #     ...
        # and set the following fields:
        self.cpp_info.builddirs.append(os.path.join("lib", "cmake"))
        cmake_module = os.path.join("lib", "cmake", "conan-official-variables.cmake")
        self.cpp_info.set_property("cmake_build_modules", [cmake_module])
        self.cpp_info.build_modules["cmake_find_package"] = [cmake_module]
        self.cpp_info.build_modules["cmake_find_package_multi"] = [cmake_module]

