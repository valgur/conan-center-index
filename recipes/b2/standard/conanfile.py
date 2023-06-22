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
from conan.tools.microsoft.visual import vs_ide_version
from conan.tools.scm import Version
from conan.tools.system import package_manager


class B2Conan(ConanFile):
    name = "b2"
    homepage = "https://www.bfgroup.xyz/b2/"
    description = "B2 makes it easy to build C++ projects, everywhere."
    topics = ("installer", "builder")
    license = "BSL-1.0"
    settings = "os", "arch"
    url = "https://github.com/conan-io/conan-center-index"

    """
    * use_cxx_env: False, True

    Indicates if the build will use the CXX and
    CXXFLAGS environment variables. The common use is to add additional flags
    for building on specific platforms or for additional optimization options.

    * toolset: 'auto', 'cxx', 'cross-cxx',
    'acc', 'borland', 'clang', 'como', 'gcc-nocygwin', 'gcc',
    'intel-darwin', 'intel-linux', 'intel-win32', 'kcc', 'kylix',
    'mingw', 'mipspro', 'pathscale', 'pgi', 'qcc', 'sun', 'sunpro',
    'tru64cxx', 'vacpp', 'vc12', 'vc14', 'vc141', 'vc142', 'vc143'

    Specifies the toolset to use for building. The default of 'auto' detects
    a usable compiler for building and should be preferred. The 'cxx' toolset
    uses the 'CXX' and 'CXXFLAGS' solely for building. Using the 'cxx'
    toolset will also turn on the 'use_cxx_env' option. And the 'cross-cxx'
    toolset uses the 'BUILD_CXX' and 'BUILD_CXXFLAGS' vars. This frees the
    'CXX' and 'CXXFLAGS' variables for use in subprocesses.
    """
    options = {
        "use_cxx_env": [False, True],
        "toolset": [
            "auto",
            "cxx",
            "cross-cxx",
            "acc",
            "borland",
            "clang",
            "como",
            "gcc-nocygwin",
            "gcc",
            "intel-darwin",
            "intel-linux",
            "intel-win32",
            "kcc",
            "kylix",
            "mingw",
            "mipspro",
            "pathscale",
            "pgi",
            "qcc",
            "sun",
            "sunpro",
            "tru64cxx",
            "vacpp",
            "vc12",
            "vc14",
            "vc141",
            "vc142",
            "vc143",
        ],
    }
    default_options = {
        "use_cxx_env": False,
        "toolset": "auto",
    }

    def configure(self):
        if (
            self.options.toolset == "cxx" or self.options.toolset == "cross-cxx"
        ) and not self.options.use_cxx_env:
            raise ConanInvalidConfiguration(
                "Option toolset 'cxx' and 'cross-cxx' requires 'use_cxx_env=True'"
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True, destination="source")

    def build(self):
        use_windows_commands = os.name == "nt"
        command = "build" if use_windows_commands else "./build.sh"
        if self.options.toolset != "auto":
            command += " " + str(self.options.toolset)
        build_dir = os.path.join(self.source_folder, "source")
        engine_dir = os.path.join(build_dir, "src", "engine")
        os.chdir(engine_dir)
        with environment_append(self, {"VSCMD_START_DIR": os.curdir}):
            if self.options.use_cxx_env:
                # Allow use of CXX env vars.
                self.run(command)
            else:
                # To avoid using the CXX env vars we clear them out for the build.
                with environment_append(
                    self,
                    {
                        "CXX": "",
                        "CXXFLAGS": "",
                    },
                ):
                    self.run(command)
        os.chdir(build_dir)
        command = os.path.join(engine_dir, "b2.exe" if use_windows_commands else "b2")
        if self.options.toolset != "auto":
            full_command = (
                "{0} --ignore-site-config --prefix=../output --abbreviate-paths"
                " toolset={1} install".format(command, self.options.toolset)
            )
        else:
            full_command = "{0} --ignore-site-config --prefix=../output --abbreviate-paths" " install".format(
                command
            )
        self.run(full_command)

    def package(self):
        copy(self, "LICENSE.txt", dst="licenses", src="source")
        copy(self, pattern="*b2", dst="bin", src="output/bin")
        copy(self, pattern="*b2.exe", dst="bin", src="output/bin")
        copy(self, pattern="*.jam", dst="bin/b2_src", src="output/share/boost-build")

    def package_info(self):
        self.cpp_info.bindirs = ["bin"]
        self.env_info.path = [os.path.join(self.package_folder, "bin")]
        self.env_info.BOOST_BUILD_PATH = os.path.join(self.package_folder, "bin", "b2_src", "src", "kernel")

    def package_id(self):
        del self.info.options.use_cxx_env
        del self.info.options.toolset
