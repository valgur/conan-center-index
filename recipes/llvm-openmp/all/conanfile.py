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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
import os
import functools
import textwrap

required_conan_version = ">=1.43.0"


class LLVMOpenMpConan(ConanFile):
    name = "llvm-openmp"
    description = (
        "The OpenMP (Open Multi-Processing) specification "
        "is a standard for a set of compiler directives, "
        "library routines, and environment variables that "
        "can be used to specify shared memory parallelism "
        "in Fortran and C/C++ programs. This is the LLVM "
        "implementation."
    )
    license = "Apache-2.0 WITH LLVM-exception"
    topics = ("llvm", "openmp", "parallelism")
    homepage = "https://github.com/llvm/llvm-project/tree/master/openmp"
    url = "https://github.com/conan-io/conan-center-index"
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
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def _supports_compiler(self):
        supported_compilers_by_os = {
            "Linux": ["clang", "gcc", "intel"],
            "Macos": ["apple-clang", "clang", "gcc", "intel"],
            "Windows": ["intel"],
        }
        the_compiler, the_os = self.settings.compiler.value, self.settings.os.value
        return the_compiler in supported_compilers_by_os.get(the_os, [])

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self._supports_compiler():
            raise ConanInvalidConfiguration(
                "llvm-openmp doesn't support compiler: {} on OS: {}.".format(
                    self.settings.compiler, self.settings.os
                )
            )

    def validate(self):
        if (
            Version(self.version) <= "10.0.0"
            and self.settings.os == "Macos"
            and self.settings.arch == "armv8"
        ):
            raise ConanInvalidConfiguration("ARM v8 not supported")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "openmp-{}.src".format(self.version)
        os.rename(extracted_dir, self.source_folder)

    def _patch_sources(self):
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OPENMP_STANDALONE_BUILD"] = True
        tc.variables["LIBOMP_ENABLE_SHARED"] = self.options.shared
        if self.settings.os == "Linux":
            tc.variables["OPENMP_ENABLE_LIBOMPTARGET"] = self.options.shared
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        self._patch_sources()
        replace_in_file(
            self, os.path.join(self.source_folder, "runtime/CMakeLists.txt"), "add_subdirectory(test)", ""
        )
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            pattern="LICENSE.txt",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )
        cmake = CMake(self)
        cmake.install()

        # TODO: to remove in conan v2 once cmake_find_package* generators removed
        self._create_cmake_module_alias_targets(
            os.path.join(self.package_folder, self._module_file_rel_path),
            {
                "OpenMP::OpenMP_C": "OpenMP::OpenMP",
                "OpenMP::OpenMP_CXX": "OpenMP::OpenMP",
            },
        )

    @staticmethod
    def _create_cmake_module_alias_targets(module_file, targets):
        content = ""
        for alias, aliased in targets.items():
            content += textwrap.dedent(
                """\
                if(TARGET {aliased} AND NOT TARGET {alias})
                    add_library({alias} INTERFACE IMPORTED)
                    set_property(TARGET {alias} PROPERTY INTERFACE_LINK_LIBRARIES {aliased})
                endif()
            """.format(
                    alias=alias, aliased=aliased
                )
            )
        save(self, module_file, content)

    @property
    def _module_file_rel_path(self):
        return os.path.join("lib", "cmake", "conan-official-{}-targets.cmake".format(self.name))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenMP")
        self.cpp_info.set_property("cmake_target_name", "OpenMP::OpenMP")
        self.cpp_info.set_property("cmake_target_aliases", ["OpenMP::OpenMP_C", "OpenMP::OpenMP_CXX"])

        # TODO: to remove in conan v2 once cmake_find_package* generators removed
        self.cpp_info.names["cmake_find_package"] = "OpenMP"
        self.cpp_info.names["cmake_find_package_multi"] = "OpenMP"
        self.cpp_info.builddirs.append(os.path.join(self.package_folder, "lib", "cmake"))
        self.cpp_info.build_modules["cmake_find_package"] = [self._module_file_rel_path]
        self.cpp_info.build_modules["cmake_find_package_multi"] = [self._module_file_rel_path]

        if self.settings.compiler in ("clang", "apple-clang"):
            self.cpp_info.cxxflags = ["-Xpreprocessor", "-fopenmp"]
        elif self.settings.compiler == "gcc":
            self.cpp_info.cxxflags = ["-fopenmp"]
        elif self.settings.compiler == "intel":
            self.cpp_info.cxxflags = ["/Qopenmp"] if self.settings.os == "Windows" else ["-Qopenmp"]
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl", "m", "pthread", "rt"]
