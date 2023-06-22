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


class EazylzmaConan(ConanFile):
    name = "easylzma"
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/lloyd/easylzma"
    description = "An easy to use, tiny, public domain, C wrapper library around \
                    Igor Pavlov's work that can be used to compress and extract lzma files"
    settings = "os", "arch", "compiler", "build_type"
    topics = ("eazylzma", "lzma")
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    @property
    def _license_text(self):
        # Extract the License/s from the README to a file
        tmp = load(self, os.path.join("source_subfolder", "README"))
        return tmp[tmp.find("License", 1) : tmp.find("work.", 1) + 5]

    @property
    def _libname(self):
        return "easylzma" if self.options.shared else "easylzma_s"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build(target=self._libname)

    def package(self):
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), self._license_text)

        copy(
            self,
            pattern="*.dylib*",
            dst=os.path.join(self.package_folder, "lib"),
            src="lib",
            keep_path=False,
            symlinks=True,
        )
        copy(
            self,
            pattern="*.so*",
            dst=os.path.join(self.package_folder, "lib"),
            src="lib",
            keep_path=False,
            symlinks=True,
        )
        copy(self, pattern="*.dll", dst=os.path.join(self.package_folder, "bin"), src="bin", keep_path=False)
        copy(self, pattern="*.a", dst=os.path.join(self.package_folder, "lib"), src="lib", keep_path=False)
        copy(self, pattern="*.lib", dst=os.path.join(self.package_folder, "lib"), src="lib", keep_path=False)

        copy(
            self,
            "easylzma/*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "src"),
        )

    def package_info(self):
        self.cpp_info.libs = [self._libname]
        if self.options.shared:
            self.cpp_info.defines = ["EASYLZMA_SHARED"]
        if self.settings.compiler == "Visual Studio":
            if "d" in str(self.settings.compiler.runtime):
                self.cpp_info.defines.append("DEBUG")
