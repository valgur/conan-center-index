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
import shutil

required_conan_version = ">=1.53.0"


class MpdecimalConan(ConanFile):
    name = "mpdecimal"
    description = (
        "mpdecimal is a package for correctly-rounded arbitrary precision decimal floating point arithmetic."
    )
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.bytereef.org/mpdecimal"
    topics = ("multiprecision", "library")

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

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if is_msvc(self) and self.settings.arch not in ("x86", "x86_64"):
            raise ConanInvalidConfiguration("Arch is unsupported")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # TODO: fill in generate()
        pass

    def _patch_sources(self):
        apply_conandata_patches(self)
        if not is_msvc(self):
            """
            Using autotools:
            - Build only shared libraries when shared == True
            - Build only static libraries when shared == False
            ! This is more complicated on Windows because when shared=True, an implicit static library has to be built
            """

            shared_ext = self._shared_ext_mapping[str(self.settings.os)]
            static_ext = ".a"
            main_version, _ = self.version.split(".", 1)

            replace_in_file(
                self,
                os.path.join(self.source_folder, "configure"),
                "libmpdec.a",
                "libmpdec{}".format(static_ext),
            )
            replace_in_file(
                self,
                os.path.join(self.source_folder, "configure"),
                "libmpdec.so",
                "libmpdec{}".format(shared_ext),
            )

            makefile_in = os.path.join(self.source_folder, "Makefile.in")
            mpdec_makefile_in = os.path.join(self.source_folder, "libmpdec", "Makefile.in")
            replace_in_file(self, makefile_in, "libdir = @libdir@", "libdir = @libdir@\nbindir = @bindir@")
            if self.options.shared:
                if self.settings.os == "Windows":
                    replace_in_file(
                        self,
                        makefile_in,
                        "LIBSHARED = @LIBSHARED@",
                        "LIBSHARED = libmpdec-{}{}".format(main_version, shared_ext),
                    )
                    replace_in_file(
                        self,
                        makefile_in,
                        "install: FORCE",
                        "install: FORCE\n\t$(INSTALL) -d -m 755 $(DESTDIR)$(bindir)",
                    )
                    replace_in_file(
                        self,
                        makefile_in,
                        "\t$(INSTALL) -m 755 libmpdec/$(LIBSHARED) $(DESTDIR)$(libdir)\n",
                        "\t$(INSTALL) -m 755 libmpdec/$(LIBSHARED) $(DESTDIR)$(bindir)\n",
                    )
                    replace_in_file(
                        self,
                        makefile_in,
                        (
                            "\tcd $(DESTDIR)$(libdir) && ln -sf $(LIBSHARED) $(LIBSONAME) && ln -sf"
                            " $(LIBSHARED) libmpdec.so\n"
                        ),
                        "",
                    )
                else:
                    replace_in_file(
                        self,
                        makefile_in,
                        "\t$(INSTALL) -m 644 libmpdec/$(LIBSTATIC) $(DESTDIR)$(libdir)\n",
                        "",
                    )
                    replace_in_file(
                        self,
                        makefile_in,
                        (
                            "\tcd $(DESTDIR)$(libdir) && ln -sf $(LIBSHARED) $(LIBSONAME) && ln -sf"
                            " $(LIBSHARED) libmpdec.so"
                        ),
                        "\tcd $(DESTDIR)$(libdir) && ln -sf $(LIBSHARED) $(LIBSONAME) && ln -sf $(LIBSHARED)"
                        " libmpdec{}".format(shared_ext),
                    )
            else:
                replace_in_file(
                    self, makefile_in, "\t$(INSTALL) -m 755 libmpdec/$(LIBSHARED) $(DESTDIR)$(libdir)\n", ""
                )
                replace_in_file(
                    self,
                    makefile_in,
                    (
                        "\tcd $(DESTDIR)$(libdir) && ln -sf $(LIBSHARED) $(LIBSONAME) && ln -sf $(LIBSHARED)"
                        " libmpdec.so\n"
                    ),
                    "",
                )

            replace_in_file(
                self,
                mpdec_makefile_in,
                "default: $(LIBSTATIC) $(LIBSHARED)",
                "default: $({})".format("LIBSHARED" if self.options.shared else "LIBSTATIC"),
            )

            if self.settings.os == "Windows":
                replace_in_file(
                    self,
                    mpdec_makefile_in,
                    "LIBSHARED = @LIBSHARED@",
                    "LIBSHARED = libmpdec-{}{}".format(main_version, shared_ext),
                )
                replace_in_file(self, mpdec_makefile_in, "\tln -sf $(LIBSHARED) libmpdec.so", "")
                replace_in_file(self, mpdec_makefile_in, "\tln -sf $(LIBSHARED) $(LIBSONAME)", "")
                replace_in_file(
                    self,
                    mpdec_makefile_in,
                    "CONFIGURE_LDFLAGS =",
                    "CONFIGURE_LDFLAGS = -Wl,--out-implib,libmpdec{}".format(static_ext),
                )
            else:
                replace_in_file(self, mpdec_makefile_in, "libmpdec.so", "libmpdec{}".format(shared_ext))

    def _build_msvc(self):
        libmpdec_folder = os.path.join(self.build_folder, self.source_folder, "libmpdec")
        vcbuild_folder = os.path.join(self.build_folder, self.source_folder, "vcbuild")
        arch_ext = "{}".format(32 if self.settings.arch == "x86" else 64)
        dist_folder = os.path.join(vcbuild_folder, "dist{}".format(arch_ext))
        os.mkdir(dist_folder)

        shutil.copy(os.path.join(libmpdec_folder, "Makefile.vc"), os.path.join(libmpdec_folder, "Makefile"))

        autotools = AutoToolsBuildEnvironment(self)

        with chdir(self, libmpdec_folder):
            with vcvars(self.settings):
                self.run(
                    """nmake /nologo MACHINE={machine} DLL={dll} CONAN_CFLAGS="{cflags}" CONAN_LDFLAGS="{ldflags}" """.format(
                        machine="ppro" if self.settings.arch == "x86" else "x64",
                        dll="1" if self.options.shared else "0",
                        cflags=" ".join(autotools.flags),
                        ldflags=" ".join(autotools.link_flags),
                    )
                )

            shutil.copy("mpdecimal.h", dist_folder)
            if self.options.shared:
                shutil.copy(
                    "libmpdec-{}.dll".format(self.version),
                    os.path.join(dist_folder, "libmpdec-{}.dll".format(self.version)),
                )
                shutil.copy(
                    "libmpdec-{}.dll.exp".format(self.version),
                    os.path.join(dist_folder, "libmpdec-{}.exp".format(self.version)),
                )
                shutil.copy(
                    "libmpdec-{}.dll.lib".format(self.version),
                    os.path.join(dist_folder, "libmpdec-{}.lib".format(self.version)),
                )
            else:
                shutil.copy("libmpdec-{}.lib".format(self.version), dist_folder)

    def _configure_autotools(self):
        tc = AutotoolsToolchain(self)
        if self.settings.os == "Macos" and self.settings.arch == "armv8":
            tc.ldflags.append("-arch arm64")
        tc.generate()

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            self._build_msvc()
        else:
            with chdir(self, self.source_folder):
                autotools = Autotools(self)
                autotools.configure()
                autotools.make()

    def package(self):
        copy(self, "LICENSE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if is_msvc(self):
            distfolder = os.path.join(
                self.build_folder,
                self.source_folder,
                "vcbuild",
                "dist{}".format(32 if self.settings.arch == "x86" else 64),
            )
            copy(
                self,
                "vc*.h",
                src=os.path.join(self.build_folder, self.source_folder, "libmpdec"),
                dst=os.path.join(self.package_folder, "include"),
            )
            copy(self, "*.h", src=distfolder, dst=os.path.join(self.package_folder, "include"))
            copy(self, "*.lib", src=distfolder, dst=os.path.join(self.package_folder, "lib"))
            copy(self, "*.dll", src=distfolder, dst=os.path.join(self.package_folder, "bin"))
        else:
            with chdir(self, os.path.join(self.build_folder, self.source_folder)):
                autotools = Autotools(self)
                autotools.install()
            rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        if is_msvc(self):
            self.cpp_info.libs = ["libmpdec-{}".format(self.version)]
        else:
            self.cpp_info.libs = ["mpdec"]
        if self.options.shared:
            if is_msvc(self):
                self.cpp_info.defines = ["USE_DLL"]
        else:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m"]
