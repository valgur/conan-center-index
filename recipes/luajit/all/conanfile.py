import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import cross_building
from conan.tools.files import get, chdir, replace_in_file, copy, rmdir, export_conandata_patches, apply_conandata_patches
from conan.tools.gnu import Autotools, GnuToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, MSBuildToolchain, unix_path
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class LuajitConan(ConanFile):
    name = "luajit"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://luajit.org"
    description = "LuaJIT is a Just-In-Time Compiler (JIT) for the Lua programming language."
    topics = ("lua", "jit")
    provides = "lua"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    languages = ["C"]
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os == "Macos" and self.settings.arch == "armv8" and cross_building(self):
            raise ConanInvalidConfiguration(f"{self.ref} can not be cross-built to Mac M1. Please, try any version >=2.1")
        elif Version(self.version) <= "2.1.0-beta1" and self.settings.os == "Macos" and self.settings.arch == "armv8":
            raise ConanInvalidConfiguration(f"{self.ref} is not supported by Mac M1. Please, try any version >=2.1")

    def source(self):
        filename = f"LuaJIT-{self.version}.tar.gz"
        get(self, **self.conan_data["sources"][self.version], filename=filename, strip_root=True)
        apply_conandata_patches(self)

    @property
    def _target_sys(self):
        if self.settings.os == "iOS":
            return "iOS"
        if is_apple_os(self):
            return "Darwin"
        return {
            "Linux": "Linux",
            "FreeBSD": "GNU/kFreeBSD",
            "SunOS": "SunOS",
            "Windows": "Windows",
        }.get(str(self.settings.os), "Linux")

    def generate(self):
        if is_msvc(self):
            tc = MSBuildToolchain(self)
            tc.generate()
        else:
            tc = GnuToolchain(self)
            tc.make_args["PREFIX"] = unix_path(self, self.package_folder)
            tc.make_args["BUILDMODE"] = "shared" if self.options.shared else "static"
            tc_vars = tc.extra_env.vars(self)
            cc = tc_vars["CC"]
            if cross_building(self):
                tc.make_args["HOST_CC"] = tc_vars.get("CC_FOR_BUILD", "cc")
                cross = tc_vars["STRIP"].replace("-strip", "-")
                tc.make_args["CROSS"] = cross
                # The makefile prepends the cross prefix to the CC variable
                cc = cc.replace(cross, "")
                cc = cc.replace(os.path.basename(cross), "")
                if self.settings.os != self.settings_build.os:
                    tc.make_args["TARGET_SYS"] = self._target_sys
            tc.make_args["CC"] = cc
            if is_apple_os(self) and self.settings.get_safe("os.version"):
                tc.make_args["MACOSX_DEPLOYMENT_TARGET"] = self.settings.os.version
            tc.generate()

    def _patch_sources(self):
        if not is_msvc(self):
            makefile = os.path.join(self.source_folder, 'src', 'Makefile')
            replace_in_file(self, makefile,
                                  'TARGET_DYLIBPATH= $(TARGET_LIBPATH)/$(TARGET_DYLIBNAME)',
                                  'TARGET_DYLIBPATH= $(TARGET_DYLIBNAME)')
            # adjust mixed mode defaults to build either .so or .a, but not both
            if not self.options.shared:
                replace_in_file(self, makefile,
                                      'TARGET_T= $(LUAJIT_T) $(LUAJIT_SO)',
                                      'TARGET_T= $(LUAJIT_T) $(LUAJIT_A)')
                replace_in_file(self, makefile,
                                      'TARGET_DEP= $(LIB_VMDEF) $(LUAJIT_SO)',
                                      'TARGET_DEP= $(LIB_VMDEF) $(LUAJIT_A)')
            else:
                replace_in_file(self, makefile,
                                      'TARGET_O= $(LUAJIT_A)',
                                      'TARGET_O= $(LUAJIT_SO)')

    @property
    def _luajit_include_folder(self):
        luaversion = Version(self.version)
        if luaversion.major == "2":
            return f"luajit-{luaversion.major}.{luaversion.minor}"
        return "luajit-2.1"

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            with chdir(self, os.path.join(self.source_folder, "src")):
                variant = '' if self.options.shared else 'static'
                self.run(f"msvcbuild.bat {variant}", env="conanbuild")
        else:
            with chdir(self, self.source_folder):
                autotools = Autotools(self)
                autotools.make()

    def package(self):
        copy(self, "COPYRIGHT", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        src_folder = os.path.join(self.source_folder, "src")
        include_folder = os.path.join(self.package_folder, "include", self._luajit_include_folder)
        if is_msvc(self):
            copy(self, "lua.h", src=src_folder, dst=include_folder)
            copy(self, "lualib.h", src=src_folder, dst=include_folder)
            copy(self, "lauxlib.h", src=src_folder, dst=include_folder)
            copy(self, "luaconf.h", src=src_folder, dst=include_folder)
            copy(self, "lua.hpp", src=src_folder, dst=include_folder)
            copy(self, "luajit.h", src=src_folder, dst=include_folder)
            copy(self, "lua51.lib", src=src_folder, dst=os.path.join(self.package_folder, "lib"))
            copy(self, "lua51.dll", src=src_folder, dst=os.path.join(self.package_folder, "bin"))
        else:
            with chdir(self, self.source_folder):
                autotools = Autotools(self)
                autotools.install(args=["DESTDIR="])
            rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
            rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["lua51" if is_msvc(self) else "luajit-5.1"]
        self.cpp_info.set_property("pkg_config_name", "luajit")
        self.cpp_info.includedirs = [os.path.join("include", self._luajit_include_folder)]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "dl"])
