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
import glob
import os

required_conan_version = ">=1.33"


class VulkanHeadersConan(ConanFile):
    name = "diligentgraphics-vulkan-headers"
    description = "Diligent fork of Vulkan Header files."
    license = "Apache-2.0"
    topics = ("vulkan-headers", "vulkan")
    homepage = "https://github.com/DiligentGraphics/Vulkan-Headers"
    url = "https://github.com/conan-io/conan-center-index"
    provides = "vulkan-headers"
    deprecated = "vulkan-headers"
    no_copy_source = True

    def package_id(self):
        self.info.header_only()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(
            self,
            "*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )
        copy(
            self,
            "*",
            dst=os.path.join("res", "vulkan", "registry"),
            src=os.path.join(self.source_folder, "registry"),
        )

    def package_info(self):
        self.cpp_info.filenames["cmake_find_package"] = "VulkanHeaders"
        self.cpp_info.filenames["cmake_find_package_multi"] = "VulkanHeaders"
        self.cpp_info.names["cmake_find_package"] = "Vulkan"
        self.cpp_info.names["cmake_find_package_multi"] = "Vulkan"
        self.cpp_info.components["vulkanheaders"].names["cmake_find_package"] = "Headers"
        self.cpp_info.components["vulkanheaders"].names["cmake_find_package_multi"] = "Headers"
        self.cpp_info.components["vulkanheaders"].bindirs = []
        self.cpp_info.components["vulkanheaders"].libdirs = []
        self.cpp_info.components["vulkanregistry"].names["cmake_find_package"] = "Registry"
        self.cpp_info.components["vulkanregistry"].names["cmake_find_package_multi"] = "Registry"
        self.cpp_info.components["vulkanregistry"].includedirs = [os.path.join("res", "vulkan", "registry")]
        self.cpp_info.components["vulkanregistry"].bindirs = []
        self.cpp_info.components["vulkanregistry"].libdirs = []
