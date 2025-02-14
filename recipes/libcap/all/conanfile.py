import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import cross_building
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, chdir, export_conandata_patches, get, rmdir
from conan.tools.gnu import Autotools, GnuToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path

required_conan_version = ">=2.3.0"


class LibcapConan(ConanFile):
    name = "libcap"
    license = "BSD-3-Clause OR GPL-2.0-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://git.kernel.org/pub/scm/libs/libcap/libcap.git"
    description = "This is a library for getting and setting POSIX.1e" \
                  " (formerly POSIX 6) draft 15 capabilities"
    topics = ("capabilities",)
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "psx_syscals": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "psx_syscals": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(f"{self.name} only supports Linux")

    def build_requirements(self):
        if cross_building(self):
            # Get arch-specific objcopy
            self.tool_requires("binutils/2.42")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = GnuToolchain(self)
        tc.extra_env.define("SHARED", "yes" if self.options.shared else "no")
        tc.extra_env.define("PTHREADS", "yes" if self.options.psx_syscals else "no")
        tc.extra_env.define_path("DESTDIR", self.package_folder)
        tc.extra_env.define_path("prefix", "/")
        tc.extra_env.define_path("lib", "lib")
        if cross_building(self):
            # libcap needs to run an executable that is compiled from sources
            # during the build - so it needs a native compiler (it doesn't matter which)
            tc.extra_env.define_path("BUILD_CC", tc.extra_env.vars(self).get("CC_FOR_BUILD", "cc")
            triplet = self.dependencies.build["binutils"].conf_info.get("user.binutils:gnu_triplet", check_type=str)
            binutils_dir = os.path.join(self.dependencies.build["binutils"].package_folder, "bin")
            tc.extra_env.define_path("OBJCOPY", unix_path(self, os.path.join(binutils_dir, f"{triplet}-objcopy")))
        tc.generate()

        # Ugly workaround for binutils/*:add_unprefixed_to_path=False having no effect
        venv = VirtualBuildEnv(self)
        env = venv.environment()
        path = env.vars(self).get("PATH")
        if path and "exec_prefix" in path:
            env.define("PATH", path.replace("exec_prefix", "exec_prefix_skip"))
        venv.generate()

    def build(self):
        autotools = Autotools(self)
        with chdir(self, os.path.join(self.source_folder, "libcap")):
            autotools.make()

    def package(self):
        copy(self, "License", self.source_folder, os.path.join(self.package_folder, "licenses"))

        autotools = Autotools(self)
        with chdir(self, os.path.join(self.source_folder, "libcap")):
            autotools.make(target="install-common-cap")
            install_cap = ("install-shared-cap" if self.options.shared
                           else "install-static-cap")
            autotools.make(target=install_cap)

            if self.options.psx_syscals:
                autotools.make(target="install-common-psx")
                install_psx = ("install-shared-psx" if self.options.shared
                               else "install-static-psx")
                autotools.make(target=install_psx)

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.components["cap"].set_property("pkg_config_name", "libcap")
        self.cpp_info.components["cap"].libs = ["cap"]
        if self.options.psx_syscals:
            self.cpp_info.components["psx"].set_property("pkg_config_name", "libpsx")
            self.cpp_info.components["psx"].libs = ["psx"]
            self.cpp_info.components["psx"].system_libs = ["pthread"]
            self.cpp_info.components["psx"].exelinkflags = ["-Wl,-wrap,pthread_create"]
            # trick to avoid conflicts with cap component
            self.cpp_info.set_property("pkg_config_name", "libcap-do-not-use")
