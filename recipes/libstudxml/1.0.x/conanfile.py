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

required_conan_version = ">=1.53.0"


class LibStudXmlConan(ConanFile):
    name = "libstudxml"
    description = (
        "A streaming XML pull parser and streaming XML serializer implementation for modern, standard C++."
    )
    topics = ("xml", "xml-parser", "serialization")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.codesynthesis.com/projects/libstudxml/"
    license = "MIT"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    _autotools = None

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

    def layout(self):
        pass

    def requirements(self):
        self.requires("expat/2.5.0", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if (
            self.info.settings.compiler == "Visual Studio"
            and Version(self.info.settings.compiler.version) < "9"
        ):
            raise ConanInvalidConfiguration(
                f"Visual Studio {self.info.settings.compiler.version} is not supported."
            )

    def build_requirements(self):
        if not is_msvc(self):
            self.tool_requires("gnu-config/cci.20210814")
            self.tool_requires("libtool/2.4.7")
            if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
                self.tool_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _configure_autotools(self):
        if not self._autotools:
            args = ["--with-external-expat"]
            if self.options.shared:
                args.extend(["--enable-shared", "--disable-static"])
            else:
                args.extend(["--disable-shared", "--enable-static"])

            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            self._autotools.configure(configure_dir=self.source_folder, args=args)
        return self._autotools

    @property
    def _vc_ver(self):
        if self.settings.compiler == "Visual Studio":
            return str(Version(self.settings.compiler.version).major)
        elif self.settings.compiler == "msvc":
            return {
                "170": "11",
                "180": "12",
                "190": "14",
                "191": "15",
                "192": "16",
                "193": "17",
            }[str(self.settings.compiler.version)]
        return None

    def _build_vs(self):
        vc_ver = int(self._vc_ver)
        sln_path = None

        def get_sln_path():
            return os.path.join(self.source_folder, f"libstudxml-vc{vc_ver}.sln")

        sln_path = get_sln_path()
        while not os.path.exists(sln_path):
            vc_ver -= 1
            sln_path = get_sln_path()

        proj_path = os.path.join(self.source_folder, "xml", f"libstudxml-vc{vc_ver}.vcxproj")

        if not self.options.shared:
            replace_in_file(self, proj_path, "DynamicLibrary", "StaticLibrary")
            replace_in_file(self, proj_path, "LIBSTUDXML_DYNAMIC_LIB", "LIBSTUDXML_STATIC_LIB")

        msbuild = MSBuild(self)
        msbuild.build(
            sln_path,
            platforms={
                "x86": "Win32",
            },
        )

    def _build_autotools(self):
        for gnu_config in [
            self.conf.get("user.gnu-config:config_guess", check_type=str),
            self.conf.get("user.gnu-config:config_sub", check_type=str),
        ]:
            if gnu_config:
                copy(
                    self,
                    os.path.basename(gnu_config),
                    src=os.path.dirname(gnu_config),
                    dst=os.path.join(self.source_folder, "config"),
                )

        if self.settings.compiler.get_safe("libcxx") == "libc++":
            # libc++ includes a file called 'version', and since libstudxml adds source_subfolder as an
            # include dir, libc++ ends up including their 'version' file instead, causing a compile error
            rm(self, "version", self.source_folder)

        with chdir(self, self.source_folder):
            self.run("{} -fiv".format(get_env(self, "AUTORECONF")), win_bash=tools.os_info.is_windows)

        autotools = self._configure_autotools()
        autotools.make()

    def build(self):
        apply_conandata_patches(self)
        if is_msvc(self):
            self._build_vs()
        else:
            self._build_autotools()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if is_msvc(self):
            copy(
                self,
                "xml/value-traits",
                dst=os.path.join(self.package_folder, "include"),
                src=self.source_folder,
            )
            copy(
                self,
                "xml/serializer",
                dst=os.path.join(self.package_folder, "include"),
                src=self.source_folder,
            )
            copy(self, "xml/qname", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
            copy(self, "xml/parser", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
            copy(
                self, "xml/forward", dst=os.path.join(self.package_folder, "include"), src=self.source_folder
            )
            copy(
                self,
                "xml/exception",
                dst=os.path.join(self.package_folder, "include"),
                src=self.source_folder,
            )
            copy(
                self, "xml/content", dst=os.path.join(self.package_folder, "include"), src=self.source_folder
            )
            copy(self, "xml/*.ixx", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
            copy(self, "xml/*.txx", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
            copy(self, "xml/*.hxx", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
            copy(self, "xml/*.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)

            suffix = ""
            if self.settings.arch == "x86_64":
                suffix = "64"
            if self.options.shared:
                copy(
                    self,
                    "*.lib",
                    dst=os.path.join(self.package_folder, "lib"),
                    src=os.path.join(self.source_folder, "lib" + suffix),
                )
                copy(
                    self,
                    "*.dll",
                    dst=os.path.join(self.package_folder, "bin"),
                    src=os.path.join(self.source_folder, "bin" + suffix),
                )
            else:
                copy(
                    self,
                    "*.lib",
                    dst=os.path.join(self.package_folder, "lib"),
                    src=os.path.join(self.source_folder, "bin" + suffix),
                )
        else:
            autotools = self._configure_autotools()
            autotools.install()
            rm(self, "*.la", os.path.join(self.package_folder, "lib"))
            rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
            rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "libstudxml")
        self.cpp_info.libs = collect_libs(self)

        # If built with makefile, static library mechanism is provided by their buildsystem already
        if is_msvc(self) and not self.options.shared:
            self.cpp_info.defines = ["LIBSTUDXML_STATIC_LIB=1"]
