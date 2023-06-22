# TODO: verify the Conan v2 migration

import os

from conan import ConanFile, conan_version
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.android import android_abi
from conan.tools.apple import (
    XCRun,
    fix_apple_shared_install_name,
    is_apple_os,
    to_apple_arch,
)
from conan.tools.build import (
    build_jobs,
    can_run,
    check_min_cppstd,
    cross_building,
    default_cppstd,
    stdcpp_library,
    valid_min_cppstd,
)
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
from conan.tools.env import (
    Environment,
    VirtualBuildEnv,
    VirtualRunEnv,
)
from conan.tools.files import (
    apply_conandata_patches,
    chdir,
    collect_libs,
    copy,
    download,
    export_conandata_patches,
    get,
    load,
    mkdir,
    patch,
    patches,
    rename,
    replace_in_file,
    rm,
    rmdir,
    save,
    symlinks,
    unzip,
)
from conan.tools.gnu import (
    Autotools,
    AutotoolsDeps,
    AutotoolsToolchain,
    PkgConfig,
    PkgConfigDeps,
)
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import (
    MSBuild,
    MSBuildDeps,
    MSBuildToolchain,
    NMakeDeps,
    NMakeToolchain,
    VCVars,
    check_min_vs,
    is_msvc,
    is_msvc_static_runtime,
    msvc_runtime_flag,
    unix_path,
    unix_path_package_info_legacy,
    vs_layout,
)
from conan.tools.microsoft.visual import vs_ide_version
from conan.tools.scm import Version
from conan.tools.system import package_manager
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
import os

required_conan_version = ">=1.33.0"


class JerryScriptStackConan(ConanFile):
    name = "jerryscript"
    license = "Apache-2.0"
    homepage = "https://github.com/jerryscript-project/jerryscript"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Ultra-lightweight JavaScript engine for the Internet of Things"
    topics = ["javascript", "iot", "javascript-engine"]
    exports_sources = "CMakeLists.txt", "patches/**"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tool_cmdline": [True, False],
        "tool_cmdline_test": [True, False],
        "tool_cmdline_snapshot": [True, False],
        "default_port_implementation": [True, False],
        "jerry_ext": [True, False],
        "jerry_math": [True, False],
        "link_time_optimization": [True, False],
        "strip_symbols": [True, False],
        "amalgamated": [True, False],
        "debugger": [True, False],
        "keep_line_info": [True, False],
        "profile": "ANY",
        "promise_callback": [True, False],
        "external_context": [True, False],
        "snapshot_execution": [True, False],
        "snapshot_saving": [True, False],
        "parser": [True, False],
        "enable_dump_bytecode": [True, False],
        "enable_dump_regexp_bytecode": [True, False],
        "strict_regexp": [True, False],
        "error_messages": [True, False],
        "logging": [True, False],
        "memory_statistics": [True, False],
        "heap_size": "ANY",
        "gc_limit": "ANY",
        "gc_mark_limit": "ANY",
        "stack_limit": "ANY",
        "cpointer_32_bit": [True, False],
        "system_allocator": [True, False],
        "valgrind": [True, False],
        "gc_before_each_alloc": [True, False],
        "vm_exec_stop": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tool_cmdline": True,
        "tool_cmdline_test": False,
        "tool_cmdline_snapshot": False,
        "default_port_implementation": True,
        "jerry_ext": True,
        "jerry_math": False,  # Initialized in `config_options`
        "link_time_optimization": False,  # Enabled by upstream, but disabled to be confirm cci (add -flto in your profile)
        "strip_symbols": True,
        "amalgamated": False,
        "debugger": False,
        "keep_line_info": False,
        "profile": None,  # Initialized in `config_options`
        "promise_callback": False,
        "external_context": False,
        "snapshot_execution": False,
        "snapshot_saving": False,
        "parser": True,
        "enable_dump_bytecode": False,
        "enable_dump_regexp_bytecode": False,
        "strict_regexp": False,
        "error_messages": False,
        "logging": False,
        "memory_statistics": False,
        "heap_size": 512,
        "gc_limit": 0,
        "gc_mark_limit": 8,
        "stack_limit": 0,
        "cpointer_32_bit": False,
        "system_allocator": False,
        "valgrind": False,
        "gc_before_each_alloc": False,
        "vm_exec_stop": False,
    }
    _predefined_profiles = ["es.next", "es5.1", "minimal"]

    @property
    def _jerry_math(self):
        return self.options.get_safe("jerry_math", False)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        # profile and jerry_match default option value depend on version
        if Version(self.version) < "2.4.0":
            self.options.profile = "es5.1"
            self.options.jerry_math = True
            if self.settings.compiler == "Visual Studio":
                self.options.rm_safe("jerry_math")  # forced to False
        else:
            self.options.profile = "es.next"
            self.options.jerry_math = False

        if self.settings.os == "Macos":
            self.options.rm_safe("jerry_math")  # forced to False
            self.options.rm_safe("link_time_optimization")  # forced to False
            self.options.rm_safe("strip")  # forced to False

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.options.shared:
            self.options.rm_safe("fPIC")

        if not self.options.debugger:
            self.options.rm_safe("keep_line_info")

        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration("jerryscript shared lib is not yet supported under windows")

    def validate(self):
        # validate integers
        try:
            checks = (
                (0 <= int(self.options.heap_size), "heap_size must be bigger than or equal to 0"),
                (0 <= int(self.options.gc_limit) <= 8192, "gc_limit must be in the range [0, 8192]"),
                (0 <= int(self.options.gc_mark_limit), "gc_mark_limit must be bigger than or equal to 0"),
                (0 <= int(self.options.stack_limit), "stack_limit must be bigger than or equal to 0"),
            )
            for check_res, txt in checks:
                if not check_res:
                    raise ConanInvalidConfiguration(txt)
        except ValueError as e:
            raise ConanInvalidConfiguration(
                "jerryscript heap size, gc mark limit, stack limit, gc limit should be a positive integer"
            )
        # validate profile file
        if self.options.profile not in self._predefined_profiles and not os.path.isfile(
            str(self.options.profile)
        ):
            raise ConanInvalidConfiguration(
                "Invalid profile option. Feature profile must either be a valid file or one of these: es.next, es5.1, minimal"
            )
        # validate the use of the system allocator option
        if self.settings.arch == "x86_64" and self.options.system_allocator:
            raise ConanInvalidConfiguration("jerryscript system allocator not available on 64bit systems")
        if self.options.system_allocator and not self.options.cpointer_32_bit:
            raise ConanInvalidConfiguration("jerryscript system allocator must be used with 32 bit pointers")

    def package_id(self):
        if self.options.profile not in self._predefined_profiles:
            self.info.options.profile = load(self, str(self.options.profile))

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        amalgamation_definition = "ENABLE_AMALGAM"
        libmath_definition = "JERRY_MATH"
        if Version(self.version) < Version(self, "2.4.0"):
            amalgamation_definition = "ENABLE_ALL_IN_ONE"
            libmath_definition = "JERRY_LIBM"
        tc.variables["JERRY_CMDLINE"] = self.options.tool_cmdline
        tc.variables["JERRY_CMDLINE_TEST"] = self.options.tool_cmdline_test
        tc.variables["JERRY_CMDLINE_SNAPSHOT"] = self.options.tool_cmdline_snapshot
        tc.variables["JERRY_PORT_DEFAULT"] = self.options.default_port_implementation
        tc.variables["JERRY_EXT"] = self.options.jerry_ext
        tc.variables[libmath_definition] = self._jerry_math
        tc.variables["ENABLE_STRIP"] = self.options.get_safe("jerry_strip", False)
        tc.variables["ENABLE_LTO"] = self.options.get_safe("link_time_optimization", False)
        tc.variables[amalgamation_definition] = self.options.amalgamated
        tc.variables["JERRY_DEBUGGER"] = self.options.debugger
        tc.variables["JERRY_LINE_INFO"] = self.options.get_safe("keep_line_info", False)
        tc.variables["JERRY_PROFILE"] = self.options.profile
        tc.variables["JERRY_EXTERNAL_CONTEXT"] = self.options.external_context
        tc.variables["JERRY_SNAPSHOT_EXEC"] = self.options.snapshot_execution
        tc.variables["JERRY_SNAPSHOT_SAVE"] = self.options.snapshot_saving
        tc.variables["JERRY_PARSER"] = self.options.parser
        tc.variables["JERRY_PARSER_DUMP_BYTE_CODE"] = self.options.enable_dump_bytecode
        tc.variables["JERRY_REGEXP_DUMP_BYTE_CODE"] = self.options.enable_dump_regexp_bytecode
        tc.variables["JERRY_REGEXP_STRICT_MODE"] = self.options.strict_regexp
        tc.variables["JERRY_ERROR_MESSAGES"] = self.options.error_messages
        tc.variables["JERRY_LOGGING"] = self.options.logging
        tc.variables["JERRY_MEM_STATS"] = self.options.memory_statistics
        tc.variables["JERRY_GLOBAL_HEAP_SIZE"] = "(%s)" % self.options.heap_size
        tc.variables["JERRY_GC_LIMIT"] = "(%s)" % self.options.gc_limit
        tc.variables["JERRY_GC_MARK_LIMIT"] = "(%s)" % self.options.gc_mark_limit
        tc.variables["JERRY_STACK_LIMIT"] = "(%s)" % self.options.stack_limit
        tc.variables["JERRY_CPOINTER_32_BIT"] = self.options.cpointer_32_bit
        tc.variables["JERRY_SYSTEM_ALLOCATOR"] = self.options.system_allocator
        tc.variables["JERRY_VALGRIND"] = self.options.valgrind
        tc.variables["JERRY_MEM_GC_BEFORE_EACH_ALLOC"] = self.options.gc_before_each_alloc
        tc.variables["JERRY_VM_EXEC_STOP"] = self.options.vm_exec_stop
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst="licenses", src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.components["libjerry-port-default"].names["pkg_config"] = ["libjerry-port-default"]
        self.cpp_info.components["libjerry-port-default"].libs = ["jerry-port-default"]

        if self._jerry_math:
            mathlibname = "jerry-libm" if Version(self.version) < "2.4.0" else "jerry-math"
            self.cpp_info.components["libjerry-math"].names["pkg_config"] = "lib{}".format(mathlibname)
            self.cpp_info.components["libjerry-math"].libs = [mathlibname]
            self.cpp_info.components["libjerry-math"].requires = ["libjerry-port-default"]
            self.cpp_info.components["libjerry-core"].requires.append("libjerry-math")

        if Version(self.version) < "2.4.0":
            self.cpp_info.components["libjerry-port-default-minimal"].names["pkg_config"] = [
                "libjerry-port-default-minimal"
            ]
            self.cpp_info.components["libjerry-port-default-minimal"].libs = ["jerry-port-default-minimal"]
            self.cpp_info.components["libjerry-port-default"].requires.append("libjerry-port-default-minimal")

        self.cpp_info.components["libjerry-core"].names["pkg_config"] = "libjerry-core"
        self.cpp_info.components["libjerry-core"].libs = ["jerry-core"]
        # The pc file does not explicitly add the port. But it's needed for the test
        self.cpp_info.components["libjerry-core"].requires = ["libjerry-port-default"]
        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.components["libjerry-core"].system_libs.append("m")

        self.cpp_info.components["libjerry-ext"].names["pkg_config"] = "libjerry-ext"
        self.cpp_info.components["libjerry-ext"].libs = ["jerry-ext"]
        self.cpp_info.components["libjerry-ext"].requires = ["libjerry-core"]
