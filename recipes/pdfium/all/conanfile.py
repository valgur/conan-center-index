import os
import re
import shutil
import textwrap

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os, XCRun
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv, Environment
from conan.tools.files import copy, get, save, replace_in_file
from conan.tools.gnu import AutotoolsToolchain, AutotoolsDeps
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class PdfiumConan(ConanFile):
    name = "pdfium"
    description = "PDF generation and rendering library."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://opensource.google/projects/pdfium"
    topics = ("generate", "generation", "rendering", "pdf", "document", "print")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_libjpeg": ["libjpeg", "libjpeg-turbo"],
        "enable_v8": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_libjpeg": "libjpeg",
        "enable_v8": True,
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("abseil/20230125.3")
        self.requires("freetype/2.13.0")
        self.requires("icu/74.1")
        self.requires("lcms/2.14")
        self.requires("openjpeg/2.5.0")
        if self.options.with_libjpeg == "libjpeg":
            self.requires("libjpeg/9e")
        elif self.options.with_libjpeg == "libjpeg-turbo":
            self.requires("libjpeg-turbo/3.0.0")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 14)
        minimum_compiler_versions = {
            "gcc": "8",
            "msvc": "191",
            "Visual Studio": "15",
        }
        min_compiler_version = minimum_compiler_versions.get(str(self.settings.compiler))
        if min_compiler_version and Version(self.settings.compiler.version) < min_compiler_version:
            raise ConanInvalidConfiguration(
                f"pdfium needs at least compiler version {min_compiler_version}"
            )

    def build_requirements(self):
        self.tool_requires("gn/cci.20210429")
        self.tool_requires("ninja/1.11.1")
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/2.0.3")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["pdfium"],
            destination=self.source_folder)
        get(self, **self.conan_data["sources"][self.version]["partition_allocator"],
            destination=os.path.join(self.source_folder, "base", "allocator", "partition_allocator"))
        get(self, **self.conan_data["sources"][self.version]["trace_event"],
            destination=os.path.join(self.source_folder, "base", "trace_event", "common"))
        get(self, **self.conan_data["sources"][self.version]["chromium_build"],
            destination=os.path.join(self.source_folder, "build"))

    @property
    def _gn_os(self):
        if self.settings.os == "Windows":
            return "win"
        elif self.settings.os == "Macos":
            return "mac"
        elif is_apple_os(self):
            return "ios"
        return str(self.settings.os).lower()

    @property
    def _gn_arch(self):
        return {
            "x86_64": "x64",
            "armv8": "arm64",
            "x86": "x86",
        }.get(str(self.settings.arch), str(self.settings.arch))

    def _generate_args_gn(self, gn_args):
        formatted_args = {}
        for k, v in gn_args.items():
            if isinstance(v, bool):
                formatted_args[k] = "true" if v else "false"
            elif isinstance(v, str):
                formatted_args[k] = f'"{v}"'
        save(self, os.path.join(self.build_folder, "args.gn"),
             "\n".join(f"{k} = {v}" for k, v in formatted_args.items()))

    @property
    def _cxx(self):
        compilers_by_conf = self.conf.get("tools.build:compiler_executables", default={}, check_type=dict)
        cxx = compilers_by_conf.get("cpp") or VirtualBuildEnv(self).vars().get("CXX")
        if cxx:
            return cxx
        if self.settings.compiler == "apple-clang":
            return XCRun(self).cxx
        compiler_version = self.settings.compiler.version
        major = Version(compiler_version).major
        if self.settings.compiler == "gcc":
            return shutil.which(f"g++-{compiler_version}") or shutil.which(f"g++-{major}") or shutil.which("g++") or ""
        if self.settings.compiler == "clang":
            return shutil.which(f"clang++-{compiler_version}") or shutil.which(f"clang++-{major}") or shutil.which("clang++") or ""
        return ""

    def generate(self):
        VirtualBuildEnv(self).generate()
        VirtualRunEnv(self).generate(scope="build")

        tc = AutotoolsToolchain(self)
        deps = AutotoolsDeps(self)

        def _get_flags(name):
            return " ".join(filter(None, [tc.vars().get(name), deps.vars().get(name)]))

        env = Environment()
        env.define("CXX", self._cxx)
        env.vars(self).save_script("conanbuild_gn")

        gn_args = {}
        # General GN args
        gn_args["extra_cflags"] = _get_flags("CPPFLAGS") + "".join(f" -I{inc}" for inc in self.dependencies["abseil"].cpp_info.aggregated_components().includedirs)
        gn_args["extra_cflags_c"] = _get_flags("CFLAGS")
        gn_args["extra_cflags_cc"] = _get_flags("CXXFLAGS")
        gn_args["extra_ldflags"] = _get_flags("LDFLAGS") + " " + _get_flags("LIBS")
        gn_args["target_os"] = self._gn_os
        gn_args["target_cpu"] = self._gn_arch
        gn_args["is_debug"] = self.settings.build_type == "Debug"
        # Pdfium args
        gn_args["use_custom_libcxx"] = False
        gn_args["is_clang"] = False
        # pdfium args based on https://github.com/bblanchon/pdfium-binaries/blob/60429bf0d/steps/05-configure.sh
        gn_args["pdf_is_standalone"] = True
        gn_args["pdf_enable_v8"] = False
        gn_args["pdf_enable_xfa"] = False
        gn_args["treat_warnings_as_errors"] = False
        gn_args["is_component_build"] = False
        if self.settings.os == "iOS":
            gn_args["ios_enable_code_signing"] = False
            gn_args["use_blink"] = True
        elif self.settings.os == "Linux":
            gn_args["use_allocator_shim"] = False
        elif self.settings.os == "Macos":
            gn_args["use_allocator_shim"] = False
            gn_args["mac_deployment_target"] = "10.13.0"
        elif self.settings.os == "Emscripten":
            gn_args["pdf_is_complete_lib"] = True
            gn_args["pdf_use_partition_alloc"] = False
        self._generate_args_gn(gn_args)

        save(self, os.path.join(self.source_folder, "build", "config", "gclient_args.gni"),
             "\n".join([
                 "checkout_android = false",
                 "checkout_skia = false",
             ])
        )

    def build(self):
        save(self, os.path.join(self.source_folder, "third_party", "BUILD.gn"), textwrap.dedent("""\
                import("//build/config/arm.gni")
                import("//build/config/linux/pkg_config.gni")
                import("//build/config/mips.gni")
                import("//build_overrides/build.gni")
                import("../pdfium.gni")

                config("pdfium_third_party_config") {
                  configs = [
                    "..:pdfium_common_config",
                    "..:pdfium_public_config",
                  ]
                }

                source_set("bigint") {}
                config("freetype_public_includes_config") {}
                config("freetype_private_config") {}
                source_set("fx_freetype") {}
                config("system_fontconfig") {}
                group("fontconfig") {}
                config("fx_agg_warnings") {}
                source_set("fx_agg") {}
                config("fx_lcms2_warnings") {}
                source_set("fx_lcms2") {}
                config("system_libjpeg_config") {}
                config("libjpeg_turbo_config") {}
                source_set("jpeg") {}
                source_set("png") {}
                config("system_zlib_config") {}
                group("zlib") {}
                group("lcms2") {}
                group("libopenjpeg2") {}
                config("fx_libopenjpeg_warnings") {}
                source_set("fx_libopenjpeg") {}
                config("system_libpng_config") {}
                source_set("fx_tiff") {}

                source_set("pdfium_compiler_specific") {
                  configs -= [ "//build/config/compiler:chromium_code" ]
                  configs += [
                    "//build/config/compiler:no_chromium_code",
                    ":pdfium_third_party_config",
                  ]
                  sources = [ "base/compiler_specific.h" ]
                }

                source_set("pdfium_base") {
                  configs -= [ "//build/config/compiler:chromium_code" ]
                  configs += [
                    "//build/config/compiler:no_chromium_code",
                    ":pdfium_third_party_config",
                  ]
                  sources = [
                    "base/bits.h",
                    "base/check.h",
                    "base/check_op.h",
                    "base/component_export.h",
                    "base/containers/adapters.h",
                    "base/containers/contains.h",
                    "base/containers/span.h",
                    "base/debug/alias.cc",
                    "base/debug/alias.h",
                    "base/immediate_crash.h",
                    "base/memory/aligned_memory.cc",
                    "base/memory/aligned_memory.h",
                    "base/memory/ptr_util.h",
                    "base/no_destructor.h",
                    "base/notreached.h",
                    "base/numerics/checked_math.h",
                    "base/numerics/checked_math_impl.h",
                    "base/numerics/clamped_math.h",
                    "base/numerics/clamped_math_impl.h",
                    "base/numerics/safe_conversions.h",
                    "base/numerics/safe_conversions_arm_impl.h",
                    "base/numerics/safe_conversions_impl.h",
                    "base/numerics/safe_math.h",
                    "base/numerics/safe_math_arm_impl.h",
                    "base/numerics/safe_math_clang_gcc_impl.h",
                    "base/numerics/safe_math_shared_impl.h",
                    "base/sys_byteorder.h",
                    "base/template_util.h",
                  ]
                  public_deps = [
                    ":pdfium_compiler_specific",
                    "//third_party/abseil-cpp:absl",
                  ]
                  if (pdf_use_partition_alloc) {
                    public_deps +=
                        [ "//base/allocator/partition_allocator/src/partition_alloc:raw_ptr" ]
                  }
                  if (is_win) {
                    sources += [
                      "base/win/scoped_select_object.h",
                      "base/win/win_util.cc",
                      "base/win/win_util.h",
                    ]
                  }
                }

                source_set("pdfium_base_test_support") {
                  testonly = true
                  sources = []
                  configs += [
                    "../:pdfium_strict_config",
                    "../:pdfium_noshorten_config",
                  ]
                  deps = []
                  if (is_posix || is_fuchsia) {
                    sources += [
                      "base/test/scoped_locale.cc",
                      "base/test/scoped_locale.h",
                    ]
                    deps += [ "//testing/gtest" ]
                  }
                }
                """))
        for third_party in ["abseil-cpp", "agg23", "bigint", "cpu_features", "depot_tools", "freetype", "fuchsia-sdk", "googletest", "icu", "instrumented_libraries", "jinja2", "lcms", "libc++", "libc++abi", "libjpeg_turbo", "libopenjpeg", "libpng", "libtiff", "libunwind", "llvm-build", "markupsafe", "nasm", "ninja", "NotoSansCJK", "pymock", "skia", "test_fonts", "zlib"]:
            save(self, os.path.join(self.source_folder, "third_party", third_party, "BUILD.gn"),
                 "\n".join([f'source_set("{x}") {{}}' for x in ["icuuc", "test_fonts", "gmock", "gmock_main", "gtest", "gtest_main", "absl"]]))
        save(self, os.path.join(self.source_folder, "build", "config", "sysroot.gni"),
             'sysroot = ""\ntarget_sysroot = ""\nuse_sysroot = false')

        for path in list(self.source_path.joinpath("core").rglob("*.cpp")) + list(self.source_path.joinpath("core").rglob("*.h")):
            content = path.read_text(encoding="utf-8")
            content, n = re.subn("third_party/(?!base)[^/]+/", "", content)
            if n:
                path.write_text(content, encoding="utf-8")

        self.run(f'gn gen "{self.build_folder}"', cwd=self.source_folder)
        self.run(f"ninja -C {self.build_folder} pdfium")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["pdfium"]
        if is_apple_os(self):
            self.cpp_info.frameworks.extend(["Appkit", "CoreFoundation", "CoreGraphics"])

        stdcpp_library = stdcpp_library(self)
        if stdcpp_library:
            self.cpp_info.system_libs.append(stdcpp_library)
