import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, rm, rmdir
from conan.tools.gnu import PkgConfigDeps
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class GnuradioConan(ConanFile):
    name = "gnuradio"
    description = "GNU Radio – the Free and Open Software Radio Ecosystem"
    license = "LGPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gnuradio.org/"
    topics = ("radio", "software-defined-radio", "sdr", "dsp", "wireless", "cybersecurity", "gnu")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_python": [True, False],
        "build_analog": [True, False],
        "build_audio": [True, False],
        "build_blocks": [True, False],
        "build_channels": [True, False],
        "build_ctrlport": [True, False],
        "build_digital": [True, False],
        "build_dtv": [True, False],
        "build_fec": [True, False],
        "build_fft": [True, False],
        "build_filter": [True, False],
        "build_iio": [False],
        "build_network": [True, False],
        "build_pdu": [True, False],
        "build_qtgui": [True, False],
        "build_soapy": [False],
        "build_trellis": [True, False],
        "build_uhd": [False],
        "build_video_sdl": [False],
        "build_vocoder": [True, False],
        "build_wavelet": [True, False],
        "build_zeromq": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_python": False,
        "build_analog": True,
        "build_audio": True,
        "build_blocks": True,
        "build_channels": True,
        "build_ctrlport": True,
        "build_digital": True,
        "build_dtv": True,
        "build_fec": True,
        "build_fft": True,
        "build_filter": True,
        "build_iio": False,
        "build_network": True,
        "build_pdu": True,
        "build_qtgui": True,
        "build_soapy": False,
        "build_trellis": True,
        "build_uhd": False,
        "build_video_sdl": False,
        "build_vocoder": False,
        "build_wavelet": True,
        "build_zeromq": True,
    }

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "7",
            "clang": "6",
            "apple-clang": "10",
            "Visual Studio": "15",
            "msvc": "191",
        }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.84.0", transitive_headers=True, transitive_libs=True)
        self.requires("gnuradio-volk/3.1.2", transitive_headers=True, transitive_libs=True)
        self.requires("gsl/2.7.1")
        self.requires("libunwind/1.8.0")
        self.requires("mpir/3.0.0", options={"enable_gmpcompat": True}, transitive_headers=True, transitive_libs=True)
        self.requires("spdlog/1.13.0", transitive_headers=True, transitive_libs=True)
        self.requires("thrift/0.18.1")
        if self.options.with_python:
            self.requires("cpython/3.10.0")
            self.requires("pybind11/2.12.0")
        if self.options.build_audio:
            self.requires("libalsa/1.2.10")
            # self.requires("oss/0")
            # self.requires("jack/0")
            # self.requires("portaudio/0")
        if self.options.build_blocks:
            self.requires("libsndfile/1.2.2")
        if self.options.build_fft:
            self.requires("fftw/3.3.10")
        if self.options.build_qtgui:
            self.requires("qt/5.15.11")
            self.requires("qwt/6.2.0")
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.requires("libglvnd/1.7.0")
            else:
                self.requires("opengl/system")
        if self.options.build_zeromq:
            self.requires("zeromq/4.3.5")
        # if self.options.build_iio:
        #     self.requires("libiio/0.21")
        #     self.requires("libad9361/0.1")
        # if self.options.build_soapy:
        #     self.requires("soapysdr/latest")
        # if self.options.build_uhd:
        #     self.requires("uhd/3.15.0")
        # if self.options.build_video_sdl:
        #     self.requires("sdl/1.x")
        # if self.options.build_vocoder:
        #     self.requires("codec2/1.0.1")
        #     self.requires("gsm/1.0.19")

        if self.options.build_qtgui:
            self.requires("xkbcommon/1.5.0", override=True)
            if self.options.with_python:
                self.requires("fontconfig/2.15.0", override=True)
                self.requires("libpng/1.6.42", override=True)


    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def build_requirements(self):
        # For CMAKE_REQUIRE_FIND_PACKAGE_<package>
        self.tool_requires("cmake/[>=3.22 <4]")
        if self.options.with_python:
            self.tool_requires("cpython/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @property
    def _find_package_enabled(self):
        return {
            "ALSA": self.options.build_audio,
            "Codec2": False,
            "Doxygen": False,
            "FFTW3f": self.options.build_fft,
            "GMP": True,
            "GSL": True,
            "GSM": False,
            "Git": False,
            "JACK": False,
            "MPIR": True,
            "MPLIB": True,
            "MathJax2": False,
            "OSS": False,
            "OpenGL": self.options.build_qtgui,
            "PORTAUDIO": False,
            "PythonInterp": True,
            "PythonLibs": self.options.with_python,
            "Qt5": self.options.build_qtgui,
            "Qwt": self.options.build_qtgui,
            "SDL": False,
            "SNDFILE": self.options.build_blocks,
            "SoapySDR": False,
            "THRIFT": True,
            "UHD": False,
            "VOLK": True,
            "ZeroMQ": self.options.build_zeromq,
            "libad9361": False,
            "libiio": False,
            "libunwind": True,
            "pybind11": self.options.with_python,
            "spdlog": True,
        }

    def generate(self):
        venv = VirtualBuildEnv(self)
        venv.generate()

        tc = CMakeToolchain(self)
        tc.variables["ENABLE_PYTHON"] = self.options.with_python
        tc.variables["ENABLE_GR_ANALOG"] = self.options.build_analog
        tc.variables["ENABLE_GR_AUDIO"] = self.options.build_audio
        tc.variables["ENABLE_GR_BLOCKS"] = self.options.build_blocks
        tc.variables["ENABLE_GR_CHANNELS"] = self.options.build_channels
        tc.variables["ENABLE_GR_CTRLPORT"] = self.options.build_ctrlport
        tc.variables["ENABLE_GR_DIGITAL"] = self.options.build_digital
        tc.variables["ENABLE_GR_DTV"] = self.options.build_dtv
        tc.variables["ENABLE_GR_FEC"] = self.options.build_fec
        tc.variables["ENABLE_GR_FFT"] = self.options.build_fft
        tc.variables["ENABLE_GR_FILTER"] = self.options.build_filter
        tc.variables["ENABLE_GR_IIO"] = self.options.build_iio
        tc.variables["ENABLE_GR_NETWORK"] = self.options.build_network
        tc.variables["ENABLE_GR_PDU"] = self.options.build_pdu
        tc.variables["ENABLE_GR_QTGUI"] = self.options.build_qtgui
        tc.variables["ENABLE_GR_SOAPY"] = self.options.build_soapy
        tc.variables["ENABLE_GR_TRELLIS"] = self.options.build_trellis
        tc.variables["ENABLE_GR_UHD"] = self.options.build_uhd
        tc.variables["ENABLE_GR_VIDEO_SDL"] = self.options.build_video_sdl
        tc.variables["ENABLE_GR_VOCODER"] = self.options.build_vocoder
        tc.variables["ENABLE_GR_WAVELET"] = self.options.build_wavelet
        tc.variables["ENABLE_GR_ZEROMQ"] = self.options.build_zeromq
        tc.variables["GR_PKG_DATA_DIR"] = "res"
        tc.variables["ENABLE_TESTING"] = False
        tc.variables["ENABLE_EXAMPLES"] = False
        tc.variables["ENABLE_NATIVE"] = False
        tc.variables["ENABLE_DOXYGEN"] = False
        tc.variables["ENABLE_MANPAGES"] = False
        for pkg, enabled in self._find_package_enabled.items():
            require = 'REQUIRE' if enabled else 'DISABLE'
            tc.variables[f"CMAKE_{require}_FIND_PACKAGE_{pkg}"] = True
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        deps = PkgConfigDeps(self)
        deps.generate()


    def _patch_sources(self):
        pass

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        # rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        # rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rm(self, "gnuradio-config-info", os.path.join(self.package_folder, "bin"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Gnuradio")
        self.cpp_info.set_property("cmake_target_name", "gnuradio::gnuradio")

        def _add_component(name, requires=None):
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", f"gnuradio::gnuradio-{name}")
            component.set_property("pkg_config_name", f"gnuradio-{name}")
            component.libs = [f"gnuradio-{name}"]
            if name != "runtime":
                component.requires = ["runtime"]
            component.requires += requires or []

        _add_component("runtime", requires=[
            "pmt",
            "boost::boost",
            "gnuradio-volk::gnuradio-volk",
            "gsl::gsl",
            "libunwind::libunwind",
            "mpir::mpir",
            "spdlog::spdlog",
            "thrift::thrift",
        ])
        self.cpp_info.components["runtime"].defines.extend(["GR_MPLIB_GMP", "GR_PERFORMANCE_COUNTERS"])
        if self.options.with_python:
            self.cpp_info.components["runtime"].requires.extend(["cpython::cpython", "pybind11::pybind11"])
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["runtime"].system_libs.extend(["m", "rt"])

        _add_component("pmt", requires=["boost::boost"])

        if self.options.build_analog:
            _add_component("analog", requires=["gnuradio-volk::gnuradio-volk"])
        if self.options.build_audio:
            _add_component("audio", requires=[
                "blocks",
                "libalsa::libalsa",
                # "oss::oss",
                # "jack::jack",
                # "portaudio::portaudio",
            ])
        if self.options.build_blocks:
            _add_component("blocks", requires=["libsndfile::libsndfile", "gnuradio-volk::gnuradio-volk"])
        if self.options.build_channels:
            _add_component("channels", requires=["filter"])
        if self.options.build_ctrlport:
            _add_component("ctrlport")
        if self.options.build_digital:
            _add_component("digital", requires=["filter", "blocks", "analog", "boost::boost", "gnuradio-volk::gnuradio-volk"])
        if self.options.build_dtv:
            _add_component("dtv")
        if self.options.build_fec:
            _add_component("fec", requires=["blocks"])
        if self.options.build_fft:
            _add_component("fft", requires=["fftw::fftw", "gnuradio-volk::gnuradio-volk"])
        if self.options.build_filter:
            _add_component("filter", requires=["fft"])
        if self.options.build_iio:
            _add_component("iio", requires=["blocks", "libiio::libiio", "libad9361::libad9361"])
        if self.options.build_network:
            _add_component("network")
        if self.options.build_pdu:
            _add_component("pdu")
        if self.options.build_qtgui:
            _add_component("qtgui", requires=["qt::qt", "qwt::qwt"])
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["qtgui"].requires.append("libglvnd::libglvnd")
            else:
                self.cpp_info.components["qtgui"].requires.append("opengl::opengl")
        if self.options.build_soapy:
            _add_component("soapy", requires=["soapysdr::soapysdr"])
        if self.options.build_trellis:
            _add_component("trellis", requires=["digital"])
        if self.options.build_uhd:
            _add_component("uhd", requires=["uhd::uhd"])
        if self.options.build_video_sdl:
            _add_component("video-sdl", requires=["sdl::sdl"])
        if self.options.build_vocoder:
            _add_component("vocoder", requires=["codec2::codec2", "gsm::gsm"])
        if self.options.build_wavelet:
            _add_component("wavelet")
        if self.options.build_zeromq:
            _add_component("zeromq", requires=["zeromq::zeromq"])
