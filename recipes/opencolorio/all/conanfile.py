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
import functools
import os

required_conan_version = ">=1.45.0"


class OpenColorIOConan(ConanFile):
    name = "opencolorio"
    description = "A color management framework for visual effects and animation."
    license = "BSD-3-Clause"
    homepage = "https://opencolorio.org/"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("colors", "visual", "effects", "animation")

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_sse": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "use_sse": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.arch not in ["x86", "x86_64"]:
            self.options.rm_safe("use_sse")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("expat/2.4.8")
        self.requires("openexr/2.5.7")
        self.requires("yaml-cpp/0.7.0")
        if Version(self.version) < "2.0.0":
            self.requires("tinyxml/2.6.2")
        else:
            self.requires("pystring/1.1.3")
        # for tools only
        self.requires("lcms/2.13.1")
        # TODO: add GLUT (needed for ociodisplay tool)

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)

        if Version(self.version) >= "2.1.0":
            tc.variables["OCIO_BUILD_PYTHON"] = False
        else:
            tc.variables["OCIO_BUILD_SHARED"] = self.options.shared
            tc.variables["OCIO_BUILD_STATIC"] = not self.options.shared
            tc.variables["OCIO_BUILD_PYGLUE"] = False

            tc.variables["USE_EXTERNAL_YAML"] = True
            tc.variables["USE_EXTERNAL_TINYXML"] = True
            tc.variables["USE_EXTERNAL_LCMS"] = True

        tc.variables["OCIO_USE_SSE"] = self.options.get_safe("use_sse", False)

        # openexr 2.x provides Half library
        tc.variables["OCIO_USE_OPENEXR_HALF"] = True

        tc.variables["OCIO_BUILD_APPS"] = True
        tc.variables["OCIO_BUILD_DOCS"] = False
        tc.variables["OCIO_BUILD_TESTS"] = False
        tc.variables["OCIO_BUILD_GPU_TESTS"] = False
        tc.variables["OCIO_USE_BOOST_PTR"] = False

        # avoid downloading dependencies
        tc.variables["OCIO_INSTALL_EXT_PACKAGE"] = "NONE"

        if is_msvc(self) and not self.options.shared:
            # define any value because ifndef is used
            tc.variables["OpenColorIO_SKIP_IMPORTS"] = True

        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

        for module in ("expat", "lcms2", "pystring", "yaml-cpp", "Imath"):
            remove_files_by_mask(
                self,
                os.path.join(self.source_folder, "share", "cmake", "modules"),
                "Find" + module + ".cmake",
            )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        if not self.options.shared:
            copy(
                self,
                "*",
                src=os.path.join(self.package_folder, "lib", "static"),
                dst=os.path.join(self.package_folder, "lib"),
            )
            rmdir(self, os.path.join(self.package_folder, "lib", "static"))

        rmdir(self, os.path.join(self.package_folder, "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        # nop for 2.x
        remove_files_by_mask(self.package_folder, "OpenColorIOConfig*.cmake")

        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"), recursive=True)

        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenColorIO")
        self.cpp_info.set_property("cmake_target_name", "OpenColorIO::OpenColorIO")
        self.cpp_info.set_property("pkg_config_name", "OpenColorIO")

        self.cpp_info.libs = ["OpenColorIO"]

        if Version(self.version) < "2.1.0":
            if not self.options.shared:
                self.cpp_info.defines.append("OpenColorIO_STATIC")

        if self.settings.os == "Macos":
            self.cpp_info.frameworks.extend(["Foundation", "IOKit", "ColorSync", "CoreGraphics"])

        if is_msvc(self) and not self.options.shared:
            self.cpp_info.defines.append("OpenColorIO_SKIP_IMPORTS")

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH env var with: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)

        # TODO: to remove in conan v2 once cmake_find_package_* & pkg_config generators removed
        self.cpp_info.names["cmake_find_package"] = "OpenColorIO"
        self.cpp_info.names["cmake_find_package_multi"] = "OpenColorIO"
        self.cpp_info.names["pkg_config"] = "OpenColorIO"
