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
import functools

required_conan_version = ">=1.53.0"


class OsgearthConan(ConanFile):
    name = "osgearth"
    license = "LGPL-3.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://osgearth.org/"
    topics = ("openscenegraph", "graphics")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_procedural_nodekit": [True, False],
        # "build_triton_nodekit": [True, False],
        # "build_silverlining_nodekit": [True, False],
        "build_leveldb_cache": [True, False],
        "build_rocksdb_cache": [True, False],
        "build_zip_plugin": [True, False],
        "enable_geocoder": [True, False],
        "with_geos": [True, False],
        "with_sqlite3": [True, False],
        "with_draco": [True, False],
        # "with_basisu": [True, False],
        # "with_glew": [True, False],
        "with_protobuf": [True, False],
        "with_webp": [True, False],
        "install_shaders": [True, False],
        "enable_nvtt_cpu_mipmaps": [True, False],
        "enable_wininet_for_http": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_procedural_nodekit": True,
        # "build_triton_nodekit": False,
        # "build_silverlining_nodekit": False,
        "build_leveldb_cache": False,
        "build_rocksdb_cache": False,
        "build_zip_plugin": True,
        "enable_geocoder": False,
        "with_geos": True,
        "with_sqlite3": True,
        "with_draco": False,
        # "with_basisu": False,
        # "with_glew": True,
        "with_protobuf": True,
        "with_webp": True,
        "install_shaders": True,
        "enable_nvtt_cpu_mipmaps": False,
        "enable_wininet_for_http": False,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os != "Windows":
            self.options.enable_wininet_for_http = False

        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

        if is_msvc(self):
            self.options.build_procedural_nodekit = False

        if self.settings.compiler == "gcc" and self.settings.compiler.version == "11":
            # need draco >= 1.4.0 for gcc11
            # https://github.com/google/draco/issues/635
            self.options.with_draco = False

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("opengl/system")
        self.requires("gdal/3.5.2")
        self.requires("openscenegraph/3.6.5")
        self.requires("libcurl/8.2.0")
        self.requires("lerc/4.0.0")
        self.requires("rapidjson/cci.20220822")

        self.requires("zlib/1.2.13", override=True)
        self.requires("libtiff/4.5.1", override=True)
        self.requires("openssl/[>=1.1 <4]", override=True)

        # if self.options.build_triton_nodekit:
        #     self.requires("triton_nodekit")
        # if self.options.build_silverlining_nodekit:
        #     self.requires("silverlining_nodekit")
        if self.options.build_leveldb_cache:
            self.requires("leveldb/1.23")
        if self.options.build_rocksdb_cache:
            self.requires("rocksdb/6.29.5")
        if self.options.build_zip_plugin:
            self.requires("zstd/1.5.5")  # override
        if self.options.with_geos:
            self.requires("geos/3.11.2")
        if self.options.with_sqlite3:
            self.requires("sqlite3/3.42.0")
        if self.options.with_draco:
            self.requires("draco/1.5.6")
        # if self.options.with_basisu:
        #     self.requires("basisu")
        # if self.options.with_glew:
        #     self.requires("glew/2.2.0")
        if self.options.with_protobuf:
            self.requires("protobuf/3.21.12")
        if self.options.with_webp:
            self.requires("libwebp/1.3.1")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)
        elif self.settings.compiler == "apple-clang":
            raise ConanInvalidConfiguration(
                "With apple-clang cppstd needs to be set, since default is not at least c++11."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

        self._patch_sources()

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OSGEARTH_BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["OSGEARTH_BUILD_TOOLS"] = False
        tc.variables["OSGEARTH_BUILD_EXAMPLES"] = False
        tc.variables["OSGEARTH_BUILD_TESTS"] = False

        tc.variables["OSGEARTH_BUILD_PROCEDURAL_NODEKIT"] = self.options.build_procedural_nodekit
        # tc.variables["OSGEARTH_BUILD_TRITON_NODEKIT"] = self.options.build_triton_nodekit
        # tc.variables["OSGEARTH_BUILD_SILVERLINING_NODEKIT"] = self.options.build_silverlining_nodekit
        tc.variables["OSGEARTH_BUILD_LEVELDB_CACHE"] = self.options.build_leveldb_cache
        tc.variables["OSGEARTH_BUILD_ROCKSDB_CACHE"] = self.options.build_rocksdb_cache
        tc.variables["OSGEARTH_BUILD_ZIP_PLUGIN"] = self.options.build_zip_plugin
        tc.variables["OSGEARTH_ENABLE_GEOCODER"] = self.options.enable_geocoder

        tc.variables["WITH_EXTERNAL_DUKTAPE"] = False
        tc.variables["WITH_EXTERNAL_TINYXML"] = False
        tc.variables["CURL_IS_STATIC"] = not self.dependencies["libcurl"].options.shared
        tc.variables["CURL_INCLUDE_DIR"] = self.dependencies["libcurl"].cpp_info.includedirs[0]
        tc.variables["OSGEARTH_INSTALL_SHADERS"] = self.options.install_shaders
        tc.variables["OSGEARTH_ENABLE_NVTT_CPU_MIPMAPS"] = self.options.enable_nvtt_cpu_mipmaps
        tc.variables["OSGEARTH_ENABLE_WININET_FOR_HTTP"] = self.options.enable_wininet_for_http

        # our own defines for using in our top-level CMakeLists.txt
        tc.variables["OSGEARTH_WITH_GEOS"] = self.options.with_geos
        tc.variables["OSGEARTH_WITH_SQLITE3"] = self.options.with_sqlite3
        tc.variables["OSGEARTH_WITH_WEBP"] = self.options.with_webp
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

        for package in ("Draco", "GEOS", "LevelDB", "OSG", "RocksDB", "Sqlite3", "WEBP"):
            # Prefer conan's find package scripts over osgEarth's
            os.unlink(os.path.join(self.source_folder, "CMakeModules", "Find{}.cmake".format(package)))

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=self.source_path.parent)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE.txt",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)

        if self.options.install_shaders:
            rename(self, os.path.join(self.package_folder, "resources"), os.path.join(self.package_folder, "res"))

        if self.settings.os in ["Linux", "FreeBSD"]:
            rename(self, os.path.join(self.package_folder, "lib64"), os.path.join(self.package_folder, "lib"))

        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        if self.settings.build_type == "Debug":
            postfix = "d"
        elif self.settings.build_type == "RelWithDebInfo":
            postfix = "rd"
        elif self.settings.build_type == "MinSizeRel":
            postfix = "s"
        else:
            postfix = ""

        def setup_lib(library, required_components):
            lib = self.cpp_info.components[library]
            lib.libs = [library + postfix]

            for source_lib, components in required_components.items():
                lib.requires += [source_lib + "::" + comp for comp in components]

            return lib

        # osgEarth the main lib
        required_libs = {"openscenegraph": ["osg", "osgUtil", "osgSim", "osgViewer", "osgText", "osgGA", "osgShadow",
                                            "OpenThreads", "osgManipulator"],
                         "libcurl": ["libcurl"],
                         "gdal": ["gdal"],
                         "opengl": ["opengl"],
                         }

        osgearth = setup_lib("osgEarth", required_libs)

        if not self.options.shared and is_msvc(self):
            osgearth.defines += ["OSGEARTH_LIBRARY_STATIC"]
        if self.options.build_zip_plugin:
            osgearth.requires += ["zstd::zstd"]
        if self.options.with_geos:
            osgearth.requires += ["geos::geos"]
        if self.options.with_sqlite3:
            osgearth.requires += ["sqlite3::sqlite3"]
        if self.options.with_protobuf:
            osgearth.requires += ["protobuf::protobuf"]
        if self.options.with_webp:
            osgearth.requires += ["libwebp::libwebp"]

        # osgEarthProcedural
        if self.options.build_procedural_nodekit:
            setup_lib("osgEarthProcedural", {}).requires.append("osgEarth")

        # plugins
        def setup_plugin(plugin):
            libname = "osgdb_" + plugin
            plugin_library = self.cpp_info.components[libname]
            plugin_library.libs = [] if self.options.shared else [libname + postfix]
            plugin_library.requires = ["osgEarth"]
            if not self.options.shared:
                plugin_library.libdirs = [os.path.join("lib", "osgPlugins-{}"
                                                       .format(self.deps_cpp_info["openscenegraph"].version))]
            return plugin_library

        setup_plugin("osgearth_bumpmap")
        setup_plugin("osgearth_cache_filesystem")

        if self.options.build_leveldb_cache:
            setup_plugin("osgearth_cache_leveldb").requires.append("leveldb::leveldb")

        if self.options.build_rocksdb_cache:
            setup_plugin("osgearth_cache_rocksdb").requires.append("rocksdb::rocksdb")

        setup_plugin("osgearth_bumpmap")
        setup_plugin("osgearth_cache_filesystem")
        setup_plugin("osgearth_colorramp")
        setup_plugin("osgearth_detail")
        setup_plugin("earth")
        setup_plugin("osgearth_engine_rex")
        setup_plugin("osgearth_featurefilter_intersect")
        setup_plugin("osgearth_featurefilter_join")
        setup_plugin("gltf").requires.append("rapidjson::rapidjson")
        setup_plugin("kml")
        setup_plugin("osgearth_mapinspector")
        setup_plugin("osgearth_monitor")
        setup_plugin("osgearth_scriptengine_javascript")
        setup_plugin("osgearth_sky_gl")
        setup_plugin("osgearth_sky_simple")
        setup_plugin("template")
        setup_plugin("osgearth_terrainshader")

        if self.options.with_webp:
            setup_plugin("webp").requires.append("libwebp::libwebp")

        setup_plugin("lerc").requires.append("lerc::lerc")
        setup_plugin("osgearth_vdatum_egm2008")
        setup_plugin("osgearth_vdatum_egm84")
        setup_plugin("osgearth_vdatum_egm96")
        setup_plugin("osgearth_viewpoints")
        setup_plugin("fastdxt")

        if self.settings.os == "Windows":
            self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
            self.env_info.PATH.append(os.path.join(self.package_folder, "bin/osgPlugins-{}"
                                                   .format(self.deps_cpp_info["openscenegraph"].version)))
        elif self.settings.os in ["Linux", "FreeBSD"]:
            self.env_info.LD_LIBRARY_PATH.append(os.path.join(self.package_folder, "lib"))
