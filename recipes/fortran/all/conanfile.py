import io
import os
import shutil
import tempfile

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class FortranConan(ConanFile):
    name = "fortran"
    description = ("A meta-package for a Fortran compiler and corresponding standard libraries. "
                   "Uses tools.build:compiler_executables, if set, and falls back to gfortran from CCI otherwise.")
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://fortran-lang.org/"
    topics = ("fortran", "gfortran", "meta-package")

    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "package": [None, "ANY"]
    }
    default_options = {
        "package": "gcc/13.2.0"
    }

    @property
    def _fortran_compiler(self):
        return self.conf.get("tools.build:compiler_executables", default={}).get("fortran")

    def _get_fortran_compiler_id(self):
        # Capture Fortran compiler ID using CMake
        run_cmd = f"cmake {self.recipe_folder} --log-level=NOTICE -DCMAKE_Fortran_COMPILER={self._fortran_compiler}"
        with tempfile.TemporaryDirectory() as tmpdir:
            self.run(run_cmd, io.StringIO(), cwd=tmpdir)
            compiler_id = load(self, os.path.join(tmpdir, "FORTRAN_COMPILER")).strip()
        return compiler_id

    def _fortran_runtime(self, fortran_id):
        if fortran_id.startswith("GNU"):
            if self.settings.compiler == "gcc":
                if Version(self.settings.compiler.version) >= "5":
                    return "gfortran"
            if self.settings.compiler == "clang":
                if Version(self.settings.compiler.version) >= "9":
                    return "gfortran"
        self.output.warning(
            f"Unable to select suitable runtime for Fortran {fortran_id} "
            f"and C++ {self.settings.compiler} {self.settings.compiler.version}")
        return None

    def export(self):
        shutil.copy(os.path.join(self.recipe_folder, "fortran_helper.cmake"),
                    os.path.join(self.export_folder, "CMakeLists.txt"))
        shutil.copy(os.path.join(self.recipe_folder, "..", "..", "..", "LICENSE"),
                    os.path.join(self.export_folder, "LICENSE"))

    def export_sources(self):
        shutil.copy(os.path.join(self.export_folder, "LICENSE"),
                    os.path.join(self.export_sources_folder, "LICENSE"))

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        if self._fortran_compiler:
            if not shutil.which(self._fortran_compiler):
                raise ConanInvalidConfiguration(f"Fortran compiler '{self._fortran_compiler}' not found")
            self.info.settings.compiler.version = self._get_fortran_compiler_id()
            del self.info.settings.build_type
            del self.info.options.package

    def validate(self):
        if not self._fortran_compiler and not self.options.package:
            raise ConanInvalidConfiguration("No Fortran compiler found. "
                                            "Please set either tools.build:compiler_executables or options.package")

        if self.options.package and not self.options.package.value.startswith("gcc/"):
            raise ConanInvalidConfiguration("Only GCC is supported as the fallback Fortran compiler currently")

    def build_requirements(self):
        if not self._fortran_compiler:
            self.tool_requires(self.options.package.value, visible=True)

    def source(self):
        pass

    def build(self):
        pass

    def package(self):
        copy(self, "LICENSE", os.path.join(self.source_folder, ".."),
             os.path.join(self.package_folder, "licenses"))
        if not self._fortran_compiler:
            dep = self.dependencies.build[self.options.package.value]
            # Copy all shared libraries from the compiler to avoid having to
            # download the full compiler toolchain in a host context.
            copy(self, "*.so*",
                 os.path.join(dep.package_folder, "lib"),
                 os.path.join(self.package_folder, "lib"),
                 excludes=["*plugin.so*"])

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.includedirs = []
        if self._fortran_compiler:
            fortran_id = self._get_fortran_compiler_id()
            compiler_rt = self._fortran_runtime(fortran_id)
            if compiler_rt:
                self.cpp_info.libs = [compiler_rt]
        elif self.options.package.value.startswith("gcc/"):
            self.cpp_info.libs = ["gfortran"]
            dep = self.dependencies.build[self.options.package.value]
            fc = dep.buildenv_info.vars(self).get("FC")
            self.buildenv_info.define_path("FC", fc)
            self.env_info.FC = fc
