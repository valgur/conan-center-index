import os
import re
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.4"


class AprConan(ConanFile):
    name = "apr"
    description = (
        "The Apache Portable Runtime (APR) provides a predictable and consistent "
        "interface to underlying platform-specific implementations"
    )
    license = "Apache-2.0"
    topics = ("apache", "platform", "library")
    homepage = "https://apr.apache.org/"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "force_apr_uuid": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "force_apr_uuid": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        if is_msvc(self):
            cmake_layout(self, src_folder="src")
        else:
            basic_layout(self, src_folder="src")

    def requirements(self):
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.requires("libxcrypt/4.4.36", transitive_headers=True, transitive_libs=True)

    def build_requirements(self):
        if not is_msvc(self):
            if self.settings_build.os == "Windows":
                self.win_bash = True
                if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                    self.tool_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "CMAKE_MINIMUM_REQUIRED(VERSION 2.8)",
                        "CMAKE_MINIMUM_REQUIRED(VERSION 3.5)")

    def _get_cross_building_configure_args(self):
        if self.settings.os == "Linux":
            # Mandatory cross-building configuration flags (tested on Linux ARM and Intel)
            return [
                "apr_cv_mutex_robust_shared=yes",
                "ac_cv_file__dev_zero=yes",
                "apr_cv_process_shared_works=yes",
                "apr_cv_tcp_nodelay_with_cork=yes",
            ]
        return []

    def generate(self):
        if is_msvc(self):
            tc = CMakeToolchain(self)
            tc.variables["INSTALL_PDB"] = False
            tc.variables["APR_BUILD_TESTAPR"] = False
            tc.generate()
        else:
            env = VirtualBuildEnv(self)
            env.generate()
            tc = AutotoolsToolchain(self)
            tc.configure_args.append("--with-installbuilddir=${prefix}/res/build-1")
            if cross_building(self):
                tc.configure_args.extend(self._get_cross_building_configure_args())
            tc.generate()
            deps = AutotoolsDeps(self)
            deps.generate()

    def _patch_sources(self):
        if self.options.force_apr_uuid:
            replace_in_file(self, os.path.join(self.source_folder, "include", "apr.h.in"),
                                  "@osuuid@", "0")

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            cmake = CMake(self)
            cmake.configure()
            cmake.build(target="libapr-1" if self.options.shared else "apr-1")
        else:
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if is_msvc(self):
            cmake = CMake(self)
            cmake.install()
        else:
            autotools = Autotools(self)
            autotools.install()
            rm(self, "*.la", os.path.join(self.package_folder, "lib"))
            rmdir(self, os.path.join(self.package_folder, "build-1"))
            rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
            fix_apple_shared_install_name(self)

            apr_rules_mk = Path(self.package_folder, "res", "build-1", "apr_rules.mk")
            apr_rules_cnt = apr_rules_mk.read_text()
            for key in ("apr_builddir", "apr_builders", "top_builddir"):
                apr_rules_cnt, nb = re.subn(f"^{key}=[^\n]*\n", f"{key}=$(_APR_BUILDDIR)\n", apr_rules_cnt, flags=re.MULTILINE)
                if nb == 0:
                    raise ConanException(f"Could not find/replace {key} in {apr_rules_mk}")
            apr_rules_mk.write_text(apr_rules_cnt)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name",  "apr-1")
        prefix = "lib" if is_msvc(self) and self.options.shared else ""
        self.cpp_info.libs = [f"{prefix}apr-1"]
        self.cpp_info.resdirs = ["res"]
        if not self.options.shared:
            self.cpp_info.defines = ["APR_DECLARE_STATIC"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["dl", "pthread", "rt"]
            if self.settings.os == "Windows":
                self.cpp_info.system_libs = ["mswsock", "rpcrt4", "ws2_32"]
