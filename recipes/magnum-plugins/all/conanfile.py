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
import os
import textwrap

required_conan_version = ">=1.33.0"


class MagnumConan(ConanFile):
    name = "magnum-plugins"
    description = "Plugins for the Magnum C++11/C++14 graphics engine"
    license = "MIT"
    topics = ("magnum", "graphics", "rendering", "3d", "2d", "opengl")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://magnum.graphics"

    settings = "os", "compiler", "build_type", "arch"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "shared_plugins": [True, False],
        "assimp_importer": [True, False],
        "basis_imageconverter": [True, False],
        "basis_importer": [True, False],
        "dds_importer": [True, False],
        "devil_imageimporter": [True, False],
        "drflac_audioimporter": [True, False],
        "drmp3_audioimporter": [True, False],
        "drwav_audioimporter": [True, False],
        "faad2_audioimporter": [True, False],
        "freetype_font": [True, False],
        "harfbuzz_font": [True, False],
        "ico_importer": [True, False],
        "jpeg_imageconverter": [True, False],
        "jpeg_importer": [True, False],
        "meshoptimizer_sceneconverter": [True, False],
        "miniexr_imageconverter": [True, False],
        "opengex_importer": [True, False],
        "png_imageconverter": [True, False],
        "png_importer": [True, False],
        "primitive_importer": [True, False],
        "stanford_importer": [True, False],
        "stanford_sceneconverter": [True, False],
        "stb_imageconverter": [True, False],
        "stb_imageimporter": [True, False],
        "stbtruetype_font": [True, False],
        "stbvorbis_audioimporter": [True, False],
        "stl_importer": [True, False],
        "tinygltf_importer": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "shared_plugins": True,
        "assimp_importer": True,
        "basis_imageconverter": False,
        "basis_importer": False,
        "dds_importer": True,
        "devil_imageimporter": False,
        "drflac_audioimporter": True,
        "drmp3_audioimporter": True,
        "drwav_audioimporter": True,
        "faad2_audioimporter": False,
        "freetype_font": True,
        "harfbuzz_font": True,
        "ico_importer": True,
        "jpeg_imageconverter": True,
        "jpeg_importer": True,
        "meshoptimizer_sceneconverter": True,
        "miniexr_imageconverter": True,
        "opengex_importer": True,
        "png_imageconverter": True,
        "png_importer": True,
        "primitive_importer": True,
        "stanford_importer": True,
        "stanford_sceneconverter": True,
        "stb_imageconverter": True,
        "stb_imageimporter": True,
        "stbtruetype_font": True,
        "stbvorbis_audioimporter": True,
        "stl_importer": True,
        "tinygltf_importer": True,
    }, "cmake_find_package_multi"

    def export_sources(self):
        copy(self, "cmake/*", self.export_sources_folder)
        export_conandata_patches(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            'set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/modules/" ${CMAKE_MODULE_PATH})',
            "",
        )
        assimp_importer_cmake_file = os.path.join(
            self.source_folder, "src", "MagnumPlugins", "AssimpImporter", "CMakeLists.txt"
        )
        replace_in_file(
            self, assimp_importer_cmake_file, "find_package(Assimp REQUIRED)", "find_package(assimp REQUIRED)"
        )
        replace_in_file(self, assimp_importer_cmake_file, "Assimp::Assimp", "assimp::assimp")

        harfbuzz_cmake_file = os.path.join(
            self.source_folder, "src", "MagnumPlugins", "HarfBuzzFont", "CMakeLists.txt"
        )
        replace_in_file(
            self, harfbuzz_cmake_file, "find_package(HarfBuzz REQUIRED)", "find_package(harfbuzz REQUIRED)"
        )
        replace_in_file(self, harfbuzz_cmake_file, "HarfBuzz::HarfBuzz", "harfbuzz::harfbuzz")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

        if self.settings.os == "Emscripten":
            self.options.shared_plugins = False
            # FIXME: Transitive dep 'glib' is not prepared for Emscripten (https://github.com/emscripten-core/emscripten/issues/11066)
            self.options.harfbuzz_font = False
            # Audio is not provided by Magnum
            self.options.drflac_audioimporter = False
            self.options.drmp3_audioimporter = False
            self.options.drwav_audioimporter = False
            self.options.faad2_audioimporter = False
            self.options.stbvorbis_audioimporter = False
            # FIXME: Conan package fails for 'brotli'
            self.options.freetype_font = False

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("magnum/{}".format(self.version))
        if self.options.assimp_importer:
            self.requires("assimp/5.0.1")
        if self.options.harfbuzz_font:
            self.requires("harfbuzz/2.8.2")
        if self.options.freetype_font:
            self.requires("freetype/2.11.0")
        if self.options.jpeg_importer or self.options.jpeg_imageconverter:
            self.requires("libjpeg/9d")
        if self.options.meshoptimizer_sceneconverter:
            self.requires("meshoptimizer/0.15")
        if self.options.png_imageconverter:
            self.requires("libpng/1.6.37")
        if self.options.basis_imageconverter or self.options.basis_importer:
            raise ConanInvalidConfiguration("Requires 'basisuniversal', not available in ConanCenter yet")
        if self.options.devil_imageimporter:
            raise ConanInvalidConfiguration("Requires 'DevIL', not available in ConanCenter yet")
        if self.options.faad2_audioimporter:
            raise ConanInvalidConfiguration("Requires 'faad2', not available in ConanCenter yet")

    def build_requirements(self):
        self.build_requires("corrade/{}".format(self.version))

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)

        if not self.options["magnum"].trade:
            raise ConanInvalidConfiguration("Magnum Trade is required")

        # TODO: There are lot of things to check here: 'magnum::audio' required for audio plugins...

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_STATIC"] = not self.options.shared
        tc.variables["BUILD_STATIC_PIC"] = self.options.get_safe("fPIC", False)
        tc.variables["BUILD_PLUGINS_STATIC"] = not self.options.shared_plugins
        tc.variables["LIB_SUFFIX"] = ""
        tc.variables["BUILD_TESTS"] = False

        tc.variables["WITH_ASSIMPIMPORTER"] = self.options.assimp_importer
        tc.variables["WITH_BASISIMAGECONVERTER"] = self.options.basis_imageconverter
        tc.variables["WITH_BASISIMPORTER"] = self.options.basis_importer
        tc.variables["WITH_DDSIMPORTER"] = self.options.dds_importer
        tc.variables["WITH_DEVILIMAGEIMPORTER"] = self.options.devil_imageimporter
        tc.variables["WITH_DRFLACAUDIOIMPORTER"] = self.options.drflac_audioimporter
        tc.variables["WITH_DRMP3AUDIOIMPORTER"] = self.options.drmp3_audioimporter
        tc.variables["WITH_DRWAVAUDIOIMPORTER"] = self.options.drwav_audioimporter
        tc.variables["WITH_FAAD2AUDIOIMPORTER"] = self.options.faad2_audioimporter
        tc.variables["WITH_FREETYPEFONT"] = self.options.freetype_font
        tc.variables["WITH_HARFBUZZFONT"] = self.options.harfbuzz_font
        tc.variables["WITH_ICOIMPORTER"] = self.options.ico_importer
        tc.variables["WITH_JPEGIMAGECONVERTER"] = self.options.jpeg_imageconverter
        tc.variables["WITH_JPEGIMPORTER"] = self.options.jpeg_importer
        tc.variables["WITH_MESHOPTIMIZERSCENECONVERTER"] = self.options.meshoptimizer_sceneconverter
        tc.variables["WITH_MINIEXRIMAGECONVERTER"] = self.options.miniexr_imageconverter
        tc.variables["WITH_OPENGEXIMPORTER"] = self.options.opengex_importer
        tc.variables["WITH_PNGIMAGECONVERTER"] = self.options.png_imageconverter
        tc.variables["WITH_PNGIMPORTER"] = self.options.png_importer
        tc.variables["WITH_PRIMITIVEIMPORTER"] = self.options.primitive_importer
        tc.variables["WITH_STANFORDIMPORTER"] = self.options.stanford_importer
        tc.variables["WITH_STANFORDSCENECONVERTER"] = self.options.stanford_sceneconverter
        tc.variables["WITH_STBIMAGECONVERTER"] = self.options.stb_imageconverter
        tc.variables["WITH_STBIMAGEIMPORTER"] = self.options.stb_imageimporter
        tc.variables["WITH_STBTRUETYPEFONT"] = self.options.stbtruetype_font
        tc.variables["WITH_STBVORBISAUDIOIMPORTER"] = self.options.stbvorbis_audioimporter
        tc.variables["WITH_STLIMPORTER"] = self.options.stl_importer
        tc.variables["WITH_TINYGLTFIMPORTER"] = self.options.tinygltf_importer

        tc.variables["CONAN_CMAKE_SILENT_OUTPUT"] = True
        # TODO: convert to CMakeToolchain variables
        # The original project uses the path to the 'magnum' package, in Conan we cannot modify existing package
        tc.variables[
            "MAGNUM_PLUGINS_DEBUG_BINARY_INSTALL_DIR"
        ] = "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_BINDIR}/magnum-d"
        tc.variables[
            "MAGNUM_PLUGINS_DEBUG_LIBRARY_INSTALL_DIR"
        ] = "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_LIBDIR}/magnum-d"
        tc.variables[
            "MAGNUM_PLUGINS_RELEASE_BINARY_INSTALL_DIR"
        ] = "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_BINDIR}/magnum"
        tc.variables[
            "MAGNUM_PLUGINS_RELEASE_LIBRARY_INSTALL_DIR"
        ] = "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_LIBDIR}/magnum"
        tc.variables[
            "MAGNUM_PLUGINS_FONT_DEBUG_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_BINARY_INSTALL_DIR}/fonts"
        tc.variables[
            "MAGNUM_PLUGINS_FONT_DEBUG_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_LIBRARY_INSTALL_DIR}/fonts"
        tc.variables[
            "MAGNUM_PLUGINS_FONT_RELEASE_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_BINARY_INSTALL_DIR}/fonts"
        tc.variables[
            "MAGNUM_PLUGINS_FONT_RELEASE_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_LIBRARY_INSTALL_DIR}/fonts"
        tc.variables[
            "MAGNUM_PLUGINS_FONTCONVERTER_DEBUG_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_BINARY_INSTALL_DIR}/fontconverters"
        tc.variables[
            "MAGNUM_PLUGINS_FONTCONVERTER_RELEASE_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_LIBRARY_INSTALL_DIR}/fontconverters"
        tc.variables[
            "MAGNUM_PLUGINS_IMAGECONVERTER_DEBUG_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_BINARY_INSTALL_DIR}/imageconverters"
        tc.variables[
            "MAGNUM_PLUGINS_IMAGECONVERTER_DEBUG_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_LIBRARY_INSTALL_DIR}/imageconverters"
        tc.variables[
            "MAGNUM_PLUGINS_IMAGECONVERTER_RELEASE_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_LIBRARY_INSTALL_DIR}/imageconverters"
        tc.variables[
            "MAGNUM_PLUGINS_IMAGECONVERTER_RELEASE_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_BINARY_INSTALL_DIR}/imageconverters"
        tc.variables[
            "MAGNUM_PLUGINS_IMPORTER_DEBUG_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_BINARY_INSTALL_DIR}/importers"
        tc.variables[
            "MAGNUM_PLUGINS_IMPORTER_DEBUG_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_LIBRARY_INSTALL_DIR}/importers"
        tc.variables[
            "MAGNUM_PLUGINS_IMPORTER_RELEASE_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_BINARY_INSTALL_DIR}/importers"
        tc.variables[
            "MAGNUM_PLUGINS_IMPORTER_RELEASE_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_LIBRARY_INSTALL_DIR}/importers"
        tc.variables[
            "MAGNUM_PLUGINS_SCENECONVERTER_DEBUG_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_BINARY_INSTALL_DIR}/sceneconverters"
        tc.variables[
            "MAGNUM_PLUGINS_SCENECONVERTER_DEBUG_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_LIBRARY_INSTALL_DIR}/sceneconverters"
        tc.variables[
            "MAGNUM_PLUGINS_SCENECONVERTER_RELEASE_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_LIBRARY_INSTALL_DIR}/sceneconverters"
        tc.variables[
            "MAGNUM_PLUGINS_SCENECONVERTER_RELEASE_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_BINARY_INSTALL_DIR}/sceneconverters"
        tc.variables[
            "MAGNUM_PLUGINS_AUDIOIMPORTER_DEBUG_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_BINARY_INSTALL_DIR}/audioimporters"
        tc.variables[
            "MAGNUM_PLUGINS_AUDIOIMPORTER_DEBUG_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_DEBUG_LIBRARY_INSTALL_DIR}/audioimporters"
        tc.variables[
            "MAGNUM_PLUGINS_AUDIOIMPORTER_RELEASE_BINARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_BINARY_INSTALL_DIR}/audioimporters"
        tc.variables[
            "MAGNUM_PLUGINS_AUDIOIMPORTER_RELEASE_LIBRARY_INSTALL_DIR"
        ] = "${MAGNUM_PLUGINS_RELEASE_LIBRARY_INSTALL_DIR}/audioimporters"
        tc.variables[
            "MAGNUM_INCLUDE_INSTALL_DIR"
        ] = "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_INCLUDEDIR}/Magnum"
        tc.variables[
            "MAGNUM_EXTERNAL_INCLUDE_INSTALL_DIR"
        ] = "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_INCLUDEDIR}/MagnumExternal"
        tc.variables[
            "MAGNUM_PLUGINS_INCLUDE_INSTALL_DIR"
        ] = "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_INCLUDEDIR}/MagnumPlugins"
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        if not self.options.shared_plugins:
            build_modules_folder = os.path.join(self.package_folder, "lib", "cmake")
            os.makedirs(build_modules_folder)
            for component, target, library, folder, deps in self._plugins:
                build_module_path = os.path.join(
                    build_modules_folder, "conan-magnum-plugins-{}.cmake".format(component)
                )
                with open(build_module_path, "w+") as f:
                    f.write(
                        textwrap.dedent(
                            """\
                        if(NOT ${{CMAKE_VERSION}} VERSION_LESS "3.0")
                            if(TARGET MagnumPlugins::{target})
                                set_target_properties(MagnumPlugins::{target} PROPERTIES INTERFACE_SOURCES
                                                    "${{CMAKE_CURRENT_LIST_DIR}}/../../include/MagnumPlugins/{library}/importStaticPlugin.cpp")
                            endif()
                        endif()
                    """.format(
                                target=target, library=library
                            )
                        )
                    )

        rmdir(self, os.path.join(self.package_folder, "share"))
        copy(self, "*.cmake", src=os.path.join(self.source_folder, "cmake"), dst=os.path.join("lib", "cmake"))
        copy(self, "COPYING", src=self.source_folder, dst="licenses")

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "MagnumPlugins"
        self.cpp_info.names["cmake_find_package_multi"] = "MagnumPlugins"

        magnum_plugin_libdir = (
            "magnum-d" if self.settings.build_type == "Debug" and self.options.shared_plugins else "magnum"
        )
        plugin_lib_suffix = (
            "-d" if self.settings.build_type == "Debug" and not self.options.shared_plugins else ""
        )
        lib_suffix = "-d" if self.settings.build_type == "Debug" else ""

        self.cpp_info.components["magnumopenddl"].names["cmake_find_package"] = "MagnumOpenDdl"
        self.cpp_info.components["magnumopenddl"].names["cmake_find_package_multi"] = "MagnumOpenDdl"
        self.cpp_info.components["magnumopenddl"].libs = ["MagnumOpenDdl{}".format(lib_suffix)]
        self.cpp_info.components["magnumopenddl"].requires = ["magnum::magnum"]

        # Plugins
        if self.options.basis_imageconverter:
            raise ConanException("Component not defined, please contribute it to the Conan recipe")

        if self.options.basis_importer:
            raise ConanException("Component not defined, please contribute it to the Conan recipe")

        if self.options.devil_imageimporter:
            raise ConanException("Component not defined, please contribute it to the Conan recipe")

        if self.options.faad2_audioimporter:
            raise ConanException("Component not defined, please contribute it to the Conan recipe")

        # The global target doesn't provide anything in this package. Null it.
        self.cpp_info.components["_global_target"].names["cmake_find_package"] = "MagnumPlugins"
        self.cpp_info.components["_global_target"].names["cmake_find_package_multi"] = "MagnumPlugins"
        self.cpp_info.components["_global_target"].build_modules["cmake_find_package"].append(
            os.path.join("lib", "cmake", "conan-bugfix-global-target.cmake")
        )

        # Add all the plugins
        for component, target, library, folder, deps in self._plugins:
            self.cpp_info.components[component].names["cmake_find_package"] = target
            self.cpp_info.components[component].names["cmake_find_package_multi"] = target
            self.cpp_info.components[component].libs = ["{}{}".format(library, plugin_lib_suffix)]
            self.cpp_info.components[component].libdirs = [
                os.path.join(self.package_folder, "lib", magnum_plugin_libdir, folder)
            ]
            self.cpp_info.components[component].requires = deps
            if not self.options.shared_plugins:
                self.cpp_info.components[component].build_modules.append(
                    os.path.join("lib", "cmake", "conan-magnum-plugins-{}.cmake".format(component))
                )
        plugin_dir = "bin" if self.settings.os == "Windows" else "lib"
        self.user_info.plugins_basepath = os.path.join(self.package_folder, plugin_dir, magnum_plugin_libdir)

    @property
    def _plugins(self):
        #   (opt_name, (component, target, library, folder, deps))
        all_plugins = (
            (
                "assimp_importer",
                (
                    "assimp_importer",
                    "AssimpImporter",
                    "AssimpImporter",
                    "importers",
                    ["magnum::trade", "assimp::assimp"],
                ),
            ),
            ("basis_imageconverter", ("basis_imageconverter", "--", "--", "--", [])),
            ("basis_importer", ("basis_importer", "--", "--", "--", [])),
            ("dds_importer", ("dds_importer", "DdsImporter", "DdsImporter", "importers", ["magnum::trade"])),
            ("devil_imageimporter", ("devil_imageimporter", "--", "--", "--", [])),
            (
                "drflac_audioimporter",
                (
                    "drflac_audioimporter",
                    "DrFlacAudioImporter",
                    "DrFlacAudioImporter",
                    "audioimporters",
                    ["magnum::audio"],
                ),
            ),
            (
                "drmp3_audioimporter",
                (
                    "drmp3_audioimporter",
                    "DrMp3AudioImporter",
                    "DrMp3AudioImporter",
                    "audioimporters",
                    ["magnum::audio"],
                ),
            ),
            (
                "drwav_audioimporter",
                (
                    "drwav_audioimporter",
                    "DrWavAudioImporter",
                    "DrWavAudioImporter",
                    "audioimporters",
                    ["magnum::audio"],
                ),
            ),
            ("faad2_audioimporter", ("faad2_audioimporter", "--", "--", "--", [])),
            (
                "freetype_font",
                (
                    "freetype_font",
                    "FreeTypeFont",
                    "FreeTypeFont",
                    "fonts",
                    ["magnum::text", "freetype::freetype"],
                ),
            ),
            (
                "harfbuzz_font",
                (
                    "harfbuzz_font",
                    "HarfBuzzFont",
                    "HarfBuzzFont",
                    "fonts",
                    ["magnum::text", "harfbuzz::harfbuzz"],
                ),
            ),
            (
                "jpeg_imageconverter",
                (
                    "jpeg_imageconverter",
                    "JpegImageConverter",
                    "JpegImageConverter",
                    "imageconverters",
                    ["magnum::trade", "libjpeg::libjpeg"],
                ),
            ),
            (
                "jpeg_importer",
                (
                    "jpeg_importer",
                    "JpegImporter",
                    "JpegImporter",
                    "importers",
                    ["magnum::trade", "libjpeg::libjpeg"],
                ),
            ),
            (
                "meshoptimizer_sceneconverter",
                (
                    "meshoptimizer_sceneconverter",
                    "MeshOptimizerSceneConverter",
                    "MeshOptimizerSceneConverter",
                    "sceneconverters",
                    ["magnum::trade", "magnum::mesh_tools", "meshoptimizer::meshoptimizer"],
                ),
            ),
            (
                "miniexr_imageconverter",
                (
                    "miniexr_imageconverter",
                    "MiniExrImageConverter",
                    "MiniExrImageConverter",
                    "imageconverters",
                    ["magnum::trade"],
                ),
            ),
            (
                "opengex_importer",
                (
                    "opengex_importer",
                    "OpenGexImporter",
                    "OpenGexImporter",
                    "importers",
                    ["magnum::trade", "magnumopenddl", "magnum::any_image_importer"],
                ),
            ),
            (
                "png_importer",
                (
                    "png_importer",
                    "PngImporter",
                    "PngImporter",
                    "importers",
                    ["magnum::trade", "libpng::libpng"],
                ),
            ),
            (
                "png_imageconverter",
                (
                    "png_imageconverter",
                    "PngImageConverter",
                    "PngImageConverter",
                    "imageconverters",
                    ["magnum::trade"],
                ),
            ),
            (
                "primitive_importer",
                (
                    "primitive_importer",
                    "PrimitiveImporter",
                    "PrimitiveImporter",
                    "importers",
                    ["magnum::primitives", "magnum::trade"],
                ),
            ),
            (
                "stanford_importer",
                (
                    "stanford_importer",
                    "StanfordImporter",
                    "StanfordImporter",
                    "importers",
                    ["magnum::mesh_tools", "magnum::trade"],
                ),
            ),
            (
                "stanford_sceneconverter",
                (
                    "stanford_sceneconverter",
                    "StanfordSceneConverter",
                    "StanfordSceneConverter",
                    "sceneconverters",
                    ["magnum::mesh_tools", "magnum::trade"],
                ),
            ),
            (
                "stb_imageconverter",
                (
                    "stb_imageconverter",
                    "StbImageConverter",
                    "StbImageConverter",
                    "imageconverters",
                    ["magnum::trade"],
                ),
            ),
            (
                "stb_imageimporter",
                ("stb_imageimporter", "StbImageImporter", "StbImageImporter", "importers", ["magnum::trade"]),
            ),
            (
                "stbtruetype_font",
                ("stbtruetype_font", "StbTrueTypeFont", "StbTrueTypeFont", "fonts", ["magnum::text"]),
            ),
            (
                "stbvorbis_audioimporter",
                (
                    "stbvorbis_audioimporter",
                    "StbVorbisAudioImporter",
                    "StbVorbisAudioImporter",
                    "audioimporters",
                    ["magnum::audio"],
                ),
            ),
            (
                "tinygltf_importer",
                (
                    "tinygltf_importer",
                    "TinyGltfImporter",
                    "TinyGltfImporter",
                    "importers",
                    ["magnum::trade", "magnum::any_image_importer"],
                ),
            ),
            (
                "stl_importer",
                (
                    "stl_importer",
                    "StlImporter",
                    "StlImporter",
                    "importers",
                    ["magnum::mesh_tools", "magnum::trade"],
                ),
            ),
        )
        return [plugin for opt_name, plugin in all_plugins if self.options.get_safe(opt_name)]
