# TODO: verify the Conan v2 migration

import glob
import os
import shutil
import stat
import textwrap

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    export_conandata_patches,
    get,
    replace_in_file,
    rm,
    rmdir,
)
from conan.tools.scm import Version


class PythonOption:
    OFF = "off"
    SYSTEM = "system"
    # in future we may allow the user to specify a version when
    # libPython is available in Conan Center Index.
    # FIXME: add option to use CCI Python package when it is available
    ALL = [OFF, SYSTEM]


required_conan_version = ">=1.53.0"


class CernRootConan(ConanFile):
    name = "cern-root"
    description = "CERN ROOT data analysis framework."
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://root.cern/"
    topics = ("data-analysis", "physics")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "python": ["off", "system"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "python": "off",
    }

    @property
    def _minimum_cpp_standard(self):
        return 11

    @property
    def _minimum_compilers_version(self):
        return {
            "Visual Studio": "16.1",
            "gcc": "4.8",
            "clang": "3.4",
            "apple-clang": "5.1",
        }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cfitsio/4.2.0")
        self.requires("fftw/3.3.10")
        self.requires("giflib/5.2.1")
        self.requires("glew/2.2.0")
        self.requires("glu/system")
        self.requires("libcurl/8.1.2")
        self.requires("libjpeg/9e")
        self.requires("libpng/1.6.39")
        self.requires("libxml2/2.11.4")
        self.requires("lz4/1.9.4")
        self.requires("opengl/system")
        self.requires("openssl/[>=1.1 <4]")
        self.requires("pcre/8.45")
        self.requires("sqlite3/3.42.0")
        self.requires("onetbb/2021.9.0")
        self.requires("xorg/system")
        self.requires("xxhash/0.8.1")
        self.requires("xz_utils/5.4.2")
        self.requires("zstd/1.5.5")

    def validate(self):
        self._enforce_minimum_compiler_version()
        self._enforce_libcxx_requirements()

    def _enforce_minimum_compiler_version(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)
        min_version = self._minimum_compilers_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warn(
                f"{self.name} recipe lacks information about the {self.settings.compiler} compiler support."
            )
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    f"{self.name} requires C++{self._minimum_cpp_standard} support. The current compiler"
                    f" {self.settings.compiler} {self.settings.compiler.version} does not support it."
                )

    def _enforce_libcxx_requirements(self):
        libcxx = self.settings.get_safe("compiler.libcxx")
        # ROOT doesn't currently build with libc++.
        # This restriction may be lifted in future if the problems are fixed upstream
        if libcxx and libcxx == "libc++":
            raise ConanInvalidConfiguration(f'{self.name} is incompatible with libc++".')

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @staticmethod
    def _make_file_executable(filename):
        st = os.stat(filename)
        os.chmod(filename, st.st_mode | stat.S_IEXEC)

    def generate(self):
        lib_paths = []
        include_paths = []
        for dep in self.dependencies.values():
            lib_paths += dep.cpp_info.libdirs
            include_paths += dep.cpp_info.includedirs

        tc = CMakeToolchain(self)
        tc.variables.update(
            {
                "BUILD_SHARED_LIBS": True,
                "fail-on-missing": True,
                "CMAKE_CXX_STANDARD": self._cmake_cxx_standard,
                "gnuinstall": True,
                "soversion": True,
                # Disable builtins and use Conan deps where available
                "builtin_cfitsio": False,
                "builtin_davix": False,
                "builtin_fftw3": False,
                "builtin_freetype": False,
                "builtin_glew": False,
                "builtin_lz4": False,
                "builtin_lzma": False,
                "builtin_openssl": False,
                "builtin_pcre": False,
                "builtin_tbb": False,
                "builtin_xxhash": False,
                "builtin_zlib": False,
                "builtin_zstd": False,
                # Enable builtins where there is no Conan package
                "builtin_afterimage": True,  # FIXME : replace with afterimage CCI package when available
                "builtin_gsl": True,  # FIXME : replace with gsl CCI package when available
                "builtin_gl2ps": True,  # FIXME : replace with gl2ps CCI package when available
                "builtin_ftgl": True,  # FIXME : replace with ftgl CCI package when available
                "builtin_vdt": True,  # FIXME : replace with vdt CCI package when available
                # No Conan packages available for these dependencies yet
                "davix": False,  # FIXME : switch on if davix CCI package available
                "pythia6": False,  # FIXME : switch on if pythia6 CCI package available
                "pythia8": False,  # FIXME : switch on if pythia8 CCI package available
                "mysql": False,  # FIXME : switch on if mysql CCI package available
                "oracle": False,
                "pgsql": False,  # FIXME: switch on if PostgreSQL CCI package available
                "gfal": False,  # FIXME: switch on if gfal CCI package available
                "tmva-pymva": False,  # FIXME: switch on if Python CCI package available
                "xrootd": False,  # FIXME: switch on if xrootd CCI package available
                "pyroot": self._cmake_pyrootopt,
                # clad is built with ExternalProject_Add and its
                # COMPILE_DEFINITIONS property is not propagated causing the build to
                # fail on some systems if libcxx != libstdc++11
                "clad": False,
                # Tell CMake where to look for Conan provided dependencies
                "CMAKE_LIBRARY_PATH": ";".join(lib_paths).replace("\\", "/"),
                "CMAKE_INCLUDE_PATH": ";".join(include_paths).replace("\\", "/"),
                # Configure install directories
                # Conan CCI hooks restrict the allowed install directory
                # names but ROOT is very picky about where build/runtime
                # resources get installed.
                # Set install prefix to work around these limitations
                # Following: https://github.com/conan-io/conan/issues/3695
                "CMAKE_INSTALL_CMAKEDIR": "lib/cmake",
                "CMAKE_INSTALL_DATAROOTDIR": "res/share",
                "CMAKE_INSTALL_SYSCONFDIR": "res/etc",
                # Fix some Conan-ROOT CMake variable naming differences
                "PNG_PNG_INCLUDE_DIR": ";".join(self.dependencies["libpng"].cpp_info.includedirs).replace(
                    "\\", "/"
                ),
                "LIBLZMA_INCLUDE_DIR": ";".join(self.dependencies["xz_utils"].cpp_info.includedirs).replace(
                    "\\", "/"
                ),
            }
        )
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_source_cmake(self):
        rm(self, "FindTBB.cmake", os.path.join(self.source_folder, "cmake", "modules"))
        # Conan generated cmake_find_packages names differ from
        # names ROOT expects (usually only due to case differences)
        # There is currently no way to change these names
        # see: https://github.com/conan-io/conan/issues/4430
        # Patch ROOT CMake to use Conan dependencies
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "project(ROOT)",
            textwrap.dedent("""\
                project(ROOT)
                # sets the current C runtime on MSVC (MT vs MD vd MTd vs MDd)
                find_package(OpenSSL REQUIRED)
                set(OPENSSL_VERSION ${OpenSSL_VERSION})
                find_package(LibXml2 REQUIRED)
                set(LIBXML2_INCLUDE_DIR ${LibXml2_INCLUDE_DIR})
                set(LIBXML2_LIBRARIES ${LibXml2_LIBRARIES})
                find_package(SQLite3 REQUIRED)
                set(SQLITE_INCLUDE_DIR ${SQLITE3_INCLUDE_DIRS})
                set(SQLITE_LIBRARIES SQLite::SQLite3)
            """),
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "set(CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake/modules)",
            "list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake/modules)",
        )

    def _fix_source_permissions(self):
        # Fix execute permissions on scripts
        scripts = [
            filename
            for pattern in (
                os.path.join("**", "configure"),
                os.path.join("**", "*.sh"),
                os.path.join("**", "*.csh"),
                os.path.join("**", "*.bat"),
            )
            for filename in glob.glob(os.path.join(self.source_folder, pattern), recursive=True)
        ]
        for s in scripts:
            self._make_file_executable(s)

    def _patch_sources(self):
        apply_conandata_patches(self)
        self._patch_source_cmake()
        self._fix_source_permissions()

    def _move_findcmake_conan_to_root_dir(self):
        for f in ["opengl_system", "GLEW", "glu", "TBB", "LibXml2", "ZLIB", "SQLite3"]:
            shutil.copy(f"Find{f}.cmake", os.path.join(self.source_folder, "cmake", "modules"))

    @property
    def _cmake_cxx_standard(self):
        return str(self.settings.get_safe("compiler.cppstd", "11"))

    @property
    def _cmake_pyrootopt(self):
        if self.options.python == PythonOption.OFF:
            return False
        else:
            return True

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )
        cmake = CMake(self)
        cmake.install()
        # Fix for CMAKE-MODULES-CONFIG-FILES (KB-H016)
        rm(
            self,
            "*Config*.cmake",
            os.path.join(self.package_folder, "lib", "cmake"),
            recursive=True,
        )
        rmdir(self, os.path.join(self.package_folder, "res", "README"))
        rmdir(self, os.path.join(self.package_folder, "res", "share", "man"))
        rmdir(self, os.path.join(self.package_folder, "res", "share", "doc"))
        rmdir(self, os.path.join(self.package_folder, "res", "tutorials"))

    def package_info(self):
        # FIXME: ROOT generates multiple CMake files
        self.cpp_info.names["cmake_find_package"] = "ROOT"
        self.cpp_info.names["cmake_find_package_multi"] = "ROOT"
        # See root-config --libs for a list of ordered libs
        self.cpp_info.libs = [
            "Core",
            "Imt",
            "RIO",
            "Net",
            "Hist",
            "Graf",
            "Graf3d",
            "Gpad",
            "ROOTVecOps",
            "Tree",
            "TreePlayer",
            "Rint",
            "Postscript",
            "Matrix",
            "Physics",
            "MathCore",
            "Thread",
            "MultiProc",
            "ROOTDataFrame",
        ]
        self.cpp_info.builddirs = [os.path.join("lib", "cmake")]
        self.cpp_info.build_modules += [
            os.path.join("lib", "cmake", "RootMacros.cmake"),
            # os.path.join("lib", "cmake", "ROOTUseFile.cmake"),
        ]
        self.cpp_info.resdirs = ["res"]
