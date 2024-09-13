import os

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.cmake import cmake_layout
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm, replace_in_file
from conan.tools.gnu import AutotoolsToolchain, AutotoolsDeps, PkgConfigDeps, Autotools
from conan.tools.microsoft import is_msvc

required_conan_version = ">=1.53.0"


class ArpackNgConan(ConanFile):
    name = "arpack-ng"
    description = "Collection of Fortran77 subroutines designed to solve large scale eigenvalue problems"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/opencollab/arpack-ng"
    topics = ("linear-algebra", "eigenvalue", "arpack", "parpack")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "fortran": ["f2c", "system"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "fortran": "f2c",
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("f2c/20240312")

    def build_requirements(self):
        self.tool_requires("libtool/2.4.7")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if self._settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")
        if is_msvc(self):
            self.tool_requires("automake/1.16.5")
        if self.options.fortran == "f2c":
            self.tool_requires("f2c/20240312", options={"fc_wrapper": False})


    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualBuildEnv(self).generate()
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")

        def yes_no(v):
            return "yes" if v else "no"

        tc = AutotoolsToolchain(self)
        env = tc.environment()
        tc.generate(env)

        tc = PkgConfigDeps(self)
        tc.generate()

        deps = AutotoolsDeps(self)
        deps.generate()


    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        autotools = Autotools(self)
        autotools.autoreconf()
        replace_in_file(self, os.path.join(self.source_folder, "configure"), "2>&5", "")
        replace_in_file(self, os.path.join(self.source_folder, "configure"), ">&5", "")
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        # rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        # rmdir(self, os.path.join(self.package_folder, "share"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "arpackng")
        self.cpp_info.set_property("cmake_target_name", "ARPACK::ARPACK")
        self.cpp_info.set_property("pkg_config_name", "package")

        self.cpp_info.libs = ["package_lib"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
            self.cpp_info.system_libs.append("pthread")
            self.cpp_info.system_libs.append("dl")
