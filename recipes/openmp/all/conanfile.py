from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class PackageConan(ConanFile):
    name = "openmp"
    description = "Conan meta-package for OpenMP (Open Multi-Processing)"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.openmp.org/"
    topics = ("parallelism", "multiprocessing")

    # package_type = "meta-package"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "provider": ["auto", "native", "llvm"],
    }
    default_options = {
        "provider": "auto",
    }

    def layout(self):
        basic_layout(self, src_folder="src")

    def config_options(self):
        if self.settings.compiler == "clang" and self.settings.os == "Linux":
            # The Clang toolchain on Linux distros typically ships without libomp.
            # FreeBSD includes it, though.
            self.options.provider = "llvm"
        elif self.settings.compiler == "apple-clang":
            self.options.provider = "llvm"
        else:
            self.options.provider = "native"

    def requirements(self):
        if self.options.provider == "llvm":
            # Note: MSVC ships with an optional LLVM OpenMP implementation, but it would require reliably setting
            # `OpenMP_RUNTIME_MSVC=llvm` in CMake for all consumers of this recipe, which is not possible in a meta-package.
            # Always use the latest llvm-openmp version, since the library is ABI-compatible across versions.
            self.requires("llvm-openmp/[*]", transitive_headers=True, transitive_libs=True)

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.options.provider == "native" and self._openmp_flags is None:
            raise ConanInvalidConfiguration(
                f"{self.settings.compiler} is not supported by this recipe. Contributions are welcome!"
            )

        if self.options.provider == "llvm":
            if self.settings.compiler not in ["clang", "apple-clang", "msvc"]:
                # More info: https://cpufun.substack.com/p/is-mixing-openmp-runtimes-safe
                self.output.warning(
                    "Warning: Using a non-native OpenMP implementation can be bug-prone. "
                    "Make sure you avoid accidental linking against the native implementation through external libraries."
                )

    @cached_property
    def _openmp_flags(self):
        # Based on https://github.com/Kitware/CMake/blob/v3.30.0/Modules/FindOpenMP.cmake#L119-L154
        compiler = str(self.settings.compiler)
        if compiler in {"gcc", "clang"}:
            return ["-fopenmp"]
        elif compiler == "apple-clang":
            return ["-Xpreprocessor", "-fopenmp"]
        elif compiler == "msvc":
            # Use `-o provider=llvm` for `-openmp=llvm` in MSVC.
            # TODO: add support for `-openmp=experimental`?
            return ["-openmp"]
        elif compiler == "intel-cc":
            if self.settings.os == "Windows":
                return ["-Qopenmp"]
            else:
                return ["-qopenmp"]
        elif compiler == "sun-cc":
            return ["-xopenmp"]

        # The following compilers are not currently covered by settings.yml,
        # but are included for completeness.
        elif compiler == "hp":
            return ["+Oopenmp"]
        elif compiler == "intel-llvm":
            if self.settings.get_safe("compiler.frontend") == "msvc":
                return ["-Qiopenmp"]
            else:
                return ["-fiopenmp"]
        elif compiler == "pathscale":
            return ["-openmp"]
        elif compiler == "nag":
            return ["-openmp"]
        elif compiler == "absoft":
            return ["-openmp"]
        elif compiler == "nvhpc":
            return ["-mp"]
        elif compiler == "pgi":
            return ["-mp"]
        elif compiler == "xl":
            return ["-qsmp=omp"]
        elif compiler == "cray":
            return ["-h", "omp"]
        elif compiler == "fujitsu":
            return ["-Kopenmp"]
        elif compiler == "fujitsu-clang":
            return ["-fopenmp"]

        return None

    def package_info(self):
        # Can't use cmake_find_mode=none because Conan tries to find_package() it internally,
        # when used transitively.
        self.cpp_info.set_property("cmake_file_name", "_openmp_")

        self.cpp_info.frameworkdirs = []
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []

        if self.options.provider == "native":
            # Export appropriate flags for packages linking against this one transitively.
            # Direct dependencies of this package will rely on CMake's FindOpenMP.cmake instead.
            self.cpp_info.cflags = self._openmp_flags
            self.cpp_info.cxxflags = self._openmp_flags
            if self.settings.compiler == "msvc":
                self.cpp_info.system_libs = ["vcompd" if self.settings.build_type == "Debug" else "vcomp"]
            elif str(self.settings.compiler) in ["intel-cc", "intel-llvm"]:
                self.cpp_info.system_libs = ["iomp5"]
            else:
                self.cpp_info.sharedlinkflags = self._openmp_flags
                self.cpp_info.exelinkflags = self._openmp_flags
