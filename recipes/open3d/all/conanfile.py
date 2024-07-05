import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class Open3dConan(ConanFile):
    name = "open3d"
    description = "Open3D: A Modern Library for 3D Data Processing"
    license = "MIT"
    homepage = "https://github.com/isl-org/Open3D"
    topics = ("3d", "point-clouds", "visualization", "machine-learning", "rendering", "computer-graphics",
              "gpu", "cuda", "registration", "reconstruction", "odometry", "mesh-processing", "3d-perception")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
        "enable_headless_rendering": [True, False],
        "with_gui": [True, False],
        "with_webrtc": [True, False],
        "with_cuda": [True, False],
        "with_ispc": [True, False],
        "with_sycl": [True, False],
        "with_openmp": [True, False],
        "with_ipp": [True, False],
        "with_blas": [True, False],
        "with_assimp": [True, False],
        "with_curl": [True, False],
        "with_eigen3": [True, False],
        "with_embree": [True, False],
        "with_filament": [True, False],
        "with_fmt": [True, False],
        "with_glew": [True, False],
        "with_glfw": [True, False],
        "with_imgui": [True, False],
        "with_jpeg": [True, False],
        "with_jsoncpp": [True, False],
        "with_liblzf": [True, False],
        "with_minizip": [True, False],
        "with_msgpack": [True, False],
        "with_nanoflann": [True, False],
        "with_openssl": [True, False],
        "with_png": [True, False],
        "with_pybind11": [True, False],
        "with_qhullcpp": [True, False],
        "with_stdgpu": [True, False],
        "with_tbb": [True, False],
        "with_tinygltf": [True, False],
        "with_tinyobjloader": [True, False],
        "with_vtk": [True, False],
        "with_zeromq": [True, False],
        "with_librealsense": [True, False],
        "with_azure_kinect": [True, False],
    }

    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": False,
        "enable_headless_rendering": False,
        "with_gui": True,
        "with_webrtc": True,
        "with_cuda": True,
        "with_ispc": True,
        "with_sycl": True,
        "with_openmp": True,
        "with_ipp": True,
        "with_blas": True,
        "with_assimp": True,
        "with_curl": True,
        "with_eigen3": True,
        "with_embree": True,
        "with_filament": True,
        "with_fmt": True,
        "with_glew": True,
        "with_glfw": True,
        "with_imgui": True,
        "with_jpeg": True,
        "with_jsoncpp": True,
        "with_liblzf": True,
        "with_minizip": True,
        "with_msgpack": True,
        "with_nanoflann": True,
        "with_openssl": True,
        "with_png": True,
        "with_pybind11": True,
        "with_qhullcpp": True,
        "with_stdgpu": True,
        "with_tbb": True,
        "with_tinygltf": True,
        "with_tinyobjloader": True,
        "with_vtk": True,
        "with_zeromq": True,
        "with_librealsense": True,
        "with_azure_kinect": True,
    }

    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Core dependencies based on find_dependencies.cmake
        if self.options.with_eigen3:
            self.requires("eigen/[^3.4]", transitive_headers=True)
        if self.options.with_fmt:
            self.requires("fmt/[^10.0]")
        if self.options.with_assimp:
            self.requires("assimp/[^5.3]")
        if self.options.with_tbb:
            self.requires("onetbb/[^2021.10]")
        if self.options.with_jsoncpp:
            self.requires("jsoncpp/[^1.9]")
        if self.options.with_png:
            self.requires("libpng/[^1.6]")
        if self.options.with_jpeg:
            self.requires("libjpeg-meta/latest")
        if self.options.with_curl:
            self.requires("libcurl/[^8.0]")
        if self.options.with_openssl:
            self.requires("openssl/[^3.0]")
        if self.options.with_zeromq:
            self.requires("zeromq/[^4.3]")
        if self.options.with_msgpack:
            self.requires("msgpack-cxx/[^6.0]")
        if self.options.with_nanoflann:
            self.requires("nanoflann/[^1.5]", transitive_headers=True)
        if self.options.with_qhullcpp:
            self.requires("qhull/[^8.0]")
        if self.options.with_liblzf:
            self.requires("liblzf/[^3.6]")
        if self.options.with_tinygltf:
            self.requires("tinygltf/[^2.8]", transitive_headers=True)
        if self.options.with_tinyobjloader:
            self.requires("tinyobjloader/[^2.0, include_prerelease]", transitive_headers=True)

        # GUI dependencies
        if self.options.with_gui:
            if self.options.with_glfw:
                self.requires("glfw/[^3.3]")
            if self.options.with_glew:
                self.requires("glew/[^2.2]")
            if self.options.with_imgui:
                self.requires("imgui/[^1.89]", transitive_headers=True)
            if self.options.with_filament:
                self.requires("filament/[^1.51]")

        # Optional dependencies
        if self.options.with_vtk:
            self.requires("vtk/[^9.2]")
        if self.options.with_embree:
            self.requires("embree3/[^4.3]")
        if self.options.with_blas:
            self.requires("openblas/[^0.3]")
        if self.options.with_ipp:
            self.requires("intel-ipp/[^2021.9]")
        if self.options.with_librealsense:
            self.requires("librealsense2/[^2.54]")

        # CUDA dependencies
        if self.options.with_cuda:
            self._utils.cuda_requires(self, "cudart", transitive_headers=True, transitive_libs=True)
            self._utils.cuda_requires(self, "cublas", transitive_libs=True)
            self._utils.cuda_requires(self, "cusolver", transitive_libs=True)
            self._utils.cuda_requires(self, "cusparse", transitive_libs=True)
            self._utils.cuda_requires(self, "curand", transitive_libs=True)
            if self.options.with_stdgpu:
                self.requires("stdgpu/[^1.3]")

    def validate(self):
        check_min_cppstd(self, 17)

        # Platform constraints from CMakeLists.txt
        if self.settings.arch == "armv8" and self.options.with_ispc:
            raise ConanInvalidConfiguration("ISPC module is not supported on ARM")

        if self.settings.arch == "armv8" and not self.options.with_blas:
            raise ConanInvalidConfiguration("ARM CPU requires BLAS support")

        if self.settings.os == "Macos" and self.options.enable_headless_rendering:
            raise ConanInvalidConfiguration("Headless rendering is not supported on macOS")

        if self.options.enable_headless_rendering and self.options.with_gui:
            raise ConanInvalidConfiguration("Headless rendering disables GUI")

        if self.options.with_webrtc and not self.options.with_gui:
            raise ConanInvalidConfiguration("WebRTC requires GUI support")

        if self.options.with_sycl and self.options.with_cuda:
            raise ConanInvalidConfiguration("SYCL and CUDA cannot be enabled simultaneously")

        if self.options.with_sycl and not self.options.glibcxx_use_cxx11_abi:
            raise ConanInvalidConfiguration("SYCL requires GLIBCXX_USE_CXX11_ABI=ON")

        # CUDA version requirements
        if self.options.with_cuda:
            if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "7":
                raise ConanInvalidConfiguration("CUDA requires GCC 7 or newer")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.24]")
        if self.options.with_cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["ENABLE_HEADLESS_RENDERING"] = self.options.enable_headless_rendering
        tc.cache_variables["ENABLE_CACHED_CUDA_MANAGER"] = self.options.enable_cached_cuda_manager
        tc.cache_variables["STATIC_WINDOWS_RUNTIME"] = is_msvc_static_runtime(self)
        tc.cache_variables["GLIBCXX_USE_CXX11_ABI"] = self.settings.compiler.get_safe("libcxx") == "libstdc++11"
        tc.cache_variables["ENABLE_SYCL_UNIFIED_SHARED_MEMORY"] = False # self.options.enable_sycl_unified_shared_memory
        tc.cache_variables["BUILD_WEBRTC"] = False # self.options.build_webrtc
        tc.cache_variables["USE_BLAS"] = self.options.with_blas
        tc.cache_variables["BUILD_GUI"] = self.options.with_gui
        tc.cache_variables["BUILD_WEBRTC"] = self.options.with_webrtc
        tc.cache_variables["BUILD_CUDA_MODULE"] = self.options.with_cuda
        tc.cache_variables["BUILD_ISPC_MODULE"] = self.options.with_ispc
        tc.cache_variables["BUILD_SYCL_MODULE"] = self.options.with_sycl
        tc.cache_variables["WITH_OPENMP"] = self.options.with_openmp
        tc.cache_variables["WITH_IPP"] = self.options.with_ipp
        tc.cache_variables["USE_BLAS"] = self.options.with_blas
        tc.cache_variables["WITH_MINIZIP"] = self.options.with_minizip
        tc.cache_variables["PREFER_OSX_HOMEBREW"] = False
        tc.cache_variables["BUILD_VTK_FROM_SOURCE"] = False
        tc.cache_variables["BUILD_FILAMENT_FROM_SOURCE"] = True
        tc.cache_variables["BUILD_LIBREALSENSE"] = False
        tc.cache_variables["BUILD_AZURE_KINECT"] = False # self.options.build_azure_kinect
        tc.cache_variables["BUILD_TENSORFLOW_OPS"] = False
        tc.cache_variables["BUILD_PYTORCH_OPS"] = False
        tc.cache_variables["BUNDLE_OPEN3D_ML"] = False
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["BUILD_UNIT_TESTS"] = False
        tc.cache_variables["BUILD_BENCHMARKS"] = False
        tc.cache_variables["BUILD_PYTHON_MODULE"] = False
        tc.cache_variables["DEVELOPER_BUILD"] = False

        tc.cache_variables["USE_SYSTEM_BLAS"] = True
        tc.cache_variables["USE_SYSTEM_ASSIMP"] = True
        tc.cache_variables["USE_SYSTEM_CURL"] = True
        tc.cache_variables["USE_SYSTEM_CUTLASS"] = True
        tc.cache_variables["USE_SYSTEM_EIGEN3"] = True
        tc.cache_variables["USE_SYSTEM_EMBREE"] = True
        tc.cache_variables["USE_SYSTEM_FILAMENT"] = True
        tc.cache_variables["USE_SYSTEM_FMT"] = True
        tc.cache_variables["USE_SYSTEM_GLEW"] = True
        tc.cache_variables["USE_SYSTEM_GLFW"] = True
        tc.cache_variables["USE_SYSTEM_IMGUI"] = True
        tc.cache_variables["USE_SYSTEM_JPEG"] = True
        tc.cache_variables["USE_SYSTEM_JSONCPP"] = True
        tc.cache_variables["USE_SYSTEM_LIBLZF"] = True
        tc.cache_variables["USE_SYSTEM_MSGPACK"] = True
        tc.cache_variables["USE_SYSTEM_NANOFLANN"] = True
        tc.cache_variables["USE_SYSTEM_OPENSSL"] = True
        tc.cache_variables["USE_SYSTEM_PNG"] = True
        tc.cache_variables["USE_SYSTEM_PYBIND11"] = True
        tc.cache_variables["USE_SYSTEM_QHULLCPP"] = True
        tc.cache_variables["USE_SYSTEM_STDGPU"] = True
        tc.cache_variables["USE_SYSTEM_TBB"] = True
        tc.cache_variables["USE_SYSTEM_TINYGLTF"] = True
        tc.cache_variables["USE_SYSTEM_TINYOBJLOADER"] = True
        tc.cache_variables["USE_SYSTEM_VTK"] = True
        tc.cache_variables["USE_SYSTEM_ZEROMQ"] = True
        tc.cache_variables["USE_SYSTEM_LIBREALSENSE"] = True
        tc.generate()

        deps = CMakeDeps(self)
        # Override CMake target names for dependencies that don't match Conan names
        deps.set_property("eigen", "cmake_target_name", "Eigen3::Eigen")
        deps.set_property("onetbb", "cmake_target_name", "TBB::tbb")
        deps.set_property("libpng", "cmake_target_name", "PNG::PNG")
        deps.set_property("libjpeg", "cmake_target_name", "JPEG::JPEG")
        deps.set_property("libcurl", "cmake_target_name", "CURL::libcurl")
        deps.set_property("zeromq", "cmake_target_name", "libzmq")
        deps.set_property("glfw", "cmake_target_name", "glfw")
        deps.set_property("glew", "cmake_target_name", "GLEW::GLEW")
        deps.generate()

        if self.options.with_cuda:
            nvcc_tc = self._utils.NvccToolchain(self)
            nvcc_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        # rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        # rmdir(self, os.path.join(self.package_folder, "share"))
        # rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        # Main Open3D library
        self.cpp_info.set_property("cmake_file_name", "Open3D")

        # Core library component
        self.cpp_info.components["open3d"].set_property("cmake_target_name", "Open3D::Open3D")
        self.cpp_info.components["open3d"].libs = ["Open3D"]

        # System libraries based on platform
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["open3d"].system_libs = ["m", "pthread", "dl", "stdc++fs"]
        elif self.settings.os == "Windows":
            self.cpp_info.components["open3d"].system_libs = ["ws2_32", "winmm", "gdi32", "opengl32"]
        elif self.settings.os == "Macos":
            self.cpp_info.components["open3d"].frameworks = ["OpenGL", "Cocoa", "IOKit", "CoreVideo"]

        # Core dependencies
        requires = []
        if self.options.with_eigen3:
            requires.append("eigen::eigen")
        if self.options.with_fmt:
            requires.append("fmt::fmt")
        if self.options.with_assimp:
            requires.append("assimp::assimp")
        if self.options.with_tbb:
            requires.append("onetbb::onetbb")
        if self.options.with_jsoncpp:
            requires.append("jsoncpp::jsoncpp")
        if self.options.with_png:
            requires.append("libpng::libpng")
        if self.options.with_jpeg:
            requires.append("libjpeg::libjpeg")
        if self.options.with_curl:
            requires.append("libcurl::libcurl")
        if self.options.with_openssl:
            requires.append("openssl::openssl")
        if self.options.with_zeromq:
            requires.append("zeromq::zeromq")
        if self.options.with_msgpack:
            requires.append("msgpack-cxx::msgpack-cxx")
        if self.options.with_nanoflann:
            requires.append("nanoflann::nanoflann")
        if self.options.with_qhullcpp:
            requires.append("qhull::qhull")
        if self.options.with_liblzf:
            requires.append("liblzf::liblzf")
        if self.options.with_tinygltf:
            requires.append("tinygltf::tinygltf")
        if self.options.with_tinyobjloader:
            requires.append("tinyobjloader::tinyobjloader")

        # GUI dependencies
        if self.options.with_gui:
            if self.options.with_glfw:
                requires.append("glfw::glfw")
            if self.options.with_glew:
                requires.append("glew::glew")
            if self.options.with_imgui:
                requires.append("imgui::imgui")
            if self.options.with_filament:
                requires.append("filament::filament")

        # Optional dependencies
        if self.options.with_vtk:
            requires.append("vtk::vtk")
        if self.options.with_embree:
            requires.append("embree3::embree3")
        if self.options.with_blas:
            requires.append("openblas::openblas")
        if self.options.with_ipp:
            requires.append("intel-ipp::intel-ipp")
        if self.options.with_librealsense:
            requires.append("librealsense2::librealsense2")

        # CUDA dependencies
        if self.options.with_cuda:
            requires.extend([
                "cudart::cudart_",
                "cublas::cublas_",
                "cusolver::cusolver_",
                "cusparse::cusparse",
                "curand::curand",
            ])
            if self.options.with_stdgpu:
                requires.append("stdgpu::stdgpu")

        self.cpp_info.components["open3d"].requires = requires

        # Compile definitions based on build options
        if self.options.with_cuda:
            self.cpp_info.components["open3d"].defines.append("BUILD_CUDA_MODULE")
            if self.options.enable_cached_cuda_manager:
                self.cpp_info.components["open3d"].defines.append("ENABLE_CACHED_CUDA_MANAGER")
        if self.options.with_ispc:
            self.cpp_info.components["open3d"].defines.append("BUILD_ISPC_MODULE")
        if self.options.with_sycl:
            self.cpp_info.components["open3d"].defines.append("BUILD_SYCL_MODULE")
            if self.options.enable_sycl_unified_shared_memory:
                self.cpp_info.components["open3d"].defines.append("ENABLE_SYCL_UNIFIED_SHARED_MEMORY")
        if self.options.with_gui:
            self.cpp_info.components["open3d"].defines.append("BUILD_GUI")
        if self.options.enable_headless_rendering:
            self.cpp_info.components["open3d"].defines.append("HEADLESS_RENDERING")
        if self.options.with_azure_kinect:
            self.cpp_info.components["open3d"].defines.append("BUILD_AZURE_KINECT")
        if self.options.with_librealsense:
            self.cpp_info.components["open3d"].defines.append("BUILD_LIBREALSENSE")
        if self.options.with_webrtc:
            self.cpp_info.components["open3d"].defines.append("BUILD_WEBRTC")
        if self.options.with_blas:
            self.cpp_info.components["open3d"].defines.append("USE_BLAS")
        if self.options.with_ipp:
            self.cpp_info.components["open3d"].defines.append("WITH_IPP")
        if self.options.glibcxx_use_cxx11_abi:
            self.cpp_info.components["open3d"].defines.append("_GLIBCXX_USE_CXX11_ABI=1")
        else:
            self.cpp_info.components["open3d"].defines.append("_GLIBCXX_USE_CXX11_ABI=0")

        if not self.options.shared:
            self.cpp_info.components["open3d"].defines.append("OPEN3D_STATIC")
