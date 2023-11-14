import os
import shutil

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os, XCRun
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv, Environment
from conan.tools.files import copy, get, save
from conan.tools.gnu import AutotoolsToolchain, AutotoolsDeps
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class PdfiumConan(ConanFile):
    name = "pdfium"
    description = "PDF generation and rendering library."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://opensource.google/projects/pdfium"
    topics = ("generate", "generation", "rendering", "pdf", "document", "print")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_libjpeg": ["libjpeg", "libjpeg-turbo"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_libjpeg": "libjpeg",
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("freetype/2.13.0")
        self.requires("icu/74.1")
        self.requires("lcms/2.14")
        self.requires("openjpeg/2.5.0")
        if self.options.with_libjpeg == "libjpeg":
            self.requires("libjpeg/9e")
        elif self.options.with_libjpeg == "libjpeg-turbo":
            self.requires("libjpeg-turbo/3.0.0")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 14)
        minimum_compiler_versions = {
            "gcc": "8",
            "msvc": "191",
            "Visual Studio": "15",
        }
        min_compiler_version = minimum_compiler_versions.get(str(self.settings.compiler))
        if min_compiler_version and Version(self.settings.compiler.version) < min_compiler_version:
            raise ConanInvalidConfiguration(
                f"pdfium needs at least compiler version {min_compiler_version}"
            )

    def build_requirements(self):
        self.tool_requires("gn/cci.20210429")
        self.tool_requires("ninja/1.11.1")
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/2.0.3")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["pdfium"],
            destination=self.source_folder)
        get(self, **self.conan_data["sources"][self.version]["trace_event"],
            destination=os.path.join(self.source_folder, "base", "trace_event", "common"))
        get(self, **self.conan_data["sources"][self.version]["chromium_build"],
            destination=os.path.join(self.source_folder, "build"))

    @property
    def _gn_os(self):
        if self.settings.os == "Windows":
            return "win"
        elif self.settings.os == "Macos":
            return "mac"
        elif is_apple_os(self):
            return "ios"
        return str(self.settings.os).lower()

    @property
    def _gn_arch(self):
        return {
            "x86_64": "x64",
            "armv8": "arm64",
            "x86": "x86",
        }.get(str(self.settings.arch), str(self.settings.arch))

    @property
    def _http_transport_impl(self):
        if not self.options.http_transport:
            return ""
        return str(self.options.http_transport)

    def _generate_args_gn(self, gn_args):
        formatted_args = {}
        for k, v in gn_args.items():
            if isinstance(v, bool):
                formatted_args[k] = "true" if v else "false"
            elif isinstance(v, str):
                formatted_args[k] = f'"{v}"'
        save(self, os.path.join(self.build_folder, "args.gn"),
             "\n".join(f"{k} = {v}" for k, v in formatted_args.items()))

    @property
    def _cxx(self):
        compilers_by_conf = self.conf.get("tools.build:compiler_executables", default={}, check_type=dict)
        cxx = compilers_by_conf.get("cpp") or VirtualBuildEnv(self).vars().get("CXX")
        if cxx:
            return cxx
        if self.settings.compiler == "apple-clang":
            return XCRun(self).cxx
        compiler_version = self.settings.compiler.version
        major = Version(compiler_version).major
        if self.settings.compiler == "gcc":
            return shutil.which(f"g++-{compiler_version}") or shutil.which(f"g++-{major}") or shutil.which("g++") or ""
        if self.settings.compiler == "clang":
            return shutil.which(f"clang++-{compiler_version}") or shutil.which(f"clang++-{major}") or shutil.which("clang++") or ""
        return ""

    def generate(self):
        VirtualBuildEnv(self).generate()
        VirtualRunEnv(self).generate(scope="build")

        tc = AutotoolsToolchain(self)
        deps = AutotoolsDeps(self)

        def _get_flags(name):
            return " ".join(filter(None, [tc.vars().get(name), deps.vars().get(name)]))

        env = Environment()
        env.define("CXX", self._cxx)
        env.vars(self).save_script("conanbuild_gn")

        gn_args = {}
        gn_args["extra_arflags"] = _get_flags("ARFLAGS")
        gn_args["extra_cflags"] = _get_flags("CPPFLAGS")
        gn_args["extra_cflags_c"] = _get_flags("CFLAGS")
        gn_args["extra_cflags_cc"] = _get_flags("CXXFLAGS")
        gn_args["extra_ldflags"] = _get_flags("LDFLAGS") + " " + _get_flags("LIBS")
        gn_args["host_os"] = self._gn_os
        gn_args["host_cpu"] = self._gn_arch
        gn_args["is_debug"] = self.settings.build_type == "Debug"
        gn_args["crashpad_http_transport_impl"] = self._http_transport_impl
        gn_args["crashpad_use_boringssl_for_http_transport_socket"] = bool(self.options.get_safe("with_tls"))
        self._generate_args_gn(gn_args)

    def build(self):
        self.run(f'gn gen "{self.build_folder}"', cwd=self.source_folder)
        targets = ["client", "minidump", "crashpad_handler", "snapshot"]
        if self.settings.os == "Windows":
            targets.append("crashpad_handler_com")
        self.run(f"ninja -C {self.build_folder} {' '.join(targets)} -j{os.cpu_count()}")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["pdfium"]
        if is_apple_os(self):
            self.cpp_info.frameworks.extend(["Appkit", "CoreFoundation", "CoreGraphics"])

        stdcpp_library = stdcpp_library(self)
        if stdcpp_library:
            self.cpp_info.system_libs.append(stdcpp_library)
