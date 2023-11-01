import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os, fix_apple_shared_install_name
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy, rm, rmdir, replace_in_file, save
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class OpenColorIOConan(ConanFile):
    name = "opencolorio"
    description = "A color management framework for visual effects and animation."
    license = "BSD-3-Clause"
    homepage = "https://opencolorio.org/"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("colors", "visual", "effects", "animation")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_apps": [True, False],
        "use_sse": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_apps": False,
        "use_sse": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.arch not in ["x86", "x86_64"]:
            del self.options.use_sse

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.options["minizip-ng"].with_zlib = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("expat/2.5.0")
        self.requires("yaml-cpp/0.8.0")
        if self.options.build_apps:
            self.requires("lcms/2.14")
            # TODO: add GLUT (needed for ociodisplay tool)
        if Version(self.version).major >= 2:
            self.requires("imath/3.1.9")
            self.requires("pystring/1.1.4")
            self.requires("minizip-ng/3.0.9")
            if self.options.build_apps:
                self.requires("openexr/3.1.9")
        else:
            self.requires("openexr/2.5.7")
            self.requires("tinyxml/2.6.2")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)

        # opencolorio>=2.2.0 requires minizip-ng with with_zlib
        if Version(self.version) >= "2.2.0" and not self.dependencies["minizip-ng"].options.get_safe("with_zlib", False):
            raise ConanInvalidConfiguration(f"{self.ref} requires minizip-ng with with_zlib = True.")

    def build_requirements(self):
        if Version(self.version) >= "2.2.0":
            self.tool_requires("cmake/[>=3.16 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OCIO_USE_SSE"] = self.options.get_safe("use_sse", False)

        # openexr 2.x provides Half library
        tc.variables["OCIO_USE_OPENEXR_HALF"] = True

        tc.variables["OCIO_BUILD_APPS"] = self.options.build_apps
        tc.variables["OCIO_BUILD_DOCS"] = False
        tc.variables["OCIO_BUILD_TESTS"] = False
        tc.variables["OCIO_BUILD_GPU_TESTS"] = False
        tc.variables["OCIO_USE_BOOST_PTR"] = False
        tc.variables["OCIO_BUILD_PYTHON"] = False

        # avoid downloading dependencies
        tc.variables["OCIO_INSTALL_EXT_PACKAGE"] = "NONE"

        if is_msvc(self) and not self.options.shared:
            # define any value because ifndef is used
            tc.variables["OpenColorIO_SKIP_IMPORTS"] = True

        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0091"] = "NEW"

        if Version(self.version) < "2.1.0":
            tc.variables["OCIO_BUILD_SHARED"] = self.options.shared
            tc.variables["OCIO_BUILD_STATIC"] = not self.options.shared
            tc.variables["OCIO_BUILD_PYGLUE"] = False
            tc.variables["USE_EXTERNAL_YAML"] = True
            tc.variables["USE_EXTERNAL_TINYXML"] = True
            tc.variables["TINYXML_OBJECT_LIB_EMBEDDED"] = False
            tc.variables["USE_EXTERNAL_LCMS"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("minizip-ng", "cmake_file_name", "minizip-ng")
        deps.set_property("minizip-ng", "cmake_target_name", "MINIZIP::minizip-ng")
        deps.set_property("lcms", "cmake_file_name", "lcms2")
        deps.set_property("lcms", "cmake_target_name", "lcms2::lcms2")
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

        for module in ("expat", "lcms2", "pystring", "yaml-cpp", "Imath", "minizip-ng"):
            rm(self, f"Find{module}.cmake", os.path.join(self.source_folder, "share", "cmake", "modules"))

        if Version(self.version).major >= 2:
            # Remove CMAKE_CXX_STANDARD cache variable
            replace_in_file(self, os.path.join(self.source_folder, "share", "cmake", "utils", "CppVersion.cmake"),
                            "set_property(CACHE CMAKE_CXX_STANDARD", "#")

            # Disable installation of deleted CMake modules
            replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                            "if (NOT BUILD_SHARED_LIBS)", "if (0)")

            # Fix pystring.h include path
            for path in self.source_path.joinpath("src", "OpenColorIO").rglob("*.cpp"):
                content = path.read_text(encoding="utf-8")
                if "pystring/pystring.h" in content:
                    content = content.replace("pystring/pystring.h", "pystring.h")
                    path.write_text(content, encoding="utf-8")

            # Fix yaml-cpp dependency
            save(self, os.path.join(self.source_folder, "src", "OpenColorIO", "CMakeLists.txt"),
                 "\ntarget_include_directories(OpenColorIO PRIVATE ${yaml-cpp_INCLUDE_DIRS})"
                 "\ntarget_link_libraries(OpenColorIO PRIVATE ${yaml-cpp_LIBS})", append=True)

        if Version(self.version) >= "2.3.0":
            # Workaround for the invalid octal value 030009 in MZ_VERSION_BUILD for v3.0.9
            mz_v4 = 1 if Version(self.dependencies["minizip-ng"].ref.version) >= "4.0.0" else 0
            for file in [
                os.path.join(self.source_folder, "src", "apps", "ocioarchive", "main.cpp"),
                os.path.join(self.source_folder, "src", "OpenColorIO", "OCIOZArchive.cpp"),
            ]:
                replace_in_file(self, file, "#if MZ_VERSION_BUILD >= 040000", f"#if {mz_v4}")

    def build(self):
        self._patch_sources()
        cm = CMake(self)
        cm.configure()
        cm.build()

    def package(self):
        cm = CMake(self)
        cm.install()

        if not self.options.shared:
            copy(self, "*",
                 src=os.path.join(self.package_folder, "lib", "static"),
                 dst=os.path.join(self.package_folder, "lib"))
            rmdir(self, os.path.join(self.package_folder, "lib", "static"))

        rmdir(self, os.path.join(self.package_folder, "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        # nop for 2.x
        rm(self, "OpenColorIOConfig*.cmake", self.package_folder)

        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

        if Version(self.version) == "1.1.1":
            fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenColorIO")
        self.cpp_info.set_property("cmake_target_name", "OpenColorIO::OpenColorIO")
        self.cpp_info.set_property("pkg_config_name", "OpenColorIO")

        self.cpp_info.libs = ["OpenColorIO"]

        if Version(self.version) < "2.1.0":
            if not self.options.shared:
                self.cpp_info.defines.append("OpenColorIO_STATIC")

        if is_apple_os(self):
            self.cpp_info.frameworks.extend(["Foundation", "IOKit", "ColorSync", "CoreGraphics"])

        if is_msvc(self) and not self.options.shared:
            self.cpp_info.defines.append("OpenColorIO_SKIP_IMPORTS")

        # TODO: to remove in conan v2 once cmake_find_package_* & pkg_config generators removed
        self.cpp_info.names["cmake_find_package"] = "OpenColorIO"
        self.cpp_info.names["cmake_find_package_multi"] = "OpenColorIO"
        bin_path = os.path.join(self.package_folder, "bin")
        self.env_info.PATH.append(bin_path)
