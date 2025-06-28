import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime

required_conan_version = ">=2.1"


class OpenImageIOConan(ConanFile):
    name = "openimageio"
    description = (
        "OpenImageIO is a library for reading and writing images, and a bunch "
        "of related classes, utilities, and applications. There is a "
        "particular emphasis on formats and functionality used in "
        "professional, large-scale animation and visual effects work for film."
    )
    topics = ("vfx", "image", "picture")
    license = "Apache-2.0 AND BSD-3-Clause"
    homepage = "http://www.openimageio.org/"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_dicom": [True, False],
        "with_ffmpeg": [True, False],
        "with_freetype": [True, False],
        "with_giflib": [True, False],
        "with_hdf5": [True, False],
        "with_libheif": [True, False],
        "with_libjxl": [True, False],
        "with_libpng": [True, False],
        "with_libultrahdr": [True, False],
        "with_libwebp": [True, False],
        "with_opencv": [True, False],
        "with_openjpeg": [True, False],
        "with_openvdb": [True, False],
        "with_ptex": [True, False],
        "with_raw": [True, False],
        "with_tbb": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_dicom": False,
        "with_ffmpeg": False,
        "with_freetype": False,
        "with_giflib": True,
        "with_hdf5": False,
        "with_libheif": False,
        "with_libjxl": False,
        "with_libpng": True,
        "with_libultrahdr": True,
        "with_libwebp": True,
        "with_openjpeg": True,
        "with_openvdb": False,
        "with_opencv": False,
        "with_ptex": False,
        "with_raw": False,
        "with_tbb": True,

        "opencv/*:videoio": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def requirements(self):
        # Required libraries
        self.requires("zlib-ng/[^2.0]")
        self.requires("libtiff/[>=4.5 <5]")
        self.requires("imath/[^3.1.9]", transitive_headers=True)
        self.requires("openexr/[^3.3.3]")
        self.requires("libjpeg-meta/latest")
        self.requires("pugixml/[^1.15]")
        self.requires("tsl-robin-map/[^1.3.0]")
        self.requires("fmt/[>=7]", transitive_headers=True)
        self.requires("opencolorio/[^2.4.2]")

        # Optional libraries
        if self.options.with_libjxl:
            self.requires("libjxl/0.11.1")
        if self.options.with_libpng:
            self.requires("libpng/[~1.6]")
        if self.options.with_freetype:
            self.requires("freetype/[^2.13.2]")
        if self.options.with_hdf5:
            self.requires("hdf5/[^1.8]")
        if self.options.with_opencv:
            self.requires("opencv/[^4.5]")
        if self.options.with_tbb:
            self.requires("onetbb/[>=2021 <2023]")
        if self.options.with_dicom:
            self.requires("dcmtk/[^3.6.8]")
        if self.options.with_ffmpeg:
            self.requires("ffmpeg/[>=6 <8]")
        if self.options.with_giflib:
            self.requires("giflib/[^5.2.1]")
        if self.options.with_libheif:
            self.requires("libheif/[^1.19.5]")
        if self.options.with_raw:
            self.requires("libraw/[>=0.21.3 <1]")
        if self.options.with_openjpeg:
            self.requires("openjpeg/[^2.5.2]")
        if self.options.with_openvdb:
            self.requires("openvdb/[^11.0.0]")
        if self.options.with_ptex:
            self.requires("ptex/2.4.2")
        if self.options.with_libwebp:
            self.requires("libwebp/[^1.3.2]")
        if self.options.with_libultrahdr:
            self.requires("libultrahdr/[^1.4.0]")

        # TODO: Field3D dependency
        # TODO: R3DSDK dependency
        # TODO: Nuke dependency

    def build_requirements(self):
        self.build_requires("cmake/[>=3.18.2 <5]")

    def validate(self):
        check_min_cppstd(self, 17)
        if is_msvc_static_runtime(self) and self.options.shared:
            raise ConanInvalidConfiguration("Building shared library with static runtime is not supported!")
        if self.options.with_opencv and not self.dependencies["opencv"].options.videoio:
            raise ConanInvalidConfiguration("-o opencv/*:videoio=True is required for with_opencv=True")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        rmdir(self, "src/cmake/modules")
        save(self, "src/testtex/CMakeLists.txt", "")
        # Disable Python
        replace_in_file(self, "src/cmake/externalpackages.cmake", "find_python()", "")
        # Inject fmt and tsl-robin-map dependencies
        replace_in_file(self, "src/libutil/CMakeLists.txt",
                        "$<TARGET_NAME_IF_EXISTS:Threads::Threads>",
                        "$<TARGET_NAME_IF_EXISTS:Threads::Threads> fmt::fmt tsl::robin_map")

    def generate(self):
        tc = CMakeToolchain(self)

        # CMake options
        tc.variables["CMAKE_DEBUG_POSTFIX"] = ""  # Needed for 2.3.x.x+ versions
        tc.variables["OIIO_BUILD_TOOLS"] = True
        tc.variables["OIIO_BUILD_TESTS"] = False
        tc.variables["BUILD_TESTING"] = False
        tc.variables["BUILD_DOCS"] = False
        tc.variables["INSTALL_DOCS"] = False
        tc.variables["INSTALL_FONTS"] = False
        tc.variables["INSTALL_CMAKE_HELPER"] = False
        tc.variables["EMBEDPLUGINS"] = True
        tc.variables["USE_EXTERNAL_PUGIXML"] = True
        tc.variables["BUILD_MISSING_FMT"] = False
        tc.variables["OIIO_INTERNALIZE_FMT"] = False

        tc.variables["USE_LIBHEIF"] = self.options.with_libheif
        tc.variables["USE_PTEX"] = self.options.with_ptex

        if self.options.with_libultrahdr:
            tc.variables["LIBUHDR_INCLUDE_DIR"] = self.dependencies["libultrahdr"].cpp_info.includedir.replace("\\", "/")

        # Override variable for internal linking visibility of Imath otherwise not visible
        # in the tools included in the build that consume the library.
        tc.cache_variables["OPENIMAGEIO_IMATH_DEPENDENCY_VISIBILITY"] = "PUBLIC"
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("ffmpeg", "cmake_file_name", "FFmpeg")
        deps.set_property("ffmpeg", "cmake_", "FFmpeg")
        deps.set_property("ffmpeg", "cmake_additional_variables_prefixes", ["FFMPEG"])
        deps.set_property("libjxl", "cmake_file_name", "JXL")
        deps.set_property("openexr", "cmake_target_name", "OpenEXR::OpenEXR")
        deps.set_property("openjpeg", "cmake_target_name", "OpenJPEG")
        deps.set_property("openjpeg", "cmake_additional_variables_prefixes", ["OPENJPEG"])
        deps.set_property("openvdb", "cmake_target_name", "OpenVDB")
        deps.set_property("openvdb", "cmake_additional_variables_prefixes", ["OPENVDB"])
        deps.set_property("libultrahdr", "cmake_file_name", "libuhdr")
        deps.set_property("libultrahdr", "cmake_target_name", "libuhdr::libuhdr")
        deps.set_property("tsl-robin-map", "cmake_file_name", "Robinmap")
        if self.dependencies["fmt"].options.header_only:
            deps.set_property("fmt", "cmake_target_name", "fmt::fmt")
        else:
            deps.set_property("fmt", "cmake_target_aliases", ["fmt::fmt-header-only"])
        deps.generate()

    def _enable_disable(self, name, condition):
        externalpackages_cmake = os.path.join(self.source_folder, "src/cmake/externalpackages.cmake")
        if condition:
            replace_in_file(self, externalpackages_cmake,
                            f"checked_find_package ({name}",
                            f"checked_find_package ({name} REQUIRED ")
        else:
            replace_in_file(self, externalpackages_cmake,
                            f"checked_find_package ({name}",
                            f"message(TRACE disabled {name}")

    def _patch_sources(self):
        self._enable_disable("JPEG", True)
        self._enable_disable("libjpeg-turbo", False)
        self._enable_disable("JXL", self.options.with_libjxl)
        self._enable_disable("Freetype", self.options.with_freetype)
        self._enable_disable("OpenColorIO", True)
        self._enable_disable("OpenCV", self.options.with_opencv)
        self._enable_disable("TBB", self.options.with_tbb)
        self._enable_disable("DCMTK", self.options.with_dicom)
        self._enable_disable("FFmpeg", self.options.with_ffmpeg)
        self._enable_disable("GIF", self.options.with_giflib)
        self._enable_disable("Libheif", self.options.with_libheif)
        self._enable_disable("LibRaw", self.options.with_raw)
        self._enable_disable("OpenJPEG", self.options.with_openjpeg)
        self._enable_disable("OpenVDB", self.options.with_openvdb)
        self._enable_disable("Ptex", self.options.with_ptex)
        self._enable_disable("WebP", self.options.with_libwebp)
        self._enable_disable("R3DSDK", False)
        self._enable_disable("Nuke", False)
        self._enable_disable("OpenGL", False)
        self._enable_disable("Qt6", False)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        if self.settings.os == "Windows":
            for vc_file in ("concrt", "msvcp", "vcruntime"):
                rm(self, f"{vc_file}*.dll", os.path.join(self.package_folder, "bin"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    @staticmethod
    def _conan_comp(name):
        return f"openimageio_{name.lower()}"

    def _add_component(self, name):
        component = self.cpp_info.components[self._conan_comp(name)]
        component.set_property("cmake_target_name", f"OpenImageIO::{name}")
        return component

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenImageIO")
        self.cpp_info.set_property("pkg_config_name", "OpenImageIO")

        # OpenImageIO::OpenImageIO_Util
        open_image_io_util = self._add_component("OpenImageIO_Util")
        open_image_io_util.libs = ["OpenImageIO_Util"]
        open_image_io_util.requires = [
            "imath::imath",
            "openexr::openexr",
        ]
        if self.settings.os in ["Linux", "FreeBSD"]:
            open_image_io_util.system_libs.extend(["dl", "m", "pthread"])
        if self.options.with_tbb:
            open_image_io_util.requires.append("onetbb::onetbb")

        # OpenImageIO::OpenImageIO
        open_image_io = self._add_component("OpenImageIO")
        open_image_io.libs = ["OpenImageIO"]
        open_image_io.requires = [
            "openimageio_openimageio_util",
            "zlib-ng::zlib-ng",
            "libtiff::libtiff",
            "pugixml::pugixml",
            "tsl-robin-map::tsl-robin-map",
            "fmt::fmt",
            "imath::imath",
            "openexr::openexr",
            "opencolorio::opencolorio",
        ]

        open_image_io.requires.append("libjpeg-meta::jpeg")
        if self.options.with_libjxl:
            open_image_io.requires += ["libjxl::libjxl", "libjxl::jxl_cms"]
        if self.options.with_libpng:
            open_image_io.requires.append("libpng::libpng")
        if self.options.with_freetype:
            open_image_io.requires.append("freetype::freetype")
        if self.options.with_hdf5:
            open_image_io.requires.append("hdf5::hdf5")
        if self.options.with_opencv:
            open_image_io.requires.append("opencv::opencv")
        if self.options.with_dicom:
            open_image_io.requires.append("dcmtk::dcmtk")
        if self.options.with_ffmpeg:
            open_image_io.requires.append("ffmpeg::ffmpeg")
        if self.options.with_giflib:
            open_image_io.requires.append("giflib::giflib")
        if self.options.with_libheif:
            open_image_io.requires.append("libheif::libheif")
        if self.options.with_raw:
            open_image_io.requires.append("libraw::libraw")
        if self.options.with_openjpeg:
            open_image_io.requires.append("openjpeg::openjpeg")
        if self.options.with_openvdb:
            open_image_io.requires.append("openvdb::openvdb")
        if self.options.with_ptex:
            open_image_io.requires.append("ptex::ptex")
        if self.options.with_libwebp:
            open_image_io.requires.append("libwebp::libwebp")
        if self.options.with_libultrahdr:
            open_image_io.requires.append("libultrahdr::libultrahdr")
        if self.settings.os in ["Linux", "FreeBSD"]:
            open_image_io.system_libs.extend(["dl", "m", "pthread"])

        if not self.options.shared:
            open_image_io.defines.append("OIIO_STATIC_DEFINE")
