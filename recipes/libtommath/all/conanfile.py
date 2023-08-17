import os

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, chdir, copy, export_conandata_patches, get
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import VCVars, is_msvc

required_conan_version = ">=1.53.0"


class LibTomMathConan(ConanFile):
    name = "libtommath"
    description = (
        "LibTomMath is a free open source portable number theoretic "
        "multiple-precision integer library written entirely in C."
    )
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.libtom.net/"
    topics = ("libtommath", "math", "multiple", "precision")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        if self._settings_build.os == "Windows" and not is_msvc(self):
            if not self.conf.get("tools.gnu:make_program", check_type=str):
                self.tool_requires("make/4.3")
        if not is_msvc(self) and self.settings.os != "Windows" and self.options.shared:
            self.tool_requires("libtool/2.4.7")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()
        tc = AutotoolsToolchain(self)
        if self.settings.os == "Windows" and not is_msvc(self):
            tc.extra_ldflags.append("-lcrypt32")
        if is_apple_os(self) and self.settings.arch == "armv8":
            # FIXME: should be handled by helper
            tc.extra_ldflags.append("-arch arm64")
        tc.generate()
        if is_msvc(self):
            vcvars = VCVars(self)
            vcvars.generate()

    def build(self):
        apply_conandata_patches(self)
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            if is_msvc(self):
                if self.options.shared:
                    target = "tommath.dll"
                else:
                    target = "tommath.lib"
                autotools.make(target, args=["-f", "makefile.msvc"])
            else:
                target = None
                if self.settings.os == "Windows":
                    makefile = "makefile.mingw"
                    if self.options.shared:
                        target = "libtommath.dll"
                    else:
                        target = "libtommath.a"
                else:
                    if self.options.shared:
                        makefile = "makefile.shared"
                    else:
                        makefile = "makefile.unix"
                autotools.make(target, args=["-f", makefile])

    def package(self):
        copy(self, "LICENSE",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        for pattern in ["*.a", "*.so*", "*.lib", "*.dylib"]:
            copy(self, pattern,
                 src=self.source_folder,
                 dst=os.path.join(self.package_folder, "lib"))
        copy(self, "*.dll",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "bin"))
        copy(self, "tommath.h",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "include"))

        if is_msvc(self) and self.options.shared:
            os.rename(
                os.path.join(self.package_folder, "lib", "tommath.dll.lib"),
                os.path.join(self.package_folder, "lib", "tommath.lib"),
            )

    def package_info(self):
        self.cpp_info.libs = ["tommath"]
        if not self.options.shared:
            if self.settings.os == "Windows":
                self.cpp_info.system_libs = ["advapi32", "crypt32"]

        self.cpp_info.set_property("pkg_config_name", "libtommath")
