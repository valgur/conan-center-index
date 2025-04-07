import os

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.files import get, copy, rmdir, download
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path

required_conan_version = ">=2.1"

class TzConan(ConanFile):
    name = "tz"
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.iana.org/time-zones"
    description = "The Time Zone Database contains data that represent the history of local time for many representative locations around the globe."
    topics = ("tz", "tzdb", "time", "zone", "date")
    package_type = "application" # This is not an application, but application has the correct traits to provide a runtime dependency on data
    settings = "os", "build_type", "arch", "compiler"
    options = {
        "with_binary_db": [True, False],
    }
    default_options = {
        "with_binary_db": True,
    }

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def build_requirements(self):
        if self.options.with_binary_db:
            self.tool_requires("mawk/1.3.4-20230404")
            if self.settings_build.os == "Windows":
                self.win_bash = True
                if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                    self.tool_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["sources"], strip_root=True)
        download(self, **self.conan_data["sources"][self.version]["windows_zones"], filename="windowsZones.xml")

    def generate(self):
        if self.options.with_binary_db:
            tc = AutotoolsToolchain(self)
            build_cc = unix_path(self, tc.vars().get("CC_FOR_BUILD" if cross_building(self) else "CC", "cc"))
            awk_path = unix_path(self, os.path.join(self.dependencies.direct_build["mawk"].package_folder, "bin", "mawk"))
            tc.make_args.extend([
                f"cc={build_cc}",
                f"AWK={awk_path}",
            ])
            tc.generate()

    def build(self):
        if self.options.with_binary_db:
            autotools = Autotools(self)
            autotools.make(args=["-C", self.source_folder.replace("\\", "/")])

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        if self.options.with_binary_db:
            autotools = Autotools(self)
            destdir = self.package_folder.replace('\\', '/')
            autotools.install(args=["-C", self.source_folder.replace("\\", "/"), f"DESTDIR={destdir}"])
            rmdir(self, os.path.join(self.package_folder, "usr", "share", "man"))
            # INFO: The library does not have a public API, it's used to build the zic and zdump tools
            rmdir(self, os.path.join(self.package_folder, "usr", "lib"))
        else:
            tzdata = [
                # This file listing is drawn from the source distribution of the tz database at
                # https://data.iana.org/time-zones/releases/tzdata2023c.tar.gz. It includes only data
                # files, and excludes project documentation such as CONTRIBUTING, NEWS, README,
                # SECURITY, theory.html.
                "africa",
                "antarctica",
                "asia",
                "australasia",
                "backward",
                "backzone",
                "calendars",
                "checklinks.awk",
                "checktab.awk",
                "etcetera",
                "europe",
                "factory",
                "iso3166.tab",
                "leap-seconds.list",
                "leapseconds",
                "leapseconds.awk",
                "northamerica",
                "southamerica",
                "version",
                "ziguard.awk",
                "zishrink.awk",
                "zone.tab",
                "zone1970.tab",
                # This file is maintained by CLDR and is required to provide a conversion between
                # windows time zone names and the IANA time zone names. This enables the IANA tzdb
                # to be used on windows. For more information, see https://cldr.unicode.org/index
                "windowsZones.xml",
            ]
            for data in tzdata:
                copy(self, data, dst=os.path.join(self.package_folder, "res", "tzdata"), src=self.source_folder)

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.resdirs = ["res"]
        self.buildenv_info.define("TZDATA", os.path.join(self.package_folder, "res", "tzdata"))
        self.runenv_info.define("TZDATA", os.path.join(self.package_folder, "res", "tzdata"))
        if self.options.with_binary_db:
            self.cpp_info.resdirs = [os.path.join("usr", "share")]
            self.cpp_info.bindirs = [os.path.join("usr", "bin"), os.path.join("usr", "sbin")]
            self.buildenv_info.define("TZDATA", os.path.join(self.package_folder, "usr", "share", "zoneinfo"))
            self.runenv_info.define("TZDATA", os.path.join(self.package_folder, "usr", "share", "zoneinfo"))
