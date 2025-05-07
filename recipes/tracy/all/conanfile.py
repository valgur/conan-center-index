import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.gnu import PkgConfigDeps
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class TracyConan(ConanFile):
    name = "tracy"
    description = "C++ frame profiler"
    license = ["BSD-3-Clause"]
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/wolfpld/tracy"
    topics = ("profiler", "performance", "gamedev")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable": [True, False],
        "on_demand": [True, False],
        "callstack": [True, False],
        "no_callstack": [True, False],
        "no_callstack_inlines": [True, False],
        "only_localhost": [True, False],
        "no_broadcast": [True, False],
        "only_ipv4": [True, False],
        "no_code_transfer": [True, False],
        "no_context_switch": [True, False],
        "no_exit": [True, False],
        "no_sampling": [True, False],
        "no_verify": [True, False],
        "no_vsync_capture": [True, False],
        "no_frame_image": [True, False],
        "no_system_tracing": [True, False],
        "delayed_init": [True, False],
        "manual_lifetime": [True, False],
        "fibers": [True, False],
        "no_crash_handler": [True, False],
        "timer_fallback": [True, False],
        "libunwind_backtrace": [True, False],
        "symbol_offline_resolve": [True, False],
        "libbacktrace_elf_dynload_support": [True, False],
        "verbose": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable": True,
        "on_demand": False,
        "callstack": False,
        "no_callstack": False,
        "no_callstack_inlines": False,
        "only_localhost": False,
        "no_broadcast": False,
        "only_ipv4": False,
        "no_code_transfer": False,
        "no_context_switch": False,
        "no_exit": False,
        "no_sampling": False,
        "no_verify": False,
        "no_vsync_capture": False,
        "no_frame_image": False,
        "no_system_tracing": False,
        "delayed_init": False,
        "manual_lifetime": False,
        "fibers": False,
        "no_crash_handler": False,
        "timer_fallback": False,
        "libunwind_backtrace": False,
        "symbol_offline_resolve": False,
        "libbacktrace_elf_dynload_support": False,
        "verbose": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

        if Version(self.version) < "0.9":
            self.options.rm_safe("manual_lifetime")
            self.options.rm_safe("fibers")
            self.options.rm_safe("no_crash_handler")
            self.options.rm_safe("timer_fallback")

        if Version(self.version) < "0.11.0":
            self.options.rm_safe("libunwind_backtrace")
            self.options.rm_safe("symbol_offline_resolve")
            self.options.rm_safe("libbacktrace_elf_dynload_support")

        if Version(self.version) < "0.11.1":
            self.options.rm_safe("verbose")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.get_safe("libunwind_backtrace"):
            self.requires("libunwind/[^1.8.1]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 11)

        # libunwind_backtrace is not supported in 0.11.0. https://github.com/wolfpld/tracy/pull/841
        if Version(self.version) == "0.11.0" and self.options.get_safe("libunwind_backtrace"):
            raise ConanInvalidConfiguration(f"libunwind_backtrace is not supported in {self.ref}")

    def build_requirements(self):
        if self.options.get_safe("libunwind_backtrace"):
            if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
                self.tool_requires("pkgconf/[>=2.2 <3]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        # Set all tracy options in the correct form
        # For example, TRACY_NO_EXIT
        for opt, switch in self.options.items():
            if opt in ["shared", "fPIC"]:
                continue
            tc.variables[f"TRACY_{opt.upper()}"] = switch
        tc.generate()
        if self.options.get_safe("libunwind_backtrace"):
            deps = PkgConfigDeps(self)
            deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Tracy")
        self.cpp_info.set_property("cmake_target_name", "Tracy::TracyClient")
        self.cpp_info.libs = ["TracyClient"]
        if self.options.shared:
            self.cpp_info.defines.append("TRACY_IMPORTS")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["pthread", "m"])
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.append("dl")
        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["dbghelp", "ws2_32"])
        if self.options.get_safe("libunwind_backtrace"):
            self.cpp_info.requires.append("libunwind::libunwind")

        # Tracy CMake adds options set to ON as public
        for opt, switch in self.options.items():
            if opt in ["shared", "fPIC"]:
                continue
            if switch:
                self.cpp_info.defines.append(f"TRACY_{opt.upper()}")
