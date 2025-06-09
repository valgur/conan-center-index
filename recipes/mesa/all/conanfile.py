import glob
import os
import re
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name, is_apple_os
from conan.tools.build import check_min_cppstd, check_max_cppstd, cross_building
from conan.tools.cmake import CMakeDeps
from conan.tools.env import Environment
from conan.tools.files import *
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


datasources = ["freedreno", "intel", "panfrost"]
freedreno_kmds = ["kgsl", "msm", "virtio"]
gallium_drivers = ["asahi", "crocus", "d3d12", "etnaviv", "freedreno", "i915", "iris", "lima", "llvmpipe", "nouveau", "panfrost", "r300", "r600", "radeonsi", "softpipe", "svga", "tegra", "v3d", "vc4", "virgl", "zink"]
platforms = ["x11", "wayland", "haiku", "android", "windows", "macos"]
tools = ["drm_shim", "etnaviv", "freedreno", "glsl", "intel", "intel_ui", "nir", "nouveau", "lima", "panfrost", "asahi", "imagination"]
video_codecs = ["av1dec", "av1enc", "h264dec", "h264enc", "h265dec", "h265enc", "vc1dec", "vp9dec"]
vulkan_drivers = ["amd", "broadcom", "freedreno", "intel", "intel_hasvk", "panfrost", "swrast", "virtio", "imagination_experimental", "microsoft_experimental", "nouveau", "asahi", "gfxstream"]
vulkan_layers = ["device_select", "intel_nullhw", "overlay", "screenshot", "vram_report_limit",]


class MesaConan(ConanFile):
    name = "mesa"
    description = "An open-source implementation of various graphics APIs."
    # https://docs.mesa3d.org/license.html#mesa-component-licenses
    # Note: patent concerns for the codec support in Mesa
    license = ("MIT", "BSD-3-Clause", "SGI-B-2.0")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://mesa3d.org/"
    topics = ("acceleration", "egl", "graphics", "opencl", "opengl", "opengles",
              "openmax", "va-api", "vdpau", "video", "vulkan")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    short_paths = True
    # Reduce the cost of copying a lot of source code.
    no_copy_source = True
    options = {
        "dri3": [True, False],
        "egl": [True, False],
        "egl_native_platform": ["android", "drm", "haiku", "surfaceless", "wayland", "windows", "x11"],
        "gallium_d3d10umd": [True, False],
        "gallium_d3d12_video": [True, False],
        "gallium_extra_hud": [True, False],
        "gallium_omx": [False, "bellagio", "tizonia"],
        "gallium_rusticl": [True, False],
        "gallium_va": [True, False],
        "gallium_vdpau": [True, False],
        "gbm": [True, False],
        "gles1": [True, False],
        "gles2": [True, False],
        "glx": [False, "dri", "xlib"],
        "imagination_srv": [True, False],
        "microsoft_clc": [True, False],
        "min_windows_version": ["7", "8", "10", "11"],
        "opencl_spirv": [True, False],
        "opengl": [True, False],
        "shader_cache": [True, False],
        "spirv_to_dxil": [True, False],
        "sse2": [True, False],
        "vmware_mks_stats": [True, False],
        "vulkan_beta": [True, False],
        "with_libelf": [True, False],
        "with_libglvnd": [True, False],
        "with_libudev": ["eudev", "systemd"],
        "with_libunwind": [True, False],
        "with_llvm": [True, False],
        # "with_lmsensors": [True, False],
        "with_perfetto": [True, False],
        "with_zstd": [True, False],
        "with_zlib": [True, False],
        "xmlconfig": [True, False],
    }
    options.update({f"datasource_{datasource}": [True, False] for datasource in datasources})
    options.update({f"freedreno_kmd_{freedreno_kmd}": [True, False] for freedreno_kmd in freedreno_kmds})
    options.update({f"gallium_driver_{gallium_driver}": [True, False] for gallium_driver in gallium_drivers})
    options.update({f"platform_{platform}": [True, False] for platform in platforms})
    options.update({f"tool_{tool}": [True, False] for tool in tools})
    options.update({f"video_codec_{video_codec}": [True, False] for video_codec in video_codecs})
    options.update({f"vulkan_driver_{vulkan_driver}": [True, False] for vulkan_driver in vulkan_drivers})
    options.update({f"vulkan_layer_{vulkan_layer}": [True, False] for vulkan_layer in vulkan_layers})

    default_options = {
        "dri3": True,
        "egl": True,
        "egl_native_platform": "wayland",
        "gallium_d3d10umd": False,
        "gallium_d3d12_video": False,
        "gallium_extra_hud": False,
        "gallium_omx": False,
        "gallium_rusticl": False,
        "gallium_va": True,
        "gallium_vdpau": True,
        "gbm": True,
        "gles1": True,
        "gles2": True,
        "glx": "dri",
        "imagination_srv": False,
        "microsoft_clc": True,
        "min_windows_version": "8",
        "opencl_spirv": False,
        "opengl": True,
        "spirv_to_dxil": False,
        "shader_cache": True,
        "sse2": True,
        "vmware_mks_stats": False,
        "vulkan_beta": False,
        "with_libelf": True,
        "with_libglvnd": True,
        "with_libudev": "systemd",
        "with_libunwind": True,
        "with_llvm": True,
        # "with_lmsensors": True,
        "with_perfetto": False,
        "with_zlib": True,
        "with_zstd": True,
        "xmlconfig": True,

        "llvm-core/*:target_AMDGPU": True,
        "llvm-core/*:target_NVPTX": True,
    }
    default_build_options = {
        "llvm-core/*:target_AMDGPU": True,
        "llvm-core/*:target_NVPTX": True,
    }
    default_options.update({f"datasource_{datasource}": False for datasource in datasources})
    default_options.update({f"freedreno_kmd_{freedreno_kmd}": freedreno_kmd == "msm" for freedreno_kmd in freedreno_kmds})
    default_options.update({f"gallium_driver_{gallium_driver}": False for gallium_driver in gallium_drivers})
    default_options.update({f"platform_{platform}": True for platform in platforms})
    default_options.update({f"tool_{tool}": False for tool in tools})
    default_options.update({f"video_codec_{video_codec}": False for video_codec in video_codecs})
    default_options.update({f"vulkan_driver_{vulkan_driver}": False for vulkan_driver in vulkan_drivers})
    default_options.update({f"vulkan_layer_{vulkan_layer}": True for vulkan_layer in vulkan_layers})

    @cached_property
    def _datasources(self):
        return set(ds for ds in datasources if self.options.get_safe(f"datasource_{ds}"))

    @cached_property
    def _freedreno_kmds(self):
        return set(kmd for kmd in freedreno_kmds if self.options.get_safe(f"freedreno_kmd_{kmd}"))

    @cached_property
    def _gallium_drivers(self):
        return set(d for d in gallium_drivers if self.options.get_safe(f"gallium_driver_{d}"))

    @cached_property
    def _platforms(self):
        return set(p for p in platforms if self.options.get_safe(f"platform_{p}"))

    @cached_property
    def _tools(self):
        return set(t for t in tools if self.options.get_safe(f"tool_{t}"))

    @cached_property
    def _video_codecs(self):
        return set(vc for vc in video_codecs if self.options.get_safe(f"video_codec_{vc}"))

    @cached_property
    def _vulkan_drivers(self):
        return set(d for d in vulkan_drivers if self.options.get_safe(f"vulkan_driver_{d}"))

    @cached_property
    def _vulkan_layers(self):
        return set(l for l in vulkan_layers if self.options.get_safe(f"vulkan_layer_{l}"))

    @cached_property
    def _requires_expat(self):
        return self.options.get_safe("xmlconfig") or self.options.tool_intel

    @cached_property
    def _requires_moltenvk(self):
        return is_apple_os(self) and "zink" in self._gallium_drivers

    @cached_property
    def _with_libdrm(self):
        return self.settings.os in ["Linux", "FreeBSD"]

    def _with_directx_headers(self):
        return (
            "d3d12" in self._gallium_drivers
            or self.options.get_safe("gallium_d3d12_video")
            or self.options.get_safe("microsoft_clc")
            or "microsoft_experimental" in self._vulkan_drivers
            or (self.settings.os == "Windows" and "zink" in self._gallium_drivers)
            or (self.settings.os == "Windows" and self._vulkan_drivers)
        )

    @cached_property
    def _default_egl_native_platform_option(self):
        if self.settings.os == "Android":
            return "android"
        if self.settings.os == "Linux":
            return "wayland"
        if self._system_has_kms_drm:
            return "drm"
        if is_apple_os(self):
            return "surfaceless"
        if self.settings.os == "Windows":
            return "windows"

    @cached_property
    def _default_glx_option(self):
        if self.settings.os in ["Android", "Windows"]:
            return False
        # https://github.com/Mesa3D/mesa/actions/runs/4754558919
        # The GLX dri option on macOS no longer builds.
        elif self.settings.os == "Macos":
            return "xlib"
        return "dri"

    @cached_property
    def _requires_libclc(self):
        return self.options.get_safe("gallium_rusticl") or self.options.get_safe("microsoft_clc")

    @cached_property
    def _is_arm_arch(self):
        return str(self.settings.arch).startswith("arm")

    @cached_property
    def _is_intel_arch(self):
        return self.settings.arch in ["x86", "x86_64"]

    @cached_property
    def _is_mips_arch(self):
        return self.settings.arch in ["mips", "mips64"]

    @cached_property
    def _system_has_kms_drm(self):
        return self.settings.os in ["Android", "FreeBSD", "Linux", "SunOS"]

    @cached_property
    def _with_any_opengl(self):
        return self.options.get_safe("opengl") or self.options.get_safe("gles1") or self.options.get_safe("gles2")

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if not self._system_has_kms_drm:
            self.options.rm_safe("dri3")
        if not self._system_has_kms_drm:
            self.options.rm_safe("gbm")
        if self.settings.os not in ["Linux", "Windows"]:
            self.options.rm_safe("microsoft_clc")
        if self.settings.os != "Windows":
            self.options.rm_safe("min_windows_version")
        if False:
            self.options.rm_safe("spirv_to_dxil")
        if self.settings.os == "Windows":
            self.options.rm_safe("shader_cache")
        if self.settings.os not in ["FreeBSD", "Linux"]:
            self.options.rm_safe("with_libglvnd")
        if self.settings.os != "Linux":
            self.options.rm_safe("with_libudev")
        if self.settings.os not in ["FreeBSD", "Linux"]:
            self.options.rm_safe("with_libunwind")
        if self.settings.os in ["Android", "Windows"]
            self.options.rm_safe("xmlconfig")

        if is_apple_os(self):
            self.options.rm_safe("egl")

        if self.settings.os == "Windows":
            self.options.rm_safe("gallium_vdpau")

        if self.settings.os != "Android":
            self.options.rm_safe("platform_android")
        if True:
            self.options.rm_safe("platform_haiku")
        if not self._system_has_kms_drm:
            self.options.rm_safe("platform_wayland")
        if not (self.settings.os == "Windows" and self.settings.get_safe("os.subsystem") is None):
            self.options.rm_safe("platform_windows")
        if not self._system_has_kms_drm and self.settings.os != "Macos" and self.settings.get_safe("os.subsystem") != "cygwin":
            self.options.rm_safe("platform_x11")
        if self.settings.os != "Macos":
            self.options.rm_safe("platform_macos")

        if is_apple_os(self):
            for vulkan_driver in vulkan_drivers:
                self.options.rm_safe(vulkan_driver)

        self.options.egl_native_platform = self._default_egl_native_platform_option

        self.options.gallium_driver_asahi = False
        self.options.gallium_driver_crocus = self._system_has_kms_drm and self._is_intel_arch
        self.options.gallium_driver_d3d12 = False
        self.options.gallium_driver_etnaviv = self._system_has_kms_drm and self._is_arm_arch
        self.options.gallium_driver_freedreno = self._system_has_kms_drm and self._is_arm_arch
        self.options.gallium_driver_i915 = self._system_has_kms_drm and self._is_intel_arch
        self.options.gallium_driver_iris = self._system_has_kms_drm and (self._is_arm_arch or self._is_intel_arch)
        self.options.gallium_driver_lima = self._system_has_kms_drm and self._is_arm_arch
        self.options.gallium_driver_nouveau = self._system_has_kms_drm
        self.options.gallium_driver_panfrost = self._system_has_kms_drm and self._is_arm_arch
        self.options.gallium_driver_r300 = self._system_has_kms_drm and (self._is_intel_arch or self._is_mips_arch)
        self.options.gallium_driver_r600 = self._system_has_kms_drm and (self._is_intel_arch or self._is_mips_arch)
        self.options.gallium_driver_radeonsi = self._system_has_kms_drm and (self._is_intel_arch or self._is_mips_arch)
        self.options.gallium_driver_svga = self._system_has_kms_drm and (self._is_arm_arch or self._is_intel_arch)
        self.options.gallium_driver_tegra = self._system_has_kms_drm and self._is_arm_arch
        self.options.gallium_driver_v3d = self._system_has_kms_drm and self._is_arm_arch
        self.options.gallium_driver_vc4 = self._system_has_kms_drm and self._is_arm_arch
        self.options.gallium_driver_virgl = self._system_has_kms_drm
        self.options.gallium_driver_zink = self.settings.os == "Macos"

        self.options.glx = self._default_glx_option

        self.options.opencl_spirv = bool(
            self.options.get_safe("gallium_rusticl")
            or self.options.get_safe("microsoft_clc")
        )

        self.options.vulkan_driver_amd = self._system_has_kms_drm and (self._is_intel_arch or self._is_mips_arch)
        self.options.vulkan_driver_broadcom = False
        self.options.vulkan_driver_freedreno = False
        self.options.vulkan_driver_imagination_experimental = False
        self.options.vulkan_driver_intel = self._system_has_kms_drm and (self._is_intel_arch or self._is_arm_arch)
        self.options.vulkan_driver_intel_hasvk = self._system_has_kms_drm and self._is_intel_arch
        self.options.vulkan_driver_microsoft_experimental = False
        self.options.vulkan_driver_nouveau = False
        self.options.vulkan_driver_panfrost = False
        self.options.vulkan_driver_swrast = (self._system_has_kms_drm or self.settings.os == "Windows") and (self._is_intel_arch or self._is_mips_arch or self._is_arm_arch)
        self.options.vulkan_driver_virtio = False

        self.options.vulkan_layer_device_select = not (self.settings.os == "Windows" and self.settings.get_safe("os.subsystem") is None) and self.settings.os != "Macos"
        # Compilation error on Windows with MSVC?
        self.options.vulkan_layer_overlay = not is_msvc(self)

        self.options.gallium_driver_radeonsi = False
        self.options.vulkan_driver_swrast = False

    def configure(self):
        self.provides = []
        if self.settings.os in ["FreeBSD", "Linux"] and not self.options.with_libglvnd:
            self.provides.append("libglvnd")
            if self.options.get_safe("egl"):
                self.provides.append("egl")
            if self.options.get_safe("opengl"):
                self.provides.append("opengl")

        # todo Perhaps it would be better to just remove these header files from the package and require these dependencies instead?
        # That's where Mesa is getting these from.
        # The same should be done for `libglvnd` too, then.
        if not self.options.get_safe("with_libglvnd") and self.settings.os != "Windows":
            if self.options.get_safe("gles1") or self.options.get_safe("gles2") or self.options.get_safe("opengl") or self.options.get_safe("egl"):
                self.provides.append("khrplatform")
            if self.options.get_safe("gles1") or self.options.get_safe("gles2") or self.options.get_safe("opengl"):
                self.provides.append("opengl-registry")
            if self.options.get_safe("egl"):
                self.provides.append("egl-headers")

        if self.options.get_safe("egl") and self.options.get_safe("with_libglvnd"):
            self.options["libglvnd"].egl = True
        if ("amd" in self._vulkan_drivers and not "windows" in self._platforms) or "radeonsi" in self._gallium_drivers:
            self.options["libdrm"].amdgpu = True
        if "i915" in self._gallium_drivers:
            self.options["libdrm"].intel = True
        if "nouveau" in self._gallium_drivers:
            self.options["libdrm"].nouveau = True
        if {"r300", "r600", "radeonsi"} & self._gallium_drivers:
            self.options["libdrm"].radeon = True
        if self.options.get_safe("gles1") and self.options.get_safe("with_libglvnd"):
            self.options["libglvnd"].gles1 = True
        if self.options.get_safe("gles2") and self.options.get_safe("with_libglvnd"):
            self.options["libglvnd"].gles2 = True
        if self.options.get_safe("glx") and self.options.get_safe("with_libglvnd"):
            self.options["libglvnd"].glx = True

        if self.options.get_safe("gallium_d3d12_video"):
            self.options.gallium_driver_d3d12.value = True

        if self.options.get_safe("gallium_rusticl") or self.options.get_safe("microsoft_clc"):
            self.options.opencl_spirv.value = True

        if ({"amd", "intel"} & self._vulkan_drivers) or "overlay" in self._vulkan_layers:
            self.options["glslang"].build_executables = True
            self.options["glslang"].enable_optimizer = False

        if not self._gallium_drivers:
            self.options.rm_safe("gallium_va")
            self.options.rm_safe("gallium_vdpau")

        if not self.options.get_safe("gallium_d3d12_video") and not ({"nouveau", "r600", "radeonsi", "virgl"} & self._gallium_drivers):
            self.options.rm_safe("gallium_va")

        if self.options.get_safe("gallium_va") and self.settings.os in ["Linux", "FreeBSD"] and not self.options.get_safe("with_libglvnd"):
            # The `with_glx` option in libva requires `opengl/system` which causes a conflict when not using libglvnd.
            self.options["libva"].with_glx = False

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self._with_libdrm:
            self.requires("libdrm/[~2.4.119]")

        if self.options.get_safe("xmlconfig"):
            self.requires("expat/[>=2.6.2 <3]")

        if "wayland" in self._platforms:
            self.requires("wayland/[^1.22.0]")

        if "x11" in self._platforms:
            self.requires("libxshmfence/1.3")
            if self.settings.os in ["FreeBSD", "Linux"]:
                self.requires("xorg/system")

        if self.options.with_libelf:
            self.requires("libelf/0.8.13")

        if self.options.get_safe("with_libglvnd"):
            self.requires("libglvnd/1.7.0")

        if self.options.get_safe("with_libudev") == "systemd":
            self.requires("libudev/[^255]")
        elif self.options.get_safe("with_libudev") == "eudev":
            self.requires("eudev/3.2.14")

        if self.options.get_safe("with_libunwind"):
            self.requires("libunwind/[^1.8.0]")

        if self.options.get_safe("with_llvm"):
            self.requires("llvm-core/[>=19]")
            self.requires("spirv-llvm-translator/[>=19]")
        if "rusticl" in self._gallium_drivers:
            self.requires("clang/[>=19]")
        if self._requires_libclc:
            self.requires("libclc/[>=19]")

        if self.options.get_safe("opencl_spirv"):
            self.requires("spirv-tools/[^1.3.239.0]")

        if self.options.get_safe("with_perfetto"):
            self.requires("perfetto/48.1")

        if self.options.with_zlib:
            self.requires("zlib-ng/[^2.0]")

        if self.options.with_zstd:
            self.requires("zstd/[^1.5]")

        if self._with_directx_headers:
            self.requires("directx-headers/[^1]")

        if self.options.get_safe("gallium_va"):
            self.requires("libva/[^2.21]")

        if self.options.get_safe("gallium_vdpau"):
            self.requires("libvdpau/1.5")

        if self.options.get_safe("tool_freedreno"):
            self.requires("libarchive/[^3.7.6]")
            self.requires("libxml2/[>=2.12.5 <3]")
            self.requires("lua/[^5.4.6]")

        if self._requires_moltenvk:
            self.requires("moltenvk/[^1.2.2]")

        if "screenshot" in self._vulkan_layers:
            self.requires("libpng/[~1.6]")

        if "intel_ui" in self._tools:
            self.requires("libepoxy/1.5.10")
            self.requires("gtk/[^3]")

    def validate(self):
        check_min_cppstd(self, 11)

        if self.options.get_safe("with_llvm"):
            llvm_opts = self.dependencies["llvm-core"].options
            if not llvm_opts.target_AMDGPU and not llvm_opts.target_NVPTX:
                raise ConanInvalidConfiguration("-o llvm-core/*:target_AMDGPU=True -o llvm-core/*:target_NVPTX=True is required to build Mesa with LLVM support")

        if "rusticl" in self._gallium_drivers:
            raise ConanInvalidConfiguration("'gallium_rusticl' option is not yet supported")

        # Not validating option and setting combinations due to the complexity of the project.

    def validate_build(self):
        check_max_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if "wayland" in self._platforms:
            self.tool_requires("wayland/<host_version>")
        if self.settings_build.os == "Windows":
            self.tool_requires("winflexbison/[^2.5.24]")
        else:
            self.tool_requires("bison/[^3.8.2]")
            self.tool_requires("flex/[^2.6.4]")
        if {"amd", "intel", "overlay"} & self._vulkan_layers:
            self.tool_requires("glslang/[^1.3.239.0]")
        if self.options.get_safe("with_llvm"):
            self.tool_requires("llvm-core/<host_version>")
        if self._requires_libclc and self.options.with_zstd:
            self.tool_requires("zstd/[^1.5]")
        if "rusticl" in self._gallium_drivers or "nouveau" in self._vulkan_drivers or "etnaviv" in self._tools:
            self.tool_requires("rust/[*]")
            self.tool_requires("rust-bindgen/[*]")
        self.tool_requires(f"mesa-clc/{self.version}")
        # Python is required for mako

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "meson.build",
                        "cpp.find_library('clang-cpp', dirs : llvm_libdir, required : false)",
                        "dependency('clang-cpp', required : true)")

    def generate(self):
        def boolean(option):
            return bool(self.options.get_safe(option, default=False))

        def feature(option):
            return "enabled" if self.options.get_safe(option) else "disabled"

        def combo(option):
            return str(self.options.get_safe(option) or "disabled")

        tc = MesonToolchain(self)
        tc.project_options["build-aco-tests"] = False
        tc.project_options["build-tests"] = False
        tc.project_options["datasources"] = sorted(self._datasources)
        tc.project_options["draw-use-llvm"] = boolean("with_llvm")
        tc.project_options["dri3"] = feature("dri3")
        tc.project_options["egl"] = feature("egl")
        tc.project_options["egl-native-platform"] = str(self.options.get_safe("egl_native_platform"))
        tc.project_options["enable-glcpp-tests"] = False
        tc.project_options["expat"] = "enabled" if self._requires_expat else "disabled"
        tc.project_options["freedreno-kmds"] = sorted(self._freedreno_kmds)
        tc.project_options["gallium-d3d10umd"] = boolean("gallium_d3d10umd")
        tc.project_options["gallium-d3d12-video"] = feature("gallium_d3d12_video")
        tc.project_options["gallium-drivers"] = sorted(self._gallium_drivers)
        tc.project_options["gallium-extra-hud"] = boolean("gallium_extra_hud")
        tc.project_options["gallium-omx"] = combo("gallium_omx")
        tc.project_options["gallium-rusticl"] = boolean("gallium_rusticl")
        tc.project_options["gallium-va"] = feature("gallium_va")
        tc.project_options["gallium-vdpau"] = feature("gallium_vdpau")
        tc.project_options["gbm"] = feature("gbm")
        tc.project_options["gles1"] = feature("gles1")
        tc.project_options["gles2"] = feature("gles2")
        tc.project_options["glvnd"] = feature("with_libglvnd")
        tc.project_options["glx"] = combo("glx")
        tc.project_options["imagination-srv"] = boolean("imagination_srv")
        tc.project_options["install-intel-gpu-tests"] = False
        tc.project_options["intel-clc"] = "system"  # mesa-clc is actually used instead
        tc.project_options["llvm"] = feature("with_llvm")
        tc.project_options["libunwind"] = feature("with_libunwind")
        tc.project_options["mesa-clc"] = "system"
        tc.project_options["microsoft-clc"] = feature("microsoft_clc")
        if self.options.get_safe("min_windows_version"):
            tc.project_options["min-windows-version"] = self.options.min_windows_version
        if self._requires_moltenvk:
            tc.project_options["moltenvk-dir"] = self.dependencies["moltenvk"].package_folder
        tc.project_options["opencl-spirv"] = boolean("opencl_spirv")
        tc.project_options["opengl"] = boolean("opengl")
        tc.project_options["perfetto"] = boolean("with_perfetto")
        if self.settings.os == "Android":
            tc.project_options["platform-sdk-version"] = str(self.settings.os.api_level)
        tc.project_options["platforms"] = sorted(self._platforms)
        tc.project_options["spirv-to-dxil"] = boolean("spirv_to_dxil")
        tc.project_options["shader-cache"] = feature("shader_cache")
        if self.options.get_safe("with_llvm"):
            tc.project_options["shared-llvm"] = "enabled" if self.dependencies["llvm-core"].options.shared else "disabled"
        tc.project_options["sse2"] = boolean("sse2")
        tc.project_options["tools"] = sorted(t.replace("_", "-") for t in self._tools)
        tc.project_options["valgrind"] = "disabled"
        tc.project_options["video-codecs"] = sorted(self._video_codecs)
        tc.project_options["vmware-mks-stats"] = boolean("vmware_mks_stats")
        tc.project_options["vulkan-beta"] = boolean("vulkan_beta")
        tc.project_options["vulkan-drivers"] = sorted(d.replace("_experimental", "-experimental") for d in self._vulkan_drivers)
        tc.project_options["vulkan-layers"] = sorted(l.replace("_", "-") for l in self._vulkan_layers)
        tc.project_options["xmlconfig"] = feature("xmlconfig")
        tc.project_options["zlib"] = feature("with_zlib")
        tc.project_options["zstd"] = feature("with_zstd")
        tc.generate()

        deps = PkgConfigDeps(self)
        deps.build_context_activated.append("wayland")
        deps.build_context_folder = os.path.join(self.generators_folder, "build")
        deps.set_property("clang::clang-cpp", "pkg_config_name", "clang-cpp")
        deps.generate()

        if cross_building(self):
            env = Environment()
            env.define_path("PKG_CONFIG_FOR_BUILD", self.conf.get("tools.gnu:pkg_config", default="pkgconf", check_type=str))
            env.define_path("PKG_CONFIG_PATH_FOR_BUILD", self.generators_folder)
            env.vars(self).save_script("pkg_config_for_build_env")

        if self.options.get_safe("with_llvm"):
            deps = CMakeDeps(self)
            deps.generate()

        if not self.conf.get("user.mesa:skip_install_mako", default=False, check_type=bool):
            env = Environment()
            env.append_path("PYTHONPATH", self._site_packages_dir)
            env.append_path("PATH", os.path.join(self._site_packages_dir, "bin"))
            if self.settings_build.os == "Linux":
                # The Python SSL module is used by pip when installing packages.
                # Depending on the Linux distribution, the OpenSSL configuration may be incompatible with the Python SSL module.
                # Set OPENSSL_CONF to avoid attempting to load an invalid configuration.
                env.define("OPENSSL_CONF", "/dev/null")
            env.vars(self).save_script("pythonpath")

    @cached_property
    def _site_packages_dir(self):
        return os.path.join(self.build_folder, "site-packages")

    def _pip_install(self, packages):
        self.run(f"python -m pip install {' '.join(packages)} --target={self._site_packages_dir}",
                 cwd=self.source_folder)

    def build(self):
        self._pip_install(["mako", "ply"])
        meson = Meson(self)
        meson.configure()
        meson.build()

    def _extract_pkg_config_version(self, file):
        pkg_config = load(self, os.path.join(self.package_folder, "lib", "pkgconfig", file))
        return re.search("^Version: ([^\n$]+)[$\n]", pkg_config, flags=re.MULTILINE).group(1)

    def _pkg_config_version_file(self, name):
        return os.path.join(self.package_folder, "share", f"{self.name}-{name}-version.txt")

    def _save_pkg_config_version(self, name):
        save(self, self._pkg_config_version_file(name), self._extract_pkg_config_version(f"{name}.pc"))

    def _load_pkg_config_version(self, name):
        return load(self, self._pkg_config_version_file(name)).strip()

    def package(self):
        copy(self, "license.rst", os.path.join(self.source_folder, "docs"), os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()

        if "d3d12" in self._gallium_drivers:
            self._save_pkg_config_version("d3d")
        if self.options.get_safe("with_libglvnd") and self.options.get_safe("egl"):
            # According to the libglvnd ICD loading rules, an ICD library installed in a non-standard directory should be referenced using an absolute path.
            # For Conan, a relative path will have to suffice.
            replace_in_file(self, os.path.join(self.package_folder, "share", "glvnd", "egl_vendor.d", "50_mesa.json"),
                            "libEGL_mesa",
                            os.path.join("..", "..", "..", "lib", "libEGL_mesa"))

        # rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

        fix_apple_shared_install_name(self)

    def package_info(self):
        if "d3d12" in self._gallium_drivers:
            d3d = self.cpp_info.components["d3d"]
            d3d.set_property("pkg_config_name", "d3d")
            if self._with_libdrm:
                d3d.requires.append("libdrm::libdrm")
            d3d.set_property("pkg_config_custom_content", "moduledir=${libdir}/d3d")
            d3d.set_property("component_version", self._load_pkg_config_version("d3d"))

        dri = self.cpp_info.components["dri"]
        dri.set_property("pkg_config_name", "dri")
        if self._with_libdrm:
            dri.requires.append("libdrm::libdrm")
        dri.set_property("component_version", self.version)
        dri.set_property("pkg_config_custom_content", "dridriverdir=${libdir}/dri")

        if self.options.get_safe("egl"):
            egl = self.cpp_info.components["egl"]
            if self.options.get_safe("with_libglvnd"):
                egl.libs = ["EGL_mesa"]
                egl.requires.append("libglvnd::egl")
            else:
                egl.libs = ["EGL"]
                egl.set_property("pkg_config_name", "egl")
            if "x11" in self._platforms and self.options.glx == "dri":
                egl.requires.extend([
                    "xorg::x11-xcb",
                    "xorg::xcb",
                    "xorg::xcb-dri3",
                    "xorg::xcb-present",
                    "xorg::xcb-randr",
                    "xorg::xcb-shm",
                    "xorg::xcb-xfixes"
                ])
            if "wayland" in self._platforms:
                egl.requires.extend([
                    "wayland::wayland-client",
                    "wayland::wayland-server",
                    "wayland::wayland-egl-backend",
                ])
            if self._with_libdrm:
                egl.requires.append("libdrm::libdrm")
            if self.options.get_safe("gbm") and "android" not in self._platforms:
                egl.requires.append("gbm::gbm")
            if self.options.get_safe("with_perfetto"):
                egl.requires.append("perfetto::perfetto")

        if self.options.get_safe("gbm"):
            gbm = self.cpp_info.components["gbm"]
            gbm.libs = ["gbm"]
            if self._with_libdrm:
                gbm.requires.append("libdrm::libdrm")
            if self.options.get_safe("xmlconfig"):
                gbm.requires.append("expat::expat")
            gbm.set_property("pkg_config_name", "gbm")
            gbm.set_property("component_version", self.version)
            gbm.set_property("pkg_config_custom_content", "gbmbackendspath=${libdir}/gbm")

        if self.options.get_safe("gles1") and not self.options.get_safe("with_libglvnd"):
            gles1 = self.cpp_info.components["gles1"]
            gles1.libs = ["GLESv1_CM"]
            gles1.set_property("pkg_config_name", "glesv1_cm")
            if self._with_libdrm:
                gles1.requires.append("libdrm::libdrm")

        if self.options.get_safe("gles2") and not self.options.get_safe("with_libglvnd"):
            gles2 = self.cpp_info.components["gles2"]
            gles2.libs = ["GLESv2"]
            gles2.set_property("pkg_config_name", "glesv1")
            if self._with_libdrm:
                gles2.requires.append("libdrm::libdrm")

        if self.options.get_safe("glx"):
            glx = self.cpp_info.components["glx"]
            gl_lib_name = "GLX_mesa" if self.options.get_safe("with_libglvnd") else "GL"
            glx.libs = [gl_lib_name]

            # Basic dependencies from the meson.build file
            if self.options.get_safe("with_libglvnd"):
                glx.requires.append("libglvnd::glx")

            # Platform specific dependencies
            if self._with_libdrm:
                glx.requires.append("libdrm::libdrm")

            if self.settings.os in ["FreeBSD", "Linux"]:
                # Dependencies from libglx and libgl in meson.build
                glx.requires.extend([
                    "libdrm::libdrm",
                    "xorg::x11",
                    "xorg::xext",
                    "xorg::xxf86vm",
                    "xorg::xfixes",
                    "xorg::xshmfence",
                    "xorg::xcb-shm",
                    "xorg::xcb",
                    "xorg::xcb-dri2",
                    "xorg::xcb-glx",
                    "xorg::x11-xcb",
                ])

                # Add xmlconfig if needed, matches idep_xmlconfig in meson.build
                if self.options.get_safe("xmlconfig"):
                    glx.requires.append("expat::expat")

                # System libraries
                glx.system_libs.extend(["dl", "m", "pthread"])

                # DRI-specific dependencies
                if self.options.get_safe("with_x11_dri2"):
                    # No additional deps needed, already included above
                    pass

            elif self.settings.os == "Windows":
                # Windows platform dependencies
                glx.system_libs.extend(["gdi32", "opengl32"])

            # GL component now uses same libs as GLX, matching meson.build's approach
            gl = self.cpp_info.components["gl"]
            gl.libs = [gl_lib_name]

            # If not using libglvnd, set pkg_config_name
            if not self.options.get_safe("with_libglvnd"):
                gl.set_property("pkg_config_name", "gl")
                gl.set_property("pkg_config_custom_content", "glx_tls=yes")

                # Add all the glx dependencies to gl as well
                gl.requires = glx.requires.copy()
                gl.system_libs = glx.system_libs.copy()

        glapi = self.cpp_info.components["glapi"]
        glapi.libs = ["glapi"]

        # Add gallium dependency with proper requirements
        if self._gallium_drivers and self.settings.os in ["Linux", "FreeBSD"]:
            gallium = self.cpp_info.components["gallium"]
            gallium.libs = [f"gallium-{self.version}"]
            gallium.requires.extend([
                "libdrm::libdrm",
                "expat::expat",
                "xorg::x11-xcb",
                "xorg::xcb",
                "xorg::xcb-dri3",
                "xorg::xcb-present",
                "xorg::xcb-randr",
                "xorg::xcb-sync",
                "xorg::xcb-xfixes",
                "libxshmfence::libxshmfence"
            ])
            if self.options.get_safe("with_llvm"):
                gallium.requires.append("llvm-core::llvm-core")
            if self.options.get_safe("with_perfetto"):
                gallium.requires.append("perfetto::perfetto")
            if self.options.get_safe("opencl_spirv"):
                gallium.requires.append("spirv-tools::spirv-tools")
            if self.options.with_zlib:
                gallium.requires.append("zlib-ng::zlib-ng")
            if self.options.with_zstd:
                gallium.requires.append("zstd::zstd")

        if self.settings.os == "Windows" and self.options.get_safe("with_opengl"):
            gallium_wgl = self.cpp_info.components["gallium_wgl"]
            gallium_wgl.libs = ["libgallium_wgl"]
            opengl32 = self.cpp_info.components["opengl32"]
            opengl32.libs = ["opengl32"]
            opengl32.requires = ["gallium_wgl"]

        # Add Vulkan driver dependencies
        if self._vulkan_drivers and self.settings.os in ["Linux", "FreeBSD"]:
            vulkan_components = ["vulkan_intel", "vulkan_intel_hasvk", "vulkan_radeon", "vulkan_asahi"]
            for comp in vulkan_components:
                if comp.replace("vulkan_", "") in self._vulkan_drivers:
                    vulkan_component = self.cpp_info.components[comp]
                    vulkan_component.libs = [f"lib{comp}"]
                    vulkan_component.requires.extend([
                        "libdrm::libdrm",
                        "expat::expat",
                        "wayland::wayland-client",
                        "xorg::x11-xcb",
                        "xorg::xcb",
                        "xorg::xcb-dri3",
                        "xorg::xcb-keysyms",
                        "xorg::xcb-present",
                        "xorg::xcb-randr",
                        "xorg::xcb-shm",
                        "xorg::xcb-sync",
                        "xorg::xcb-xfixes",
                        "libxshmfence::libxshmfence"
                    ])
                    if self.options.get_safe("with_libudev"):
                        vulkan_component.requires.append("libudev::libudev")
                    if self.options.get_safe("with_perfetto"):
                        vulkan_component.requires.append("perfetto::perfetto")
                    if self.options.get_safe("opencl_spirv"):
                        vulkan_component.requires.append("spirv-tools::spirv-tools")
                    if self.options.with_zlib:
                        vulkan_component.requires.append("zlib-ng::zlib-ng")
                    if self.options.with_zstd:
                        vulkan_component.requires.append("zstd::zstd")
                    if comp == "vulkan_radeon" and self.options.with_libelf:
                        vulkan_component.requires.append("libelf::libelf")

        # Add vulkan layer dependencies
        if "device_select" in self._vulkan_layers and self.settings.os in ["Linux", "FreeBSD"]:
            vulkan_device_select = self.cpp_info.components["vulkan_device_select"]
            vulkan_device_select.libs = ["libVkLayer_MESA_device_select"]
            vulkan_device_select.requires.extend([
                "libdrm::libdrm",
                "wayland::wayland-client",
                "xorg::xcb",
                "xorg::xcb-dri3"
            ])

        if "screenshot" in self._vulkan_layers:
            vulkan_screenshot = self.cpp_info.components["vulkan_screenshot"]
            vulkan_screenshot.libs = ["libVkLayer_MESA_screenshot"]
            vulkan_screenshot.requires.append("libpng::libpng")

        # Add general dependencies
        if self.options.get_safe("tool_intel") or self.options.get_safe("xmlconfig"):
            self.cpp_info.requires.append("expat::expat")

        if "wayland" in self._platforms:
            self.cpp_info.requires.append("wayland::wayland")

        if "x11" in self._platforms:
            self.cpp_info.requires.append("libxshmfence::libxshmfence")
            if self.settings.os in ["FreeBSD", "Linux"]:
                self.cpp_info.requires.append("xorg::xorg")

        if self.options.with_libelf:
            self.cpp_info.requires.append("libelf::libelf")

        if self.options.get_safe("with_libudev") == "systemd":
            self.cpp_info.requires.append("libudev::libudev")
        elif self.options.get_safe("with_libudev") == "eudev":
            self.cpp_info.requires.append("eudev::eudev")

        if self.options.get_safe("with_libunwind"):
            self.cpp_info.requires.append("libunwind::libunwind")

        if self.options.get_safe("opencl_spirv"):
            self.cpp_info.requires.append("spirv-tools::spirv-tools")

        if self.options.get_safe("with_perfetto"):
            self.cpp_info.requires.append("perfetto::perfetto")

        if self.options.with_zlib:
            self.cpp_info.requires.append("zlib-ng::zlib-ng")

        if self.options.with_zstd:
            self.cpp_info.requires.append("zstd::zstd")

        if self.options.get_safe("with_llvm"):
            self.cpp_info.requires.append("llvm-core::llvm-core")
        if self._requires_libclc:
            self.cpp_info.requires.append("libclc::libclc")
        if self.options.get_safe("gallium_va"):
            self.cpp_info.requires.append("libva::libva_")
            if self.settings.os == "Windows":
                self.cpp_info.requires.append("libva::libva-win32")
        if self.options.get_safe("gallium_vdpau"):
            self.cpp_info.requires.append("libvdpau::libvdpau")

        if self.options.get_safe("tool_freedreno"):
            self.cpp_info.requires.append("libarchive::libarchive")
            self.cpp_info.requires.append("libxml2::libxml2")
            self.cpp_info.requires.append("lua::lua")

        if self._requires_moltenvk:
            self.cpp_info.requires.append("moltenvk::moltenvk")

        if self._with_directx_headers:
            self.cpp_info.requires.append("directx-headers::directx-headers")

        if self.options.get_safe("with_libglvnd") and self.options.get_safe("egl"):
            self.runenv_info.prepend_path("__EGL_VENDOR_LIBRARY_DIRS", os.path.join(self.package_folder, "share", "glvnd", "egl_vendor.d"))

        if self._gallium_drivers:
            libgl_drivers_path = os.path.join(self.package_folder, "lib", "dri")
            if self.settings.os == "Windows":
                libgl_drivers_path = os.path.join(self.package_folder, "bin")
            self.runenv_info.prepend_path("LIBGL_DRIVERS_PATH", libgl_drivers_path)

            if self.options.get_safe("gallium_va"):
                self.runenv_info.prepend_path("LIBVA_DRIVERS_PATH", libgl_drivers_path)

            if self.options.get_safe("gallium_vdpau"):
                self.runenv_info.prepend_path("VDPAU_DRIVER_PATH", os.path.join(self.package_folder, "lib", "vdpau"))

        if self.settings.os in ["FreeBSD", "Linux"]:
            self.runenv_info.prepend_path("DRIRC_CONFIGDIR", os.path.join(os.path.join(self.package_folder, "share", "drirc.d")))

        if self._vulkan_layers:
            self.runenv_info.prepend_path("VK_LAYER_PATH", os.path.join(self.package_folder, "share", "vulkan", "implicit.d"))
            self.runenv_info.prepend_path("VK_LAYER_PATH", os.path.join(self.package_folder, "share", "vulkan", "icd.d"))
            self.runenv_info.prepend_path("VK_LAYER_PATH", os.path.join(self.package_folder, "share", "vulkan", "explicit_layer.d"))

        if self._vulkan_drivers:
            for driver_file in glob.glob(os.path.join(self.package_folder, "share", "vulkan", "icd.d", "*.json")):
                self.runenv_info.prepend_path("VK_ADD_DRIVER_FILES", driver_file)
