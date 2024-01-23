import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import copy, get, export_conandata_patches, apply_conandata_patches, replace_in_file, rmdir
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class SystemcComponentsConan(ConanFile):
    name = "scc"
    description = "A light-weight productivity library for SystemC and TLM 2.0"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://minres.github.io/SystemC-Components"
    topics = ("systemc", "modeling", "tlm", "scc")

    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "enable_phase_callbacks": [True, False],
        "enable_phase_callbacks_tracing": [True, False],
    }
    default_options = {
        "fPIC": True,
        "enable_phase_callbacks": False,
        "enable_phase_callbacks_tracing": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # https://github.com/Minres/SystemC-Components/blob/2023.06/src/sysc/scc/perf_estimator.h#L20
        self.requires("boost/1.83.0", transitive_headers=True, transitive_libs=True)
        # https://github.com/Minres/SystemC-Components/blob/2023.06/src/sysc/scc/trace/vcd_trace.hh#L28
        self.requires("fmt/10.2.1", transitive_headers=True, transitive_libs=True)
        # https://github.com/Minres/SystemC-Components/blob/2023.06/src/common/util/lz4_streambuf.h#L13
        self.requires("lz4/1.9.4", transitive_headers=True, transitive_libs=True)
        self.requires("rapidjson/cci.20220822")
        self.requires("spdlog/1.13.0")
        # https://github.com/Minres/SystemC-Components/blob/2023.06/src/sysc/tlm/scc/lwtr/tlm2_lwtr.h
        self.requires("systemc-cci/1.0.0", transitive_headers=True, transitive_libs=True)
        self.requires("systemc/2.3.4", transitive_headers=True, transitive_libs=True)
        # https://github.com/Minres/SystemC-Components/blob/2023.06/src/sysc/scc/trace/gz_writer.hh#L18
        self.requires("zlib/[>=1.2.11 <2]", transitive_headers=True, transitive_libs=True)
        self.requires("yaml-cpp/0.8.0")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)
        if is_apple_os(self):
            raise ConanInvalidConfiguration(f"{self.name} is not suppported on {self.settings.os}.")
        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "7":
            raise ConanInvalidConfiguration("GCC < version 7 is not supported")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.24 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SC_WITH_PHASE_CALLBACKS"] = self.options.enable_phase_callbacks
        tc.variables["SC_WITH_PHASE_CALLBACK_TRACING"] = self.options.enable_phase_callbacks_tracing
        tc.variables["BUILD_SCC_DOCUMENTATION"] = False
        tc.variables["SCC_LIB_ONLY"] = True
        tc.variables["ENABLE_CONAN"] = False
        if self.settings.os == "Windows":
            tc.variables["SCC_LIMIT_TRACE_TYPE_LIST"] = True
        if not is_msvc(self):
            # Used at https://github.com/Minres/SystemC-Components/blob/2023.06/src/common/util/pool_allocator.h#L110
            # but is not set anywhere
            tc.preprocessor_definitions["_GLIBCXX_USE_NOEXCEPT"] = "noexcept"
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("systemc", "cmake_file_name", "SystemC")
        deps.set_property("systemc-cci", "cmake_target_name", "systemc-cci::systemc-cci")
        deps.set_property("yaml-cpp", "cmake_target_name", "yaml-cpp::yaml-cpp")
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        replace_in_file(self, os.path.join(self.source_folder, "third_party", "axi_chi", "CMakeLists.txt"),
                        " STATIC", "")
        if is_msvc(self):
            # Fix duplicate definition by `template<> struct value_converter<sc_dt::uint64>`
            # https://github.com/Minres/LWTR4SC/blob/03d52fc4e704d62377d1b1073fc45b2b22512654/src/lwtr/lwtr.h#L137-L172
            lwtr_h = os.path.join(self.source_folder, "third_party", "lwtr4sc", "src", "lwtr", "lwtr.h")
            replace_in_file(self, lwtr_h, "VAL_CONV(int64_t);", "")
            replace_in_file(self, lwtr_h, "VAL_CONV(uint64_t);", "")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.components["scc-sysc"].libs = ["scc-sysc"]
        self.cpp_info.components["scc-sysc"].requires = [
            "fstapi",
            "lwtr",
            "scc-util",
            "scv-tr",
            "boost::date_time",
            "fmt::fmt",
            "lz4::lz4",
            "rapidjson::rapidjson",
            "spdlog::spdlog",
            "systemc-cci::systemc-cci",
            "systemc::systemc",
            "yaml-cpp::yaml-cpp",
            "zlib::zlib",
        ]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["scc-sysc"].system_libs = ["pthread", "dl"]

        self.cpp_info.components["busses"].libs = ["busses"]
        self.cpp_info.components["busses"].requires = ["tlm-interfaces", "scc-sysc"]

        self.cpp_info.components["fstapi"].libs = ["fstapi"]
        self.cpp_info.components["fstapi"].requires = ["zlib::zlib", "lz4::lz4"]

        self.cpp_info.components["lwtr"].libs = ["lwtr"]
        self.cpp_info.components["lwtr"].requires = ["zlib::zlib", "lz4::lz4", "systemc::systemc", "fmt::fmt"]

        self.cpp_info.components["scc-util"].libs = ["scc-util"]
        self.cpp_info.components["scc-util"].requires = ["lz4::lz4"]

        self.cpp_info.components["scv-tr"].libs = ["scv-tr"]
        self.cpp_info.components["scv-tr"].requires = ["fmt::fmt", "systemc::systemc"]

        self.cpp_info.components["tlm-interfaces"].libs = ["tlm-interfaces"]
        self.cpp_info.components["tlm-interfaces"].requires = ["scc-sysc", "systemc::systemc"]
