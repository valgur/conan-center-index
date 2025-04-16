import os
from functools import lru_cache
from pathlib import Path

import yaml
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class FreeRTOSKernelConan(ConanFile):
    name = "freertos-kernel"
    description = "The FreeRTOS Kernel library"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.freertos.org/"
    license = "MIT"
    settings = "os", "arch", "compiler", "build_type"
    topics = ("freertos", "realtime", "rtos")
    package_type = "library"
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
        "port": ["A_CUSTOM_PORT", "ANY"],
        "risc_v_chip_extension": [
            "Pulpino_Vega_RV32M1RM",
            "RISCV_MTIME_CLINT_no_extensions",
            "RISCV_no_extensions",
            "RV32I_CLINT_no_extensions",
        ],
        "heap": ["1", "2", "3", "4", "5"],
        "config": [None, "ANY"],
        "config_contents": ["", "ANY"],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
        "port": "GCC_POSIX",
        "heap": "4",
        "risc_v_chip_extension": "RISCV_no_extensions",
        "config": None,
        "config_contents": "",
    }
    options_description = {
        "config": "The path to the FreeRTOSConfig.h file.",
        "config_contents": "The contents fo the FreeRTOSConfig.h file.",
    }

    @staticmethod
    def _config_contents(self):
        if self.options.config:
            return Path(str(self.options.config)).read_text(encoding="utf-8")
        else:
            return str(self.options.config_contents)

    @property
    @lru_cache
    def _port_include_directories(self):
        v = Version(self.version)
        return yaml.safe_load(Path(self.recipe_folder, "include_dirs", f"{v.major}.{v.minor}.yml").read_text())

    def export(self):
        v = Version(self.version)
        copy(self, f"include_dirs/{v.major}.{v.minor}.yml", self.recipe_folder, self.export_folder)

    def config_options(self):
        if self.settings.os in ["baremetal", "Windows"]:
            self.options.rm_safe("fPIC")
            self.options.port = "MSVC_MINGW"

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

        if self.options.port not in ["GCC_RISC_V_GENERIC", "IAR_RISC_V_GENERIC"]:
            self.options.rm_safe("risc_v_chip_extension")
        else:
            if self.options.port == "IAR_RISC_V_GENERIC":
                self.options.risc_v_chip_extension = "RV32I_CLINT_no_extensions"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.options.config_contents = self._config_contents(self.info)
        del self.info.options.config

    def validate(self):
        if self.options.port != "A_CUSTOM_PORT" and str(self.options.port) not in self._port_include_directories:
            raise ConanInvalidConfiguration(
                f"Unknown port '{self.options.port}' selected."
                f"Supported ports are: A_CUSTOM_PORT, {', '.join(self._port_include_directories.keys())}"
            )
        if not self.options.config_contents and not self.options.config:
            raise ConanInvalidConfiguration("At least one of 'config_contents' or 'config' options must be provided.")
        if self.options.config_contents and self.options.config:
            raise ConanInvalidConfiguration("Both 'config_contents' and 'config' options may not be set simultaneously.")
        if (
                self.options.port == "IAR_RISC_V_GENERIC"
                and self.options.get_safe("risc_v_chip_extension") != "RV32I_CLINT_no_extensions"
        ):
            raise ConanInvalidConfiguration(
                "Only the RV32I_CLINT_no_extensions RISC-V extension can be enabled when using the IAR_RISC_V_GENERIC port"
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["FREERTOS_HEAP"] = self.options.heap
        tc.variables["FREERTOS_PORT"] = self.options.port
        if self.options.get_safe("risc_v_chip_extension"):
            tc.variables["FREERTOS_RISCV_EXTENSION"] = self.options.risc_v_chip_extension
        tc.variables["_FREERTOS_CONFIG_DIR"] = self.build_folder.replace("\\", "/")
        tc.generate()

    def build(self):
        config_path = Path(self.source_folder, "include", "FreeRTOSConfig.h")
        config_path.parent.mkdir(exist_ok=True)
        config_path.write_text(self._config_contents(self), encoding="utf-8")
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "*.h",
             os.path.join(self.source_folder, "include"),
             os.path.join(self.package_folder, "include"),
             keep_path=False)
        if self.options.get_safe("risc_v_chip_extension"):
            for risc_v_generic_port in ["GCC", "IAR"]:
                self._port_include_directories[f"{risc_v_generic_port}_RISC_V_GENERIC"].append(
                    os.path.join(risc_v_generic_port, "RISC-V", "chip_specific_extensions", str(self.options.risc_v_chip_extension))
                )
        for include_directory in self._port_include_directories[str(self.options.port)]:
            copy(self, "*.h",
                 os.path.join(self.source_folder, "portable", include_directory),
                 os.path.join(self.package_folder, "include"),
                 keep_path=False)
        copy(self, "*freertos_kernel.dll", self.build_folder, os.path.join(self.package_folder, "bin"))
        copy(self, "*freertos_kernel.lib", self.build_folder, os.path.join(self.package_folder, "lib"))
        copy(self, "*freertos_kernel.so*", self.build_folder, os.path.join(self.package_folder, "lib"))
        copy(self, "*freertos_kernel.dylib", self.build_folder, os.path.join(self.package_folder, "lib"))
        copy(self, "*freertos_kernel.a", self.build_folder, os.path.join(self.package_folder, "lib"))
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.libs = ["freertos_kernel"]

        if self.settings.os in ["FreeBSD", "Linux"]:
            self.cpp_info.system_libs.append("pthread")
