from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CudaCcclConan(ConanFile):
    name = "cuda-cccl"
    description = "CUDA C++ Core Libraries"
    homepage = "https://nvidia.github.io/cccl/cpp.html"
    topics = ("cuda", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "cudax": [True, False],
    }
    default_options = {
        "cudax": False,
    }

    def config_options(self):
        if Version(self.version) < "2.5":
            del self.options.cudax

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def requirements(self):
        if Version(self.version) >= "2.0":
            self.requires(f"libcudacxx/{self.version}")
            self.requires(f"cub/{self.version}")
            self.requires(f"thrust/{self.version}")
            if self.options.get_safe("cudax"):
                self.requires(f"cudax/{self.version}")
        else:
            self.requires(f"libcudacxx/{self.version}")
            self.requires("cub/[^1]")
            self.requires("thrust/[^1]")

    def validate(self):
        check_min_cppstd(self, 11)

    def package_info(self):
        # https://github.com/NVIDIA/cccl/blob/main/lib/cmake/cccl/cccl-config.cmake
        self.cpp_info.set_property("cmake_file_name", "CCCL")
        self.cpp_info.set_property("cmake_target_name", "CCCL::CCCL")
        self.cpp_info.set_property("cmake_additional_variables_prefixes", ["CCCL"])

        self.cpp_info.components["libcudacxx"].set_property("cmake_target_name", "CCCL::libcudacxx")
        self.cpp_info.components["libcudacxx"].requires = ["libcudacxx::libcudacxx"]

        self.cpp_info.components["cub"].set_property("cmake_target_name", "CCCL::CUB")
        self.cpp_info.components["cub"].requires = ["cub::cub"]

        self.cpp_info.components["thrust"].set_property("cmake_target_name", "CCCL::Thrust")
        self.cpp_info.components["thrust"].requires = ["thrust::thrust"]

        if self.options.get_safe("cudax"):
            self.cpp_info.components["cudax"].set_property("cmake_target_name", "CCCL::cudax")
            self.cpp_info.components["cudax"].requires = ["cudax::cudax"]

        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.resdirs = []

        for _, component in self.cpp_info.components.items():
            component.bindirs = []
            component.libdirs = []
            component.frameworkdirs = []
            component.resdirs = []
            component.includedirs = []
