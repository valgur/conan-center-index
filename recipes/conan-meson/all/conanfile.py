from pathlib import Path

from conan import ConanFile
from conan.tools.files import rename

required_conan_version = ">=2.1"


class ConanMesonPackage(ConanFile):
    name = "conan-meson"
    version = "latest"
    description = "Conan helper for functions for Meson-based projects"
    license = "MIT"
    package_type = "python-require"


class MesonUtils:
    def fix_msvc_libnames(self: ConanFile, extensions=None, remove_lib_prefix=True):
        """
        Rename all lib*.a files built by Meson to *.lib files when using a cl-like compiler on Windows.

        See https://github.com/mesonbuild/meson/issues/8153 for context.
        """
        fix_msvc_libnames(self, extensions, remove_lib_prefix)


def fix_msvc_libnames(conanfile: ConanFile, extensions=None, remove_lib_prefix=True):
    if not conanfile.settings.os == "Windows":
        return
    if conanfile.settings.compiler == "msvc" or conanfile.settings.get_safe("compiler.runtime"):
        _fix_libnames(conanfile, conanfile.package_folder, extensions, remove_lib_prefix)


def _fix_libnames(conanfile: ConanFile, lib_dir, extensions=None, remove_lib_prefix=True):
    extensions = extensions or [".a"]
    for ext in extensions:
        for lib_path in sorted(Path(lib_dir).rglob(f"*{ext}")):
            libname = lib_path.name[0:-len(ext)]
            if remove_lib_prefix and libname.startswith("lib"):
                libname = libname[3:]
            rename(conanfile, lib_path, lib_path.parent / f"{libname}.lib")
