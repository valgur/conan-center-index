import os
import textwrap

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name, is_apple_os
from conan.tools.build import can_run
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class LibxlsConan(ConanFile):
    name = "libxls"
    description = "a C library which can read Excel (xls) files."
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/libxls/libxls/"
    topics = ("excel", "xls")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_cli": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_cli": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if not is_apple_os(self):
            self.requires("libiconv/[^1.17]")

    def validate(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration(f"{self.ref} doesn't support Visual Studio (yet). Contributions are always welcomed")

    def build_requirements(self):
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()
        if can_run(self):
            env = VirtualRunEnv(self)
            env.generate(scope="build")
        tc = AutotoolsToolchain(self)
        if not can_run(self):
            tc.configure_args.append("ac_cv_func_malloc_0_nonnull=yes")
            tc.configure_args.append("ac_cv_func_realloc_0_nonnull=yes")
        tc.generate()
        deps = AutotoolsDeps(self)
        deps.generate()

    def _patch_sources(self):
        config_h_content = textwrap.dedent(f"""
            #define HAVE_ICONV 1
            #define ICONV_CONST
            #define PACKAGE_VERSION "{self.version}"
            """)
        if self.settings.os == "Macos":
            config_h_content += "#define HAVE_XLOCALE_H 1\n"
        save(self, os.path.join(self.source_folder, "include", "config.h"), config_h_content)

    def build(self):
        self._patch_sources()
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "libxls")
        self.cpp_info.libs = ["xlsreader"]
        if is_apple_os(self):
            self.cpp_info.system_libs.append("iconv")
