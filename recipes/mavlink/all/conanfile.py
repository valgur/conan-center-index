import os

from conan import ConanFile
from conan.tools.cmake import cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class MavlinkConan(ConanFile):
    name = "mavlink"
    description = "Marshalling / communication library for drones."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mavlink/mavlink"
    topics = ("mav", "drones", "marshalling", "communication")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        # https://mavlink.io/en/messages/README.html
        "dialect": [
            "all",
            "common",
            "standard",
            "minimal",
            "development",
            "ardupilotmega",
            "ASLUAV",
            "AVSSUAS",
            "csAirLink",
            "cubepilot",
            "icarous",
            "loweheiser",
            "matrixpilot",
            "paparazzi",
            "storm32",
            "ualberta",
            "uAvionix",
        ],
        # https://github.com/ArduPilot/pymavlink/blob/v2.4.42/tools/mavgen.py#L24
        "wire_protocol": ["0.9", "1.0", "2.0"],
    }
    default_options = {
        "dialect": "common",
        "wire_protocol": "2.0",
    }
    languages = ["C"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.settings.clear()

    def source(self):
        info = self.conan_data["sources"][self.version]
        get(self, **info["mavlink"], strip_root=True)
        get(self, **info["pymavlink"], strip_root=True, destination="pymavlink")

    def generate(self):
        venv = self._utils.PythonVenv(self)
        venv.generate()

    def build(self):
        # Reproduce these CMake steps https://github.com/mavlink/mavlink/blob/5e3a42b8f3f53038f2779f9f69bd64767b913bb8/CMakeLists.txt#L32-L39
        # for a tighter control over the created temporary Python environment.
        self._utils.pip_install(self, ["-r", "pymavlink/requirements.txt"], cwd=self.source_folder)
        self.run("python3 -m pymavlink.tools.mavgen --lang=C"
                 f" --wire-protocol={self.options.wire_protocol}"
                 f" --output {self.build_folder}/include/mavlink/"
                 f" message_definitions/v1.0/{self.options.dialect}.xml",
                 cwd=self.source_folder)

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.build_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "MAVLink")
        self.cpp_info.set_property("cmake_target_name", "MAVLink::mavlink")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
