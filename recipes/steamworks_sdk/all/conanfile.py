import os
import textwrap

import requests
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, save, unzip

required_conan_version = ">=2.1"


class SteamworksSdkConan(ConanFile):
    name = "steamworks_sdk"
    description = ("Steamworks SDK is a set of tools and services that help game developers and publishers"
                   " build their games and get the most out of distributing on Steam.")
    license = "STEAMWORKS SDK license"
    _license_url = "https://partner.steamgames.com/documentation/sdk_access_agreement"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://partner.steamgames.com/doc/sdk"
    topics = ("game-dev", "steam", "sdk", "pre-built")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "agreed_to_license_terms": [True, False],
        "build_glmgr": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "agreed_to_license_terms": False,
        "build_glmgr": True,
        "tools": True,
    }
    options_description = {
        "agreed_to_license_terms": f"You have agreed to the Steamworks SDK license terms at {_license_url}.",
        "build_glmgr": "Build the GLMgr OSX DirectX to OpenGL conversion library.",
        "tools": "Package the tools directory under share/.",
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src", "glmgr"))

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if not is_apple_os(self):
            del self.options.build_glmgr

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        if not self.info.options.get_safe("build_glmgr"):
            del self.info.settings.compiler
            del self.info.settings.build_type

    def validate(self):
        if self.settings.os not in ["Windows", "Linux"] and not is_apple_os(self):
            raise ConanInvalidConfiguration(f"{self.name} is not supported on {self.settings.os}")
        if (self.settings.os in ["Windows", "Linux"] and self.settings.arch not in ["x86", "x86_64"] or
                is_apple_os(self) and self.settings.arch not in ["x86_64", "x86", "armv8"]):
            raise ConanInvalidConfiguration(f"{self.name} is not supported on {self.settings.os} {self.settings.arch}")

        if not self.options.agreed_to_license_terms:
            raise ConanInvalidConfiguration(
                "You must set '-o steamworks_sdk/*:agreed_to_license_terms=True' after you have accepted the terms of "
                f"the Valve Corporation Steamworks SDK Access Agreement at {self._license_url}."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if self.options.get_safe("build_glmgr"):
            tc = CMakeToolchain(self)
            tc.generate()

    def build(self):
        if self.options.get_safe("build_glmgr"):
            cmake = CMake(self)
            cmake.configure(build_script_folder=os.path.join(self.source_folder, "glmgr"))
            cmake.build()

    def _fetch_license(self):
        r = requests.get(self._license_url)
        r.raise_for_status()
        license_raw = r.text.split('<div class="access_agreement_area">', 1)[1].split("</div>", 1)[0]
        return textwrap.dedent(license_raw.replace("\n", "").replace("\r", "").replace("<br>", "\n"))

    def package(self):
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), self._fetch_license())

        if self.options.get_safe("build_glmgr"):
            cmake = CMake(self)
            cmake.install()

        copy(self, "*.h", os.path.join(self.source_folder, "public"), os.path.join(self.package_folder, "include"))

        # sdkencryptedappticket library files
        lib_dir = os.path.join(self.source_folder, "public", "steam", "lib")
        if self.settings.os == "Windows":
            lib_dir = os.path.join(lib_dir, "win64" if self.settings.arch == "x86_64" else "win32")
            copy(self, "*.lib", lib_dir, os.path.join(self.package_folder, "lib"))
            copy(self, "*.dll", lib_dir, os.path.join(self.package_folder, "bin"))
        if self.settings.os == "Linux":
            lib_dir = os.path.join(lib_dir, "linux64" if self.settings.arch == "x86_64" else "linux32")
            copy(self, "*.so", lib_dir, os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*.dylib", os.path.join(lib_dir, "osx"), os.path.join(self.package_folder, "lib"))

        # steam_api library files
        redist_dir = os.path.join(self.source_folder, "redistributable_bin")
        if self.settings.os == "Windows":
            name = "steam_api64" if self.settings.arch == "x86_64" else "steam_api"
            copy(self, f"{name}.lib", redist_dir, os.path.join(self.package_folder, "lib"), keep_path=False)
            copy(self, f"{name}.dll", redist_dir, os.path.join(self.package_folder, "bin"), keep_path=False)
        elif self.settings.os == "Linux":
            redist_dir = os.path.join(redist_dir, "linux64" if self.settings.arch == "x86_64" else "linux32")
            copy(self, "*.so", redist_dir, os.path.join(self.package_folder, "lib"))
        else:
            copy(self, "*.dylib", os.path.join(redist_dir, "osx"), os.path.join(self.package_folder, "lib"))

        if self.options.tools:
            copy(self, "*", os.path.join(self.source_folder, "tools"), os.path.join(self.package_folder, "share", "tools"))
            unzip(self, os.path.join(self.package_folder, "share", "tools", "ContentPrep.zip"),
                  destination=os.path.join(self.package_folder, "share", "tools"))
            os.unlink(os.path.join(self.package_folder, "share", "tools", "ContentPrep.zip"))
            unzip(self, os.path.join(self.package_folder, "share", "tools", "SteamPipeGUI.zip"),
                  destination=os.path.join(self.package_folder, "share", "tools"))
            os.unlink(os.path.join(self.package_folder, "share", "tools", "SteamPipeGUI.zip"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "SteamworksSDK")

        suffix = ""
        if self.settings.os == "Windows" and self.settings.arch == "x86_64":
            suffix = "64"

        self.cpp_info.components["steam_api"].set_property("cmake_target_name", "SteamworksSDK::SteamworksSDK")
        self.cpp_info.components["steam_api"].libs = ["steam_api" + suffix]

        self.cpp_info.components["sdkencryptedappticket"].set_property("cmake_target_name", "SteamworksSDK::AppTicket")
        self.cpp_info.components["sdkencryptedappticket"].set_property("nosoname", True)
        self.cpp_info.components["sdkencryptedappticket"].libs = ["sdkencryptedappticket" + suffix]

        if self.options.get_safe("build_glmgr"):
            self.cpp_info.components["glmgr"].set_property("cmake_target_name", "SteamworksSDK::GLMgr")
            self.cpp_info.components["glmgr"].libs = ["GLMgr"]
            self.cpp_info.components["glmgr"].defines.append("GL_SILENCE_DEPRECATION=1")
            self.cpp_info.components["glmgr"].frameworks = ["Cocoa", "IOKit", "OpenAL", "OpenGL"]
