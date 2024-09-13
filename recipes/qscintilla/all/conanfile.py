import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, chdir, save
from conan.tools.gnu.autotools import Autotools
from conan.tools.gnu.autotoolstoolchain import AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import unix_path

required_conan_version = ">=1.60.0 <2.0 || >=2.0.5"


class QScintillaConan(ConanFile):
    name = "qscintilla"
    description = "QScintilla is a Qt port of the Scintilla text editing component"
    license = "GPL-3.0-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://riverbankcomputing.com/software/qscintilla"
    topics = ("qt", "scintilla", "text-editor", "widget")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _min_cppstd(self):
        return 11

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.options["qt"].widgets = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("qt/[>=6.7 <7]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        if not self.dependencies["qt"].options.widgets:
            raise ConanInvalidConfiguration("QScintilla requires -o qt/*:widgets=True")

    def build_requirements(self):
        self.tool_requires("qt/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _configure_qmake(self):
        # Set standard build args for qmake
        tc = AutotoolsToolchain(self)
        tc_vars = tc.vars()
        cc = tc_vars.get("CC")
        cxx = tc_vars.get("CXX")
        cppflags = tc_vars.get("CPPFLAGS", "")
        cflags = tc_vars.get("CFLAGS", "") + " " + cppflags
        cxxflags = tc_vars.get("CXXFLAGS", "") + " " + cppflags
        ldflags = tc_vars.get("LDFLAGS", "")
        qmake_args = [
            f'QMAKE_CC="{cc}"',
            f'QMAKE_LINK_C="{cc}"',
            f'QMAKE_LINK_C_SHLIB="{cc}"',
            f'QMAKE_CXX="{cxx}"',
            f'QMAKE_LINK="{cxx}"',
            f'QMAKE_LINK_SHLIB="{cxx}"',
        ]
        if cflags:
            qmake_args.append(f'QMAKE_CFLAGS+="{cflags}"')
        if cxxflags:
            qmake_args.append(f'QMAKE_CXXFLAGS+="{cxxflags}"')
        if ldflags:
            qmake_args.append(f'QMAKE_LDFLAGS+="{ldflags}"')
        if self.options.shared:
            qmake_args.append("CONFIG-=staticlib")
        else:
            qmake_args.append("CONFIG+=staticlib")
        if self.settings.build_type == "Debug":
            qmake_args.append("CONFIG+=debug")
        elif self.settings.build_type == "Release":
            qmake_args.append("CONFIG+=release")
        elif self.settings.build_type == "RelWithDebInfo":
            qmake_args.append("CONFIG+=release")
            qmake_args.append("CONFIG+=debug")
        return qmake_args

    def generate(self):
        VirtualBuildEnv(self).generate()
        VirtualRunEnv(self).generate(scope="build")

        tc = AutotoolsToolchain(self)
        tc.generate()

        qt = self.dependencies["qt"]
        qmake_args = self._configure_qmake()
        qmake_args.append(f"QT_MAJOR_VERSION={qt.ref.version.major}")
        qmake_args.append(f"DESTDIR={unix_path(self, os.path.join(self.package_folder, 'lib'))}")
        if self.options.shared:
            qmake_args.append("CONFIG-=staticlib")
        else:
            qmake_args.append("CONFIG+=staticlib")
        save(self, os.path.join(self.generators_folder, "qmake.conf"), "\n".join(qmake_args))

    def build(self):
        apply_conandata_patches(self)
        with chdir(self, os.path.join(self.source_folder, "src")):
            self.run(f"qmake -d QMAKESPEC={self.generators_folder}", scope="build")
            autotools = Autotools(self)
            autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        with chdir(self, os.path.join(self.source_folder, "src")):
            autotools = Autotools(self)
            autotools.install(args=[f"DESTDIR={unix_path(self, self.package_folder)}", "PREFIX=/"])

    def package_info(self):
        qt_major = self.dependencies["qt"].ref.version.major
        lib_name = f"qscintilla2_qt{qt_major}"
        if self.settings.build_type == "Debug":
            if is_apple_os(self):
                lib_name += "_debug"
            elif self.settings.os == "Windows":
                lib_name += "d"
        if not self.options.shared:
            lib_name += "_static"
        self.cpp_info.libs = [lib_name]

        self.cpp_info.requires = ["qt::qtWidgets"]
        if self.settings.os != "iOS":
            self.cpp_info.requires.append("qt::qtPrintSupport")
        if qt_major == 5 and is_apple_os(self):
            self.cpp_info.frameworks.extend(["qtMacExtras"])
