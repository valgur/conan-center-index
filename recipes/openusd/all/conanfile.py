import json
import os
import re
import textwrap
from functools import lru_cache
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class OpenUSDConan(ConanFile):
    name = "openusd"
    description = "Universal Scene Description"
    license = "DocumentRef-LICENSE.txt:LicenseRef-Modified-Apache-2.0-License"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://openusd.org/"
    topics = ("3d", "scene", "usd")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_usd_tools": [True, False],
        "build_imaging": [True, False],
        "build_usd_imaging": [True, False],
        "build_usdview": [True, False],
        "build_openimageio_plugin": [True, False],
        "build_opencolorio_plugin": [True, False],
        "build_embree_plugin": [True, False],
        "enable_materialx_support": [True, False],
        "enable_vulkan_support": [True, False],
        "enable_gl_support": [True, False],
        "build_gpu_support": [True, False],
        "enable_ptex_support": [True, False],
        "enable_openvdb_support": [True, False],
        "build_alembic_plugin": [True, False],
        "enable_hdf5_support": [True, False],
        "build_draco_plugin": [True, False],
        "enable_osl_support": [True, False],
        "build_animx_tests": [True, False],
        "enable_python_support": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": False,
        "build_usd_tools": True,
        "build_imaging": True,
        "build_usd_imaging": True,
        "build_usdview": True,
        "build_openimageio_plugin": False,
        "build_opencolorio_plugin": False,
        "build_embree_plugin": False,
        "enable_materialx_support": True,
        "enable_vulkan_support": False,
        "enable_gl_support": True,
        "enable_ptex_support": True,
        "enable_openvdb_support": False,
        "build_alembic_plugin": False,
        "enable_hdf5_support": True,
        "build_draco_plugin": False,
        "enable_osl_support": False,
        "build_animx_tests": False,
        "enable_python_support": False
    }

    no_copy_source = True

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        # as defined in https://github.com/PixarAnimationStudios/OpenUSD/blob/release/VERSIONS.md
        return {
            "apple-clang": "13",
            "clang": "7",
            "gcc": "9",
            "msvc": "191",
            "Visual Studio": "15",
        }

    @property
    def _enable_ptex(self):
        return self.options.enable_ptex_support and self.options.enable_gl_support and self.options.build_gpu_support

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.options.build_usd_imaging and not self.options.build_imaging:
            self.options.build_usd_imaging = False
        self.options.build_gpu_support = self.options.enable_gl_support or is_apple_os(self) or self.options.enable_vulkan_support
        if self.options.build_usdview:
            if self.options.build_imaging:
                self.options.build_usd_imaging = False
        if self.options.build_usdview:
            if not self.options.build_usd_imaging:
                self.options.build_usdview = False
            elif not self.options.enable_python_support:
                self.options.build_usdview = False
            elif not self.options.build_gpu_support:
                self.options.build_usdview = False
        if self.options.build_embree_plugin:
            if not self.options.build_imaging:
                self.options.build_embree_plugin = False
            elif not self.options.build_gpu_support:
                self.options.build_embree_plugin = False

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        # Set same options as in https://github.com/PixarAnimationStudios/OpenUSD/blob/release/build_scripts/build_usd.py#L1476
        self.options["opensubdiv/*"].with_tbb = True
        if self.options.enable_gl_support:
            self.options["opensubdiv/*"].with_opengl = self.options.enable_gl_support

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.enable_python_support:
            self.requires("boost/1.87.0")
        # openusd doesn't support yet recent release of onetbb, see https://github.com/PixarAnimationStudios/OpenUSD/issues/1471
        self.requires("onetbb/2021.12.0", transitive_headers=True)
        if self.options.build_imaging:
            if self.options.build_openimageio_plugin and self.options.build_gpu_support:
                self.requires("openimageio/2.5.18.0")
            if not self.options.build_openimageio_plugin and self.options.build_opencolorio_plugin and self.options.build_gpu_support and self.options.enable_gl_support:
                self.requires("opencolorio/2.4.2")
            self.requires("opensubdiv/3.6.0")
            if self.options.enable_vulkan_support:
                self.requires("vulkan-headers/1.4.309.0")
            if self.options.enable_gl_support:
                self.requires("opengl/system")
            # if self._enable_ptex:
            #     self.requires("ptex/2.4.2")
            if self.options.enable_openvdb_support and self.options.build_gpu_support:
                self.requires("openvdb/11.0.0")
            if self.options.build_embree_plugin and self.options.build_gpu_support:
                self.requires("embree3/3.13.5")
        if self.options.build_alembic_plugin:
            self.requires("alembic/1.8.6")
            if self.options.enable_hdf5_support:
                self.requires("hdf5/1.14.5")
        if self.options.build_draco_plugin:
            self.requires("draco/1.5.6")
        if self.options.enable_materialx_support:
            self.requires("materialx/1.39.1", transitive_headers=True)
        # if self.options.enable_osl_support:
           # TODO: add osl to conan center (https://github.com/AcademySoftwareFoundation/OpenShadingLanguage)
            # self.requires("openshadinglanguage/1.13.8.0")
        # if self.options.build_animx_tests:
           # TODO: add animx to conan center (https://github.com/Autodesk/animx/)
            # self.requires("animx/x.y.z")
        if self.options.build_imaging and (self.options.build_openimageio_plugin and self.options.build_gpu_support or self.options.enable_openvdb_support):
            self.requires("imath/3.1.12")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.requires("xorg/system")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support.")
        if self.options.enable_gl_support and is_apple_os(self):
            raise ConanInvalidConfiguration(f'{self.ref} needs -o="opensubdiv/*:with_metal=True"')
        if self.options.build_animx_tests:
            raise ConanInvalidConfiguration("animx recipe doesn't yet exists in conan center index")
        if self.options.enable_osl_support:
            raise ConanInvalidConfiguration("openshadinglanguage recipe doesn't yet exists in conan center index")
        if self.options.enable_python_support:
            raise ConanInvalidConfiguration("python doesn't yet supported")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        # Use variables in documented in https://github.com/PixarAnimationStudios/OpenUSD/blob/release/BUILDING.md
        tc.cache_variables["PXR_BUILD_TESTS"] = False
        tc.cache_variables["PXR_BUILD_EXAMPLES"] = False
        tc.cache_variables["PXR_BUILD_TUTORIALS"] = False
        tc.cache_variables["PXR_BUILD_HTML_DOCUMENTATION"] = False
        tc.cache_variables["PXR_ENABLE_PYTHON_SUPPORT"] = self.options.enable_python_support
        tc.cache_variables["PXR_BUILD_USD_TOOLS"] = self.options.build_usd_tools

        if self.options.enable_gl_support:
            tc.cache_variables["OPENSUBDIV_LIBRARIES"] = "OpenSubdiv::osdcpu"
            tc.cache_variables["OPENSUBDIV_INCLUDE_DIR"] = self.dependencies['opensubdiv'].cpp_info.includedirs[0].replace("\\", "/")
        target_suffix = "" if self.dependencies["opensubdiv"].options.shared else "_static"
        tc.cache_variables["OPENSUBDIV_OSDCPU_LIBRARY"] = "OpenSubdiv::osdcpu"+target_suffix

        tc.cache_variables["TBB_tbb_LIBRARY"] = "TBB::tbb"

        tc.cache_variables["PXR_ENABLE_MATERIALX_SUPPORT"] = self.options.enable_materialx_support

        tc.cache_variables["PXR_BUILD_IMAGING"] = self.options.build_imaging
        if self.options.build_imaging:
            tc.cache_variables["PXR_BUILD_IMAGING"] = True
            tc.cache_variables["PXR_ENABLE_GL_SUPPORT"] = self.options.enable_gl_support
            tc.cache_variables["PXR_ENABLE_VULKAN_SUPPORT"] = self.options.enable_vulkan_support

            # if self._enable_ptex:
            #     tc.cache_variables["PXR_ENABLE_PTEX_SUPPORT"] = True
            #     tc.cache_variables["PTEX_LIBRARY"] = self.dependencies['ptex'].cpp_info.libdirs[0]
            #     tc.cache_variables["PTEX_INCLUDE_DIR"] = self.dependencies['ptex'].cpp_info.includedirs[0].replace("\\", "/")

            tc.cache_variables["PXR_ENABLE_OPENVDB_SUPPORT"] = self.options.enable_openvdb_support and self.options.enable_gl_support
            tc.cache_variables["OPENVDB_LIBRARY"] = "OpenVDB::openvdb"

            tc.cache_variables["PXR_BUILD_OPENIMAGEIO_PLUGIN"] = self.options.build_openimageio_plugin and self.options.shared and self.options.build_gpu_support
            tc.cache_variables["PXR_BUILD_COLORIO_PLUGIN"] = self.options.build_opencolorio_plugin and self.options.shared and self.options.enable_gl_support and self.options.build_gpu_support

            if self.options.build_embree_plugin and self.options.shared and self.options.build_gpu_support:
                tc.cache_variables["PXR_BUILD_EMBREE_PLUGIN"] = self.options.build_embree_plugin
                tc.cache_variables["EMBREE_LIBRARY"] = self.dependencies['embree3'].cpp_info.libdirs[0]
                tc.cache_variables["EMBREE_INCLUDE_DIR"] = self.dependencies['embree3'].cpp_info.includedirs[0].replace("\\", "/")

            if self.options.build_usd_imaging:
                tc.cache_variables["PXR_BUILD_USD_IMAGING"] = True
                if self.options.build_usdview:
                    tc.cache_variables["PXR_BUILD_USDVIEW"] = True

        # Renderman is a proprietary software, see build_renderman_plugin
        tc.cache_variables["PXR_BUILD_PRMAN_PLUGIN"] = False

        if self.options.build_alembic_plugin and self.options.shared:
            tc.cache_variables["PXR_BUILD_ALEMBIC_PLUGIN"] = True
            tc.cache_variables["ALEMBIC_FOUND"] = True
            tc.cache_variables["ALEMBIC_LIBRARIES"] = "Alembic::Alembic"
            tc.cache_variables["ALEMBIC_LIBRARY_DIR"] = self.dependencies['alembic'].cpp_info.libdirs[0].replace("\\", "/")
            tc.cache_variables["ALEMBIC_INCLUDE_DIR"] = self.dependencies['alembic'].cpp_info.includedirs[0].replace("\\", "/")

        tc.cache_variables["PXR_ENABLE_HDF5_SUPPORT"] = self.options.build_alembic_plugin and self.options.enable_hdf5_support

        if self.options.build_draco_plugin and self.options.shared:
            tc.cache_variables["PXR_BUILD_DRACO_PLUGIN"] = True
            tc.cache_variables["DRACO_LIBRARY"] = "draco::draco"
            tc.cache_variables["DRACO_INCLUDES"] = self.dependencies['draco'].cpp_info.includedirs[0].replace("\\", "/")

        tc.cache_variables["PXR_ENABLE_OSL_SUPPORT"] = self.options.enable_osl_support
        tc.cache_variables["PXR_BUILD_ANIMX_TESTS"] = self.options.build_animx_tests

        tc.cache_variables["MaterialX_DIR"] = self.options.build_animx_tests

        tc.generate()

        deps = CMakeDeps(self)
        if self.options.build_imaging:
            deps.set_property("opensubdiv::osdcpu", "cmake_target_name", "OpenSubdiv::osdcpu")
            deps.set_property("opensubdiv::osdcpu", "cmake_target_aliases", ["OpenSubdiv::osdcpu_static"])
        if self.options.enable_materialx_support:
            deps.set_property("materialx::MaterialXCore", "cmake_target_name", "MaterialXCore")
            deps.set_property("materialx::MaterialXFormat", "cmake_target_name", "MaterialXFormat")
            deps.set_property("materialx::MaterialXGenShader", "cmake_target_name", "MaterialXGenShader")
            deps.set_property("materialx::MaterialXRender", "cmake_target_name", "MaterialXRender")
            deps.set_property("materialx::MaterialXGenGlsl", "cmake_target_name", "MaterialXGenGlsl")
        deps.generate()
        self._cmakedeps = deps

    @property
    @lru_cache
    def _cmake_to_conan_targets(self):
        def _get_targets(*args):
            targets = [self._cmakedeps.get_property("cmake_target_name", *args),
                       self._cmakedeps.get_property("cmake_module_target_name", *args)]
            targets += self._cmakedeps.get_property("cmake_target_aliases", *args) or []
            return list(filter(None, targets))

        cmake_targets_map = {}
        for req, dependency in self.dependencies.host.items():
            dep_name = req.ref.name
            for target in _get_targets(dependency):
                cmake_targets_map[target] = f"{dep_name}::{dep_name}"
            for component, _ in dependency.cpp_info.components.items():
                for target in _get_targets(dependency, component):
                    cmake_targets_map[target] = f"{dep_name}::{component}"
        return cmake_targets_map

    @property
    @lru_cache
    def _build_info(self):
        return {
            "components": components_from_dotfile(self._graphviz_file.read_text(), self._cmake_to_conan_targets),
        }

    def _write_build_info(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self._build_info, indent=2))

    @property
    def _graphviz_file(self):
        return Path(self.build_folder) / f"{self.name}.dot"

    def _validate_components(self, components):
        direct_deps = {k.ref.name for k, v in self.dependencies.direct_host.items()}
        all_ext_deps = set()
        for component, info in components.items():
            for req in info["requires"]:
                if "::" in req:
                    dep, dep_comp = req.split("::", 1)
                    if dep not in direct_deps:
                        raise ConanException(f"Unexpected dependency for {component}: {req}")
                    if dep != dep_comp and dep_comp not in self.dependencies.host[dep].cpp_info.components:
                        raise ConanException(f"Unexpected dependency for {component}: no component {dep}::{dep_comp} in {dep}")
                    all_ext_deps.add(dep)
        if direct_deps - all_ext_deps:
            raise ConanException(f"Dependencies not used by any components: {', '.join(direct_deps - all_ext_deps)}")

    def build(self):
        cmake = CMake(self)
        # components not exported or not of interest
        exclude_patterns = [
            "CONAN_LIB.+",
            ".+_DEPS_TARGET",
            r".+\.conan2.+",
        ]
        save(self, Path(self.build_folder) / "CMakeGraphVizOptions.cmake", textwrap.dedent(f"""
            set(GRAPHVIZ_EXECUTABLES OFF)
            set(GRAPHVIZ_MODULE_LIBS OFF)
            set(GRAPHVIZ_OBJECT_LIBS OFF)
            set(GRAPHVIZ_IGNORE_TARGETS "{';'.join(exclude_patterns)}")
        """))
        cmake.configure(cli_args=[f"--graphviz={self._graphviz_file}"])
        self._write_build_info(self._build_info_file.name)
        self._validate_components(self._build_info["components"])
        cmake.build()

    @property
    def _cmake_module_path(self):
        return Path("lib") / "cmake" / self.name

    @property
    def _build_info_file(self):
        return Path(self.package_folder) / self._cmake_module_path / "conan_build_info.json"

    def _read_build_info(self) -> dict:
        return json.loads(self._build_info_file.read_text())

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        self._write_build_info(self._build_info_file)
        rm(self, "pxrConfig.cmake", self.package_folder)
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "pxr")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["PXR"])
        plugins = {p.stem for p in Path(self.package_folder, "plugin", "usd").iterdir() if p.suffix in [".so", ".dll", ".dylib"]}
        components = self._read_build_info()["components"]
        for name, data in components.items():
            if name not in plugins:
                component = self.cpp_info.components[name]
                component.libs = [f"usd_{name}"]
                component.requires = data["requires"]
                component.system_libs = data["system_libs"]

def parse_dotfile(dotfile, label_replacements=None):
    """
    Load the dependency graph defined by the nodes and edges in a dotfile.
    """
    label_replacements = label_replacements or {}
    labels = {}
    for node, label in re.findall(r'^\s*"(node\d+)"\s*\[\s*label\s*=\s*"(.+?)"', dotfile, re.MULTILINE):
        labels[node] = label_replacements.get(label, label)
    components = {l: [] for l in labels.values()}
    for src, dst in re.findall(r'^\s*"(node\d+)"\s*->\s*"(node\d+)"', dotfile, re.MULTILINE):
        components[labels[src]].append(labels[dst])
    return components


def components_from_dotfile(dotfile, cmake_to_conan_targets):
    """
    Parse the dotfile generated by the
    [cmake --graphviz](https://cmake.org/cmake/help/latest/module/CMakeGraphVizOptions.html)
    option to generate the list of available CMake targets and their inter-component dependencies.
    """
    known_system_libs = {
        "dl",
        "pthread",
        "m",
        "rt",
        "Shlwapi",
        "Shlwapi.lib",
        "Dbghelp",
        "Dbghelp.lib",
    }
    ext_dep_map = cmake_to_conan_targets | {
        "libICE":  "xorg::ice",
        "libSM":   "xorg::sm",
        "libX11":  "xorg::x11",
        "libXext": "xorg::xext",
        "OpenGL::EGL": "egl::egl",
        "OpenGL::GL": "opengl::opengl",
        "OpenGL::GLES2": "opengl::opengl",
        "OpenGL::GLES3": "opengl::opengl",
        "OpenGL::GLX": "opengl::opengl",
        "OpenGL::OpenGL": "opengl::opengl",
        "MaterialXGenMsl": "materialx::MaterialXGenMsl",
        "MaterialXRenderGlsl": "materialx::MaterialXRenderGlsl",
    }
    components = {}
    for component, deps in parse_dotfile(dotfile).items():
        if "::" in component or component in ext_dep_map:
            continue
        if component in known_system_libs:
            continue
        if "/" in component or "\\" in component:
            continue
        requires = []
        system_libs = []
        for dep in deps:
            if dep.endswith(".so"):
                dep = Path(dep).stem
            if dep in known_system_libs:
                system_libs.append(dep)
            else:
                dep = ext_dep_map.get(dep, dep)
                requires.append(dep)
        components[component] = {
            "requires": requires,
            "system_libs": system_libs,
        }
    return components
