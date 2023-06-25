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


class Stlab(ConanFile):
    name = "stlab"
    description = "The Software Technology Lab libraries."
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/stlab/libraries"
    license = "BSL-1.0"
    topics = ("c++", "concurrency", "futures", "channels")

    settings = ("arch", "os", "compiler", "build_type")

    options = {
        "boost_optional": [True, False],
        "boost_variant": [True, False],
        "coroutines": [True, False],
        "task_system": ["portable", "libdispatch", "emscripten", "pnacl", "windows", "auto"],
    }

    default_options = {
        "boost_optional": False,
        "boost_variant": False,
        "coroutines": False,
        "task_system": "auto",
    }

    no_copy_source = True
    _source_subfolder = "source_subfolder"

    def _use_boost(self):
        return self.options.boost_optional or self.options.boost_variant

    def _requires_libdispatch(self):
        # On macOS it is not necessary to use the libdispatch conan package, because the library is
        # included in the OS.
        return self.options.task_system == "libdispatch" and self.settings.os != "Macos"

    def requirements(self):
        if self._use_boost():
            self.requires("boost/1.75.0")

        if self._requires_libdispatch():
            self.requires("libdispatch/5.3.2")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = "libraries-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def _fix_boost_components(self):
        if self.settings.os != "Macos":
            return
        if self.settings.compiler != "apple-clang":
            return
        if Version(self.settings.compiler.version) >= "12":
            return

        #
        # On Apple we have to force the usage of boost.variant, because Apple's implementation of C++17 is not complete.
        #
        self.output.info(
            "Apple-Clang versions less than 12 do not correctly support std::optional or std::variant, so we will use boost::optional and boost::variant instead."
        )
        self.options.boost_optional = True
        self.options.boost_variant = True

    def _default_task_system(self):
        if self.settings.os == "Macos":
            return "libdispatch"

        if self.settings.os == "Windows":
            return "windows"

        if self.settings.os == "Emscripten":
            return "emscripten"

        return "portable"

    def _validate_task_system_libdispatch(self):
        if self.settings.os == "Linux":
            if self.settings.compiler != "clang":
                raise ConanInvalidConfiguration(
                    "{}/{} task_system=libdispatch needs Clang compiler when using OS: {}. Use Clang compiler or switch to task_system=portable or task_system=auto".format(
                        self.name, self.version, self.settings.os
                    )
                )
        elif self.settings.os != "Macos":
            raise ConanInvalidConfiguration(
                "{}/{} task_system=libdispatch is not supported on {}. Try using task_system=auto".format(
                    self.name, self.version, self.settings.os
                )
            )

    def _validate_task_system_windows(self):
        if self.settings.os != "Windows":
            self.output.info(
                "Libdispatch is not supported on {}. The task system is changed to {}.".format(
                    self.settings.os, self.options.task_system
                )
            )
            raise ConanInvalidConfiguration(
                "{}/{} task_system=windows is not supported on {}. Try using task_system=auto".format(
                    self.name, self.version, self.settings.os
                )
            )

    def _validate_task_system_emscripten(self):
        if self.settings.os != "Emscripten":
            raise ConanInvalidConfiguration(
                "{}/{} task_system=emscripten is not supported on {}. Try using task_system=auto".format(
                    self.name, self.version, self.settings.os
                )
            )

    def _validate_task_system(self):
        if self.options.task_system == "libdispatch":
            self._validate_task_system_libdispatch()
        elif self.options.task_system == "windows":
            self._validate_task_system_windows()
        elif self.options.task_system == "emscripten":
            self._validate_task_system_emscripten()

    def _validate_boost_components(self):
        if self.settings.os != "Macos":
            return
        if self.settings.compiler != "apple-clang":
            return
        if Version(self.settings.compiler.version) >= "12":
            return
        if self.options.boost_optional and self.options.boost_variant:
            return
        #
        # On Apple we have to force the usage of boost.variant, because Apple's implementation of C++17
        # is not complete.
        #
        msg = "Apple-Clang versions less than 12 do not correctly support std::optional or std::variant, so we will use boost::optional and boost::variant instead. "
        if not self.options.boost_optional and not self.options.boost_variant:
            msg += "Try -o boost_optional=True -o boost_variant=True"
        elif not self.options.boost_optional:
            msg += "Try -o boost_optional=True."
        else:
            msg += "Try -o boost_variant=True."

        raise ConanInvalidConfiguration(msg)

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, "17")

        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "9":
            raise ConanInvalidConfiguration("Need GCC >= 9")

        if self.settings.compiler == "clang" and Version(self.settings.compiler.version) < "8":
            raise ConanInvalidConfiguration("Need Clang >= 8")

        if self.settings.compiler == "Visual Studio" and Version(self.settings.compiler.version) < "15.8":
            raise ConanInvalidConfiguration("Need Visual Studio >= 2017 15.8 (MSVC 19.15)")

        # Actually, we want *at least* 15.8 (MSVC 19.15), but we cannot check this for now with Conan.
        if self.settings.compiler == "msvc" and Version(self.settings.compiler.version) < "19.15":
            raise ConanInvalidConfiguration("Need msvc >= 19.15")

        self._validate_task_system()
        self._validate_boost_components()

    def configure(self):
        if self.options.task_system == "auto":
            self.options.task_system = self._default_task_system()
        self.output.info("Stlab Task System: {}.".format(self.options.task_system))

    def package(self):
        copy(self, "*LICENSE", dst=os.path.join(self.package_folder, "licenses"), keep_path=False)
        copy(self, "stlab/*", src=self.source_folder, dst=os.path.join(self.package_folder, "include/"))

    def package_id(self):
        self.info.header_only()
        self.info.options.boost_optional = "ANY"
        self.info.options.boost_variant = "ANY"

    def package_info(self):
        coroutines_value = 1 if self.options.coroutines else 0

        self.cpp_info.defines = ["STLAB_FUTURE_COROUTINES={}".format(coroutines_value)]

        if self.options.boost_optional:
            self.cpp_info.defines.append("STLAB_FORCE_BOOST_OPTIONAL")

        if self.options.boost_variant:
            self.cpp_info.defines.append("STLAB_FORCE_BOOST_VARIANT")

        if self.options.task_system == "portable":
            self.cpp_info.defines.append("STLAB_FORCE_TASK_SYSTEM_PORTABLE")
        elif self.options.task_system == "libdispatch":
            self.cpp_info.defines.append("STLAB_FORCE_TASK_SYSTEM_LIBDISPATCH")
        elif self.options.task_system == "emscripten":
            self.cpp_info.defines.append(
                "STLAB_FORCE_TASK_SYSTEM_EMSRIPTEN"
            )  # Note: there is a typo in Stlab Cmake.
            self.cpp_info.defines.append(
                "STLAB_FORCE_TASK_SYSTEM_EMSCRIPTEN"
            )  # Note: for typo fix in later versions
        elif self.options.task_system == "pnacl":
            self.cpp_info.defines.append("STLAB_FORCE_TASK_SYSTEM_PNACL")
        elif self.options.task_system == "windows":
            self.cpp_info.defines.append("STLAB_FORCE_TASK_SYSTEM_WINDOWS")

        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread"]
