import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, rm, rmdir, replace_in_file, load
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain
from conan.tools.microsoft import is_msvc_static_runtime, is_msvc
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class GrapheneConan(ConanFile):
    name = "graphene"
    description = "A thin layer of graphic data types."
    topics = ("graphic", "canvas", "types")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://ebassi.github.io/graphene/"
    license = "MIT"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_glib": [True, False],
        "with_introspection": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_glib": True,
        "with_introspection": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")
        if self.options.shared and self.options.with_glib:
            self.options["glib"].shared = True
        if not self.options.with_glib:
            del self.options.with_introspection

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_glib:
            self.requires("glib/2.78.3")

    def validate(self):
        if self.settings.compiler == "gcc":
            if Version(self.settings.compiler.version) < "5.0":
                raise ConanInvalidConfiguration("graphene does not support GCC before 5.0")

        if self.options.with_glib:
            glib_is_shared = self.dependencies["glib"].options.shared
            if self.options.shared and not glib_is_shared:
                raise ConanInvalidConfiguration(
                    "Linking a shared library against static glib can cause unexpected behaviour."
                )
            if glib_is_shared and is_msvc_static_runtime(self):
                raise ConanInvalidConfiguration(
                    "Linking shared glib with the MSVC static runtime is not supported"
                )

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", default=False):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if self.options.get_safe("with_introspection"):
            self.tool_requires("gobject-introspection/1.78.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()

        deps = PkgConfigDeps(self)
        if self.options.get_safe("with_introspection"):
            deps.build_context_activated = ["gobject-introspection"]
        deps.generate()

        meson = MesonToolchain(self)
        meson.project_options.update({
            "tests": "false",
            "installed_tests": "false",
            "gtk_doc": "false",
        })
        meson.project_options["gobject_types"] = "true" if self.options.with_glib else "false"
        if Version(self.version) < "1.10.4":
            meson.project_options["introspection"] = "true" if self.options.get_safe("with_introspection") else "false"
        else:
            meson.project_options["introspection"] =  "enabled" if self.options.get_safe("with_introspection") else "disabled"
        meson.generate()

    def _patch_sources(self):
        # The finite-math-only optimization has no effect and can cause linking errors
        # when linked against glibc >= 2.31
        replace_in_file(self, os.path.join(self.source_folder, "meson.build"),
                        "'-ffast-math'",
                        "'-ffast-math', '-fno-finite-math-only'")

    def build(self):
        self._patch_sources()
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        if self.options.get_safe("with_introspection"):
            os.rename(os.path.join(self.package_folder, "share"),
                      os.path.join(self.package_folder, "res"))
        rm(self, "*.pdb", self.package_folder, recursive=True)
        fix_apple_shared_install_name(self)
        fix_msvc_libname(self)

    def _get_simd_config(self):
        config = load(self, os.path.join(self.package_folder, "lib", "graphene-1.0", "include", "graphene-config.h"))
        return {
            "sse2": "GRAPHENE_HAS_SSE 1" in config,
            "gcc": "GRAPHENE_HAS_GCC 1" in config,
            "neon": "GRAPHENE_HAS_ARM_NEON 1" in config,
            "scalar": "GRAPHENE_HAS_SCALAR 1" in config,
        }

    def package_info(self):
        self.cpp_info.components["graphene-1.0"].set_property("pkg_config_name", "graphene-1.0")
        self.cpp_info.components["graphene-1.0"].libs = ["graphene-1.0"]
        self.cpp_info.components["graphene-1.0"].includedirs = [os.path.join("include", "graphene-1.0"), os.path.join("lib", "graphene-1.0", "include")]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["graphene-1.0"].system_libs = ["m", "pthread"]
        if self.options.with_glib:
            self.cpp_info.components["graphene-1.0"].requires = ["glib::gobject-2.0"]

        if self.options.get_safe("with_introspection"):
            self.cpp_info.components["graphene-1.0"].resdirs = ["res"]
            self.buildenv_info.append_path("GI_GIR_PATH", os.path.join(self.package_folder, "res", "gir-1.0"))
            self.buildenv_info.append_path("GI_TYPELIB_PATH", os.path.join(self.package_folder, "lib", "girepository-1.0"))
            self.env_info.GI_GIR_PATH.append(os.path.join(self.package_folder, "res", "gir-1.0"))
            self.env_info.GI_TYPELIB_PATH.append(os.path.join(self.package_folder, "lib", "girepository-1.0"))

        simd = self._get_simd_config()
        if simd["sse2"]:
            # https://salsa.debian.org/gnome-team/graphene/-/blob/1.10.0/meson.build?ref_type=tags#L274
            if not is_msvc(self):
                self.cpp_info.components["graphene-1.0"].cflags = ["-mfpmath=sse", "-msse", "-msse2"]
        elif simd["neon"]:
            # https://salsa.debian.org/gnome-team/graphene/-/blob/1.10.0/meson.build?ref_type=tags#L339-343
            if not is_msvc(self):
                if self.settings.os == "Android":
                    self.cpp_info.components["graphene-1.0"].cflags.append("-mfloat-abi=softfp")

        if self.options.with_glib:
            self.cpp_info.components["graphene-gobject-1.0"].set_property("pkg_config_name","graphene-gobject-1.0")
            self.cpp_info.components["graphene-gobject-1.0"].includedirs = [os.path.join("include", "graphene-1.0")]
            self.cpp_info.components["graphene-gobject-1.0"].requires = ["graphene-1.0", "glib::gobject-2.0"]
            # https://salsa.debian.org/gnome-team/graphene/-/blob/1.10.0/src/meson.build?ref_type=tags#L79-93
            simd_info = "\n".join(f"graphene_has_{k}={int(v)}" for k, v in simd.items())
            self.cpp_info.components["graphene-gobject-1.0"].set_property("pkg_config_custom_content", simd_info)

def fix_msvc_libname(conanfile, remove_lib_prefix=True):
    """remove lib prefix & change extension to .lib in case of cl like compiler"""
    from conan.tools.files import rename
    import glob
    if not conanfile.settings.get_safe("compiler.runtime"):
        return
    libdirs = getattr(conanfile.cpp.package, "libdirs")
    for libdir in libdirs:
        for ext in [".dll.a", ".dll.lib", ".a"]:
            full_folder = os.path.join(conanfile.package_folder, libdir)
            for filepath in glob.glob(os.path.join(full_folder, f"*{ext}")):
                libname = os.path.basename(filepath)[0:-len(ext)]
                if remove_lib_prefix and libname[0:3] == "lib":
                    libname = libname[3:]
                rename(conanfile, filepath, os.path.join(os.path.dirname(filepath), f"{libname}.lib"))
