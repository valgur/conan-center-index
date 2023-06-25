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
from conan.tools.scm import Version
from conan.tools.system import package_manager
import os

required_conan_version = ">=1.33.0"


class PdfiumConan(ConanFile):
    name = "pdfium"
    description = "PDF generation and rendering library."
    license = "BSD-3-Clause"
    topics = ("generate", "generation", "rendering", "pdf", "document", "print")
    homepage = "https://opensource.google/projects/pdfium"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "with_libjpeg": ["libjpeg", "libjpeg-turbo"]}
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_libjpeg": "libjpeg",
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("freetype/2.10.4")
        self.requires("icu/69.1")
        self.requires("lcms/2.11")
        self.requires("openjpeg/2.4.0")
        if self.options.with_libjpeg == "libjpeg":
            self.requires("libjpeg/9d")
        elif self.options.with_libjpeg == "libjpeg-turbo":
            self.requires("libjpeg-turbo/2.1.0")

    def build_requirements(self):
        self.build_requires("pkgconf/1.7.4")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 14)
        minimum_compiler_versions = {"gcc": 8, "Visual Studio": 15}
        min_compiler_version = minimum_compiler_versions.get(str(self.settings.compiler))
        if min_compiler_version:
            if Version(self.settings.compiler.version) < min_compiler_version:
                raise ConanInvalidConfiguration(
                    "pdfium needs at least compiler version {}".format(min_compiler_version)
                )

    def source(self):
        get(
            self,
            **self.conan_data["sources"][self.version]["pdfium-cmake"],
            destination="pdfium-cmake",
            strip_root=True
        )
        get(self, **self.conan_data["sources"][self.version]["pdfium"], destination=self.source_folder)
        get(
            self,
            **self.conan_data["sources"][self.version]["trace_event"],
            destination=os.path.join(self.source_folder, "base", "trace_event", "common")
        )
        get(
            self,
            **self.conan_data["sources"][self.version]["chromium_build"],
            destination=os.path.join(self.source_folder, "build")
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["PDFIUM_ROOT"] = self.source_folder.replace("\\", "/")
        tc.variables["PDF_LIBJPEG_TURBO"] = self.options.with_libjpeg == "libjpeg-turbo"
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="pdfium-cmake/cmake")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["pdfium"]
        if is_apple_os(self.settings.os):
            self.cpp_info.frameworks.extend(["Appkit", "CoreFoundation", "CoreGraphics"])

        stdcpp_library = stdcpp_library(self)
        if stdcpp_library:
            self.cpp_info.system_libs.append(stdcpp_library)
