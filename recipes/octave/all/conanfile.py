import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.env import Environment, VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import copy, rm, get
from conan.tools.gnu import Autotools, AutotoolsDeps, AutotoolsToolchain, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path

required_conan_version = ">=1.54.0"


class OctaveConan(ConanFile):
    name = "octave"
    description = "GNU Octave - a high-level language for numerical computations"
    license = "GPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://octave.org/"
    topics = ("matlab", "scientific", "numerical")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_curl": [True, False],
        "with_fftw": [True, False],
        "with_fltk": [True, False],
        "with_fontconfig": [True, False],
        "with_freetype": [True, False],
        "with_gl2ps": [True, False],
        "with_glpk": [True, False],
        "with_hdf5": [True, False],
        "with_magick": [True, False],
        "with_openmp": [True, False],
        "with_openssl": [True, False],
        "with_qhull": [True, False],
        "with_qt": [True, False],
        "with_rapidjson": [True, False],
        "with_sndfile": [True, False],
        "with_suitesparse": [True, False],
        "with_sundials": [True, False],
        "with_x": [True, False],
    }
    default_options = {
        "with_curl": True,
        "with_fftw": True,
        "with_fltk": True,
        "with_fontconfig": True,
        "with_freetype": True,
        "with_gl2ps": True,
        "with_glpk": True,
        "with_hdf5": True,
        "with_magick": True,
        "with_openmp": True,
        "with_openssl": True,
        "with_qhull": True,
        "with_qt": False,
        "with_rapidjson": True,
        "with_sndfile": True,
        "with_suitesparse": True,
        "with_sundials": True,
        "with_x": True,
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def config_options(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            del self.options.with_x
        if not self.options.with_qt and not self.options.with_fltk:
            del self.options.with_fontconfig
            del self.options.with_freetype
            del self.options.with_gl2ps

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        # https://wiki.octave.org/Building
        self.requires("openblas/0.3.27", options={"build_lapack": True})
        self.requires("pcre2/10.42")
        self.requires("readline/8.2")

        # Optional deps
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("bzip2/1.0.8")
        if self.options.with_curl:
            self.requires("libcurl/[>=7.78.0 <9]")
        if self.options.with_fftw:
            self.requires("fftw/3.3.10")
        if self.options.with_fltk:
            self.requires("fltk/1.3.9")
        if self.options.get_safe("with_fontconfig"):
            self.requires("fontconfig/2.15.0")
        if self.options.get_safe("with_freetype"):
            self.requires("freetype/2.13.2")
        if self.options.get_safe("with_gl2ps"):
            self.requires("gl2ps/1.4.2")
        if self.options.with_glpk:
            self.requires("glpk/5.0")
        if self.options.with_hdf5:
            self.requires("hdf5/1.14.4.3")
        if self.options.with_magick:
            self.requires("imagemagick/7.1.1.38")
        if self.options.with_openmp:
            self.requires("openmp/system")
        if self.options.with_openssl:
            self.requires("openssl/[>=1.1 <4]")
        if self.options.with_qhull:
            self.requires("qhull/8.0.1")
        if self.options.with_qt:
            self.requires("qt/[>=6.7 <7]", options={
                "opengl": "desktop",
                "gui": True,
                "widgets": True,
                "qttools": True,
                "qt5compat": True,
            })
            self.requires("qscintilla/2.14.1")
        if self.options.with_rapidjson:
            self.requires("rapidjson/1.1.0")
        if self.options.with_sndfile:
            self.requires("libsndfile/1.2.2")
        if self.options.with_suitesparse:
            self.requires("suitesparse-amd/3.3.3")
            self.requires("suitesparse-camd/3.3.3")
            self.requires("suitesparse-ccolamd/3.3.4")
            self.requires("suitesparse-cholmod/5.3.0")
            self.requires("suitesparse-colamd/3.3.4")
            self.requires("suitesparse-config/7.8.2")
            self.requires("suitesparse-cxsparse/4.4.1")
            self.requires("suitesparse-klu/2.3.4")
            self.requires("suitesparse-spqr/4.3.4")
            self.requires("suitesparse-umfpack/6.3.4")
        if self.options.with_sundials:
            self.requires("sundials/7.1.1")
        if self.options.get_safe("with_x"):
            self.requires("xorg/system")

        # TODO:
        # - ARPACK-NG
        # - gnuplot
        # - PortAudio
        # - QRUPDATE

    def validate(self):
        if not self.dependencies["openblas"].options.build_lapack:
            raise ConanInvalidConfiguration(
                "Octave requires OpenBLAS with LAPACK support (-o openblas/*:build_lapack=True)"
            )

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
        if self.options.with_qt:
            self.tool_requires("qt/<host_version>")
        self.tool_requires("f2c/20240312")
        self.tool_requires("flex/2.6.4")
        self.tool_requires("bison/3.8.2")
        self.tool_requires("gperf/3.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualBuildEnv(self).generate()
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")

        def yes_no(v):
            return "yes" if v else "no"

        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            "--disable-docs",
            "--disable-rpath",
            "--disable-hg-id",
            "--enable-fortran-calling-convention=f2c",
            f"--with-pkgconfigdir={unix_path(self, self.generators_folder)}",
            "--with-blas=openblas",
            "--with-framework-carbon",
            "--disable-java",
            "--without-java",
            f"--enable-openmp={yes_no(self.options.with_openmp)}",
            "--without-pcre",
            f"--enable-rapidjson={yes_no(self.options.with_rapidjson)}",
            f"--with-qt={self.dependencies['qt'].ref.version}" if self.options.with_qt else "--without-qt",
            f"--with-x={yes_no(self.options.get_safe('with_x'))}",
        ])

        # Possibly useful
        #   --enable-cross-guesses={conservative|risky}
        #   --enable-cross-tools    build cross tools (mkoctfile, octave-config) if
        #   --enable-no-undefined   pass -no-undefined to libtool when linking Octave
        #   --enable-year2038       support timestamps after 2038
        #   --with-libiconv-prefix     don't search for libiconv in includedir and libdir
        #   --with-libiconv-prefix[=DIR]  search for libiconv in DIR/include and DIR/lib
        #   --disable-readline      do not use readline library
        #   --with-libreadline-prefix     don't search for libreadline in includedir and libdir
        #   --with-libreadline-prefix[=DIR]  search for libreadline in DIR/include and DIR/lib
        #   --with-system-freefont=DIR

        def _configure_dep(configure_opt, dep_name, enabled):
            if enabled:
                includedir = unix_path(self, self.dependencies[dep_name].cpp_info.includedirs[0])
                libdir = unix_path(self, self.dependencies[dep_name].cpp_info.libdirs[0])
                tc.configure_args.extend([
                    f"--with-{configure_opt}",
                    f"--with-{configure_opt}-includedir={includedir}",
                    f"--with-{configure_opt}-libdir={libdir}",
                ])
            else:
                tc.configure_args.extend([f"--without-{configure_opt}"])

        _configure_dep("arpack", "arpack-ng", False)
        _configure_dep("bz2", "bzip2", True)
        _configure_dep("curl", "libcurl", self.options.with_curl)
        _configure_dep("fftw3", "fftw", self.options.with_fftw)
        _configure_dep("fftw3f", "fftw", self.options.with_fftw)
        _configure_dep("fltk", "fltk", self.options.with_fltk)
        _configure_dep("fontconfig", "fontconfig", self.options.get_safe("with_fontconfig"))
        _configure_dep("freetype", "freetype", self.options.get_safe("with_freetype"))
        _configure_dep("glpk", "glpk", self.options.with_glpk)
        _configure_dep("hdf5", "hdf5", self.options.with_hdf5)
        _configure_dep("lapack", "openblas", True)
        _configure_dep("magick", "imagemagick", self.options.with_magick)
        _configure_dep("openssl", "openssl", self.options.with_openssl)
        _configure_dep("pcre2", "pcre2", True)
        _configure_dep("portaudio", "portaudio", False)
        _configure_dep("qhull_r", "qhull", self.options.with_qhull)
        _configure_dep("qrupdate", "qrupdate", False)
        _configure_dep("qscintilla", "qscintilla", self.options.with_qt)
        _configure_dep("qt", "qt", self.options.with_qt)
        _configure_dep("sndfile", "libsndfile", self.options.with_sndfile)
        _configure_dep("amd", "suitesparse-amd", self.options.with_suitesparse)
        _configure_dep("camd", "suitesparse-camd", self.options.with_suitesparse)
        _configure_dep("ccolamd", "suitesparse-ccolamd", self.options.with_suitesparse)
        _configure_dep("cholmod", "suitesparse-cholmod", self.options.with_suitesparse)
        _configure_dep("colamd", "suitesparse-colamd", self.options.with_suitesparse)
        _configure_dep("cxsparse", "suitesparse-cxsparse", self.options.with_suitesparse)
        _configure_dep("klu", "suitesparse-klu", self.options.with_suitesparse)
        _configure_dep("spqr", "suitesparse-spqr", self.options.with_suitesparse)
        _configure_dep("suitesparseconfig", "suitesparse-config", self.options.with_suitesparse)
        _configure_dep("umfpack", "suitesparse-umfpack", self.options.with_suitesparse)
        _configure_dep("sundials_core", "sundials", self.options.with_sundials)
        _configure_dep("sundials_ida", "sundials",
                       self.options.with_sundials and
                       self.dependencies["sundials"].options.build_ida)
        _configure_dep("sundials_nvecserial", "sundials", self.options.with_sundials)
        _configure_dep("sundials_sunlinsolklu", "sundials",
            self.options.with_sundials
            and self.dependencies["sundials"].options.build_kinsol
            and self.dependencies["sundials"].options.get_safe("with_klu"))
        _configure_dep("z", "zlib", True)

        if self.options.with_magick:
            tc.configure_args.append("--with-magick=" + self.dependencies["imagemagick"].cpp_info.components["Magick++"].libs[0])

        if self.options.with_fltk:
            # FLTK from Conan does not provide fltk-config.
            # The build flags are passed via AutotoolsDeps instead.
            tc.configure_args.extend([
                "FLTK_CONFIG=no",
                "octave_cv_fltk_opengl_support=yes",
                "build_fltk_graphics=yes",
            ])
            tc.extra_defines.append("HAVE_FLTK=1")

        tc.generate()

        tc = PkgConfigDeps(self)
        tc.generate()

        deps = AutotoolsDeps(self)
        deps.generate()

        if is_msvc(self):
            env = Environment()
            automake_conf = self.dependencies.build["automake"].conf_info
            compile_wrapper = unix_path(self, automake_conf.get("user.automake:compile-wrapper", check_type=str))
            ar_wrapper = unix_path(self, automake_conf.get("user.automake:lib-wrapper", check_type=str))
            env.define("CC", f"{compile_wrapper} cl -nologo")
            env.define("CXX", f"{compile_wrapper} cl -nologo")
            env.define("LD", "link -nologo")
            env.define("AR", f"{ar_wrapper} lib")
            env.define("NM", "dumpbin -symbols")
            env.define("OBJDUMP", ":")
            env.define("RANLIB", ":")
            env.define("STRIP", ":")
            env.vars(self).save_script("conanbuild_msvc")

    def build(self):
        autotools = Autotools(self)
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
        # TODO: split into octave and octaveinterp components
        self.cpp_info.set_property("pkg_config_name", "octave")
        self.cpp_info.libs = ["octave"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["dl", "m", "pthread"])
