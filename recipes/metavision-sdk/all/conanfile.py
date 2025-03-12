import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, replace_in_file, rmdir, rename, export_conandata_patches, apply_conandata_patches
from conan.tools.scm import Version

required_conan_version = ">=2.0"


class MetavisionSdkConan(ConanFile):
    name = "metavision-sdk"
    description = "Open source SDK to create applications leveraging event-based vision hardware equipment"
    license = "Apache"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/prophesee-ai/openeb"
    topics = ("sdk", "computer-vision", "camera-api", "neuromorphic", "event-camera")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_hdf5": [True, False],
        # modules
        "stream": [True, False],
        "ui": [True, False],
    }
    default_options = {
        "with_hdf5": True,
        # modules
        "stream": True,
        "ui": True,
    }

    @property
    def _stream_module(self):
        return "stream" if Version(self.version).major >= 5 else "driver"

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Android":
            del self.options.with_hdf5

    def configure(self):
        if not self.options.stream:
            self.options.rm_safe("with_hdf5")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # metavision/psee_hw_layer/boards/utils/psee_libusb.h
        self.requires("libusb/1.0.26", transitive_headers=True)
        # several headers, e.g. metavision/sdk/core/preprocessors/json_parser.h
        self.requires("boost/1.86.0", transitive_headers=True)
        # used in many public headers
        self.requires("opencv/4.11.0", transitive_headers=True)
        if self.options.stream:
            # newer version conflicts with opencv
            self.requires("protobuf/3.21.12")
            if self.options.get_safe("with_hdf5"):
                # hdf5_ecf/ecf_h5filter.h
                self.requires("hdf5/1.14.5", transitive_headers=True)
        if self.options.ui:
            # metavision/sdk/ui/utils/opengl_api.h
            self.requires("opengl/system", transitive_headers=True)
            self.requires("glew/2.2.0", transitive_headers=True)
            self.requires("glfw/3.4", transitive_headers=True)

    def build_requirements(self):
        if self.options.stream:
            self.tool_requires("protobuf/<host_version>")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["openeb"], strip_root=True)
        get(self, **self.conan_data["sources"][self.version]["hdf5_ecf"], strip_root=True,
            destination=os.path.join("sdk", "modules", self._stream_module, "cpp", "3rdparty", "hdf5_ecf"))
        apply_conandata_patches(self)
        # Let Conan set the C++ version
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 17)", "")
        # Unvendor nlohmann_json
        rmdir(self, os.path.join("utils", "cpp", "3rdparty"))
        # Ensure Conan deps are used
        rmdir(self, os.path.join("cmake", "Modules"))
        # Don't look for nvcc - only used for Python bindings
        replace_in_file(self, "CMakeLists.txt", "check_language(CUDA)", "")
        # Only used for Python bindings
        rmdir(self, os.path.join("sdk", "modules", "core_ml", "models"))

    @property
    def _enabled_modules(self):
        modules = ["base", "core"]
        if self.options.stream:
            modules.append(self._stream_module)
        if self.options.ui:
            modules.append("ui")
        return modules

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["BUILD_SAMPLES"] = False
        tc.cache_variables["GENERATE_DOC"] = False
        tc.cache_variables["COMPILE_PYTHON3_BINDINGS"] = False
        tc.cache_variables["UDEV_RULES_SYSTEM_INSTALL"] = False
        tc.cache_variables["HDF5_DISABLED"] = not self.options.get_safe("with_hdf5", False)
        tc.cache_variables["METAVISION_SELECTED_MODULES"] = ";".join(self._enabled_modules)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("libusb", "cmake_target_name", "libusb-1.0")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE_OPEN", os.path.join(self.source_folder, "licensing"), os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share", "hdf5_ecf"))
        rmdir(self, os.path.join(self.package_folder, "share", "metavision", "hal_psee_plugins"))
        rmdir(self, os.path.join(self.package_folder, "share", "metavision", "licensing"))
        rmdir(self, os.path.join(self.package_folder, "share", "metavision", "log"))
        rename(self, os.path.join(self.package_folder, "share"), os.path.join(self.package_folder, "res"))

    def package_info(self):
        # The project also installs config files for MetavisionHAL, MetavisionPSEEHWLayer and hdf5_ecf,
        # which cannot be reproduced by Conan
        self.cpp_info.set_property("cmake_file_name", "MetavisionSDK")

        self.cpp_info.components["base"].set_property("cmake_target_name", "Metavision::base")
        self.cpp_info.components["base"].libs = ["metavision_sdk_base"]

        self.cpp_info.components["HAL"].set_property("cmake_target_name", "Metavision::HAL")
        self.cpp_info.components["HAL"].libs = ["metavision_hal"]
        self.cpp_info.components["HAL"].requires = ["base"]
        self.cpp_info.components["HAL"].resdirs = [os.path.join("res", "HAL", "resources")]
        self.runenv_info.append("MV_HAL_PLUGIN_PATH", os.path.join(self.package_folder, "lib", "metavision", "hal", "plugins"))

        self.cpp_info.components["HAL_discovery"].set_property("cmake_target_name", "Metavision::HAL_discovery")
        self.cpp_info.components["HAL_discovery"].libs = ["metavision_hal_discovery"]
        self.cpp_info.components["HAL_discovery"].requires = ["HAL"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["HAL_discovery"].system_libs.append("dl")

        self.cpp_info.components["PSEEHWLayer"].set_property("cmake_target_name", "Metavision::PSEEHWLayer")
        self.cpp_info.components["PSEEHWLayer"].libs = ["metavision_psee_hw_layer"]
        self.cpp_info.components["PSEEHWLayer"].libdirs = [os.path.join("lib", "metavision", "hal", "plugins")]
        self.cpp_info.components["PSEEHWLayer"].requires = [
            "HAL",
            "libusb::libusb",
        ]

        self.cpp_info.components["core"].set_property("cmake_target_name", "Metavision::core")
        self.cpp_info.components["core"].libs = ["metavision_sdk_core"]
        self.cpp_info.components["core"].requires = [
            "base",
            "opencv::opencv_core",
            "opencv::opencv_imgproc",
            "opencv::opencv_videoio",
            "boost::headers",
            "boost::timer",
        ]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["core"].system_libs.append("m")

        if self.options.stream:
            self.cpp_info.components["hdf5_ecf_codec"].set_property("cmake_target_name", "hdf5_ecf_codec")
            self.cpp_info.components["hdf5_ecf_codec"].libs = ["hdf5_ecf_codec"]
            self.runenv_info.append("HDF5_PLUGIN_PATH", os.path.join(self.package_folder, "lib", "hdf5", "plugin"))

            self.cpp_info.components[self._stream_module].set_property("cmake_target_name", f"Metavision::{self._stream_module}")
            if Version(self.version) < "5.0":
                self.cpp_info.components[self._stream_module].set_property("cmake_target_aliases", ["Metavision::stream"])
            self.cpp_info.components[self._stream_module].libs = [f"metavision_sdk_{self._stream_module}"]
            self.cpp_info.components[self._stream_module].requires = [
                "base",
                "core",
                "HAL",
                "HAL_discovery",
                "protobuf::libprotobuf",
                "hdf5_ecf_codec",
            ]
            if self.options.get_safe("with_hdf5"):
                self.cpp_info.components["stream"].requires.append("hdf5::hdf5_cpp")

        if self.options.ui:
            self.cpp_info.components["ui"].set_property("cmake_target_name", "Metavision::ui")
            self.cpp_info.components["ui"].libs = ["metavision_sdk_ui"]
            self.cpp_info.components["ui"].requires = [
                "core",
                "opencv::opencv_core",
                "opengl::opengl",
                "glfw::glfw",
                "glew::glew",
            ]
