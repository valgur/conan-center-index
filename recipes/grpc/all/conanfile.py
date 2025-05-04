import os
from functools import cached_property
from pathlib import Path

import yaml
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import cross_building, check_min_cppstd
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain, CMakeDeps
from conan.tools.files import *
from conan.tools.microsoft import check_min_vs, is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class GrpcConan(ConanFile):
    name = "grpc"
    description = "Google's RPC (remote procedure call) library and framework."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/grpc/grpc"
    topics = ("rpc",)

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "codegen": [True, False],
        "csharp_ext": [True, False],
        "cpp_plugin": [True, False],
        "csharp_plugin": [True, False],
        "node_plugin": [True, False],
        "objective_c_plugin": [True, False],
        "php_plugin": [True, False],
        "python_plugin": [True, False],
        "ruby_plugin": [True, False],
        "otel_plugin": [True, False],
        "secure": [True, False],
        "with_libsystemd": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "codegen": True,
        "csharp_ext": False,
        "cpp_plugin": True,
        "csharp_plugin": True,
        "node_plugin": True,
        "objective_c_plugin": True,
        "php_plugin": True,
        "python_plugin": True,
        "ruby_plugin": True,
        "otel_plugin": False,
        "secure": False,
        "with_libsystemd": False,
    }

    @property
    def _grpc_plugin_template(self):
        return "grpc_plugin_template.cmake.in"

    def export(self):
        copy(self, f"target_info/grpc_{self.version}.yml", self.recipe_folder, self.export_folder)

    def export_sources(self):
        copy(self, "conan_cmake_project_include.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))
        copy(self, f"cmake/{self._grpc_plugin_template}", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if not (self.settings.os in ["Linux", "FreeBSD"] and Version(self.version) >= "1.52"):
            del self.options.with_libsystemd
        if Version(self.version) < "1.65.0":
            del self.options.otel_plugin

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
            self.options["protobuf"].shared = True
            if cross_building(self):
                self.options["grpc"].shared = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # abseil requires:
        # transitive_headers=True because grpc headers include abseil headers
        # transitive_libs=True because generated code (grpc_cpp_plugin) require symbols from abseil
        if Version(self.version) >= "1.62.0":
            self.requires("protobuf/5.27.0", transitive_headers=True)
            self.requires("abseil/[>=20240116.1 <20240117.0]", transitive_headers=True, transitive_libs=True)
        else:
            self.requires("protobuf/3.21.12", transitive_headers=True)
            self.requires("abseil/[>=20230125.3 <=20230802.1]", transitive_headers=True, transitive_libs=True)
        self.requires("c-ares/[>=1.19.1 <2]")
        self.requires("openssl/[>=1.1 <4]")
        self.requires("re2/20230301")
        self.requires("zlib/[>=1.2.11 <2]")
        if self.options.get_safe("with_libsystemd"):
            self.requires("libsystemd/[^255]")
        if self.options.get_safe("otel_plugin"):
            self.requires("opentelemetry-cpp/1.14.2")

    def package_id(self):
        del self.info.options.secure

    def validate(self):
        check_min_vs(self, "190")
        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} shared not supported by Visual Studio")

        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "6":
            raise ConanInvalidConfiguration("GCC older than 6 is not supported")

        check_min_cppstd(self, 17 if Version(self.version) >= "1.70" else 14)

        if self.options.shared and not self.dependencies.host["protobuf"].options.shared:
            raise ConanInvalidConfiguration(
                "If built as shared protobuf must be shared as well. "
                "Please, use `protobuf/*:shared=True`.",
            )

    def build_requirements(self):
        # cmake >=3.25 required to use `cmake -E env --modify` below
        self.tool_requires("cmake/[>=3.25 <5]")
        self.tool_requires("protobuf/<host_version>")
        if cross_building(self):
            # when cross compiling we need pre compiled grpc plugins for protoc
            self.tool_requires(f"grpc/{self.version}")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_grpc_INCLUDE"] = os.path.join(self.source_folder, "conan_cmake_project_include.cmake")
        tc.cache_variables["gRPC_BUILD_CODEGEN"] = self.options.codegen
        tc.cache_variables["gRPC_BUILD_CSHARP_EXT"] = self.options.csharp_ext
        tc.cache_variables["gRPC_BUILD_TESTS"] = False
        # We need the generated cmake/ files (bc they depend on the list of targets, which is dynamic)
        tc.cache_variables["gRPC_INSTALL"] = True
        tc.cache_variables["gRPC_BUILD_GRPC_CPP_PLUGIN"] = self.options.cpp_plugin
        tc.cache_variables["gRPC_BUILD_GRPC_CSHARP_PLUGIN"] = self.options.csharp_plugin
        tc.cache_variables["gRPC_BUILD_GRPC_NODE_PLUGIN"] = self.options.node_plugin
        tc.cache_variables["gRPC_BUILD_GRPC_OBJECTIVE_C_PLUGIN"] = self.options.objective_c_plugin
        tc.cache_variables["gRPC_BUILD_GRPC_PHP_PLUGIN"] = self.options.php_plugin
        tc.cache_variables["gRPC_BUILD_GRPC_PYTHON_PLUGIN"] = self.options.python_plugin
        tc.cache_variables["gRPC_BUILD_GRPC_RUBY_PLUGIN"] = self.options.ruby_plugin
        tc.cache_variables["gRPC_BUILD_GRPCPP_OTEL_PLUGIN"] = self.options.get_safe("otel_plugin", False)
        tc.cache_variables["gRPC_USE_SYSTEMD"] = self.options.get_safe("with_libsystemd", False)
        # tell grpc to use the find_package versions
        for dep in ["ZLIB", "CARES", "RE2", "SSL", "PROTOBUF", "ABSL", "OPENTELEMETRY"]:
            tc.cache_variables[f"gRPC_{dep}_PROVIDER"] = "package"
        # Never download unnecessary archives
        tc.cache_variables["gRPC_DOWNLOAD_ARCHIVES"] = False
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        # workaround for: install TARGETS given no BUNDLE DESTINATION for MACOSX_BUNDLE executable
        tc.cache_variables["CMAKE_MACOSX_BUNDLE"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        # Management of shared libs when grpc has shared dependencies (like protobuf)
        # As the grpc_cpp_plugin that executes during the build will need those packages shared libs
        cmakelists = os.path.join(self.source_folder, "CMakeLists.txt")
        variable, repl = None, None
        if self.settings_build.os == "Macos":
            # On macOS if all the following are true:
            # - protoc from protobuf has shared library dependencies
            # - grpc_cpp_plugin has shared library deps (when crossbuilding)
            # - using `make` as the cmake generator
            # Make will run commands via `/bin/sh` which will strip all env vars that start with `DYLD*`
            # This workaround wraps the protoc command to be invoked by CMake with a modified environment
            variable, repl = "DYLD_LIBRARY_PATH", "$ENV{DYLD_LIBRARY_PATH}" # to bypass OSX restrictions
        elif not cross_building(self) and self.settings_build.os == "Linux":
            # CMAKE_LIBRARY_PATH is defined by conan_toolchain.cmake, in Linux it is "lib" dir of .so dependencies
            variable, repl = "LD_LIBRARY_PATH", "$<JOIN:${CMAKE_LIBRARY_PATH},:>" # to allow using protobuf/abseil as shared deps
        elif not cross_building(self) and self.settings_build.os == "Windows":
            # CONAN_RUNTIME_LIB_DIRS defined by conan_toolchain.cmake points to the "bin" folder in Linux, containing the DLLs
            variable, repl = "PATH", "$<JOIN:${CONAN_RUNTIME_LIB_DIRS},;>" # to allow using protobuf/abseil as shared deps

        if variable and repl:
            replace_in_file(self, cmakelists,
                            "COMMAND ${_gRPC_PROTOBUF_PROTOC_EXECUTABLE}",
                            f'COMMAND ${{CMAKE_COMMAND}} -E env --modify "{variable}=path_list_prepend:{repl}" ${{_gRPC_PROTOBUF_PROTOC_EXECUTABLE}}')

        if self.settings.os == "Macos" and Version(self.version) >= "1.64":
            # See https://github.com/grpc/grpc/issues/36654#issuecomment-2228569158
            replace_in_file(self, cmakelists, "target_compile_features(upb_textformat_lib PUBLIC cxx_std_14)",
            """target_compile_features(upb_textformat_lib PUBLIC cxx_std_14)
            target_link_options(upb_textformat_lib PRIVATE -Wl,-undefined,dynamic_lookup)
            target_link_options(upb_json_lib PRIVATE -Wl,-undefined,dynamic_lookup)
            """)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @cached_property
    def _target_info(self):
        path = Path(self.recipe_folder, "target_info", f"grpc_{self.version}.yml")
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

        # Create one custom module file per executable in order to emulate
        # CMake executables imported targets of grpc plugins.
        for executable, plugin_info in self._target_info["plugins"].items():
            target = f"gRPC::{executable}"
            option_name = executable.replace("grpc_", "")
            if self.options.get_safe(option_name):
                self._create_executable_module_file(target, executable)

    def _create_executable_module_file(self, target, executable):
        module_abs_path = os.path.join(self.package_folder, self._module_path)

        # Copy our CMake module template file to package folder
        copy(self, self._grpc_plugin_template, src=os.path.join(self.source_folder, "cmake"), dst=module_abs_path)

        # Rename it
        dst_file = os.path.join(module_abs_path, f"{executable}.cmake")
        rename(self, os.path.join(module_abs_path, self._grpc_plugin_template), dst_file)

        # Replace placeholders
        replace_in_file(self, dst_file, "@target_name@", target)
        replace_in_file(self, dst_file, "@executable_name@", executable)

        find_program_var = f"{executable.upper()}_PROGRAM"
        replace_in_file(self, dst_file, "@find_program_variable@", find_program_var)

        module_folder_depth = len(os.path.normpath(self._module_path).split(os.path.sep))
        rel_path = "".join(["../"] * module_folder_depth)
        replace_in_file(self, dst_file, "@relative_path@", rel_path)

    @property
    def _module_path(self):
        return os.path.join("lib", "cmake", "conan_trick")

    @property
    def _grpc_components(self):
        system_libs = []
        if self.settings.os == "Windows":
            system_libs = ["crypt32", "ws2_32", "wsock32"]
        elif self.settings.os in ["Linux", "FreeBSD"]:
            system_libs = ["m", "pthread"]

        libsystemd = ["libsystemd::libsystemd"] if self.options.get_safe("with_libsystemd") else []

        renames = {"grpc": "_grpc"}
        components = {}
        for name, target in self._target_info["targets"].items():
            if self.options.secure and name in ["grpc_unsecure", "grpc++_unsecure"]:
                continue
            if not self.options.codegen and name in ["grpc++_reflection", "grpcpp_channelz"]:
                continue
            components[renames.get(name, name)] = {
                "lib": target.get("lib", name),
                "requires": [renames.get(x, x) for x in target.get("deps", [])] + libsystemd,
                "system_libs": system_libs,
                "frameworks": ["CoreFoundation"] if name in ["grpc", "grpc_unsecure"] else [],
            }

        return components

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "gRPC")
        self.cpp_info.resdirs = ["share"]
        ssl_roots_file_path = os.path.join(self.package_folder, "share", "grpc", "roots.pem")
        self.runenv_info.define_path("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", ssl_roots_file_path)

        for component, values in self._grpc_components.items():
            target = values.get("lib")
            lib = values.get("lib")
            self.cpp_info.components[component].set_property("cmake_target_name", f"gRPC::{target}")
            # actually only gpr, grpc, grpc_unsecure, grpc++ and grpc++_unsecure should have a .pc file
            self.cpp_info.components[component].set_property("pkg_config_name", target)
            self.cpp_info.components[component].libs = [lib]
            self.cpp_info.components[component].requires = values.get("requires", [])
            self.cpp_info.components[component].system_libs = values.get("system_libs", [])
            if is_apple_os(self):
                self.cpp_info.components[component].frameworks = values.get("frameworks", [])

        # Executable imported targets are added through custom CMake module files,
        # since conan generators don't know how to emulate these kind of targets.
        grpc_modules = []
        for executable, plugin_info in self._target_info["plugins"].items():
            option_name = executable.replace("grpc_", "")
            if self.options.get_safe(option_name):
                grpc_module_filename = f"{executable}.cmake"
                grpc_modules.append(os.path.join(self._module_path, grpc_module_filename))
        self.cpp_info.set_property("cmake_build_modules", grpc_modules)
