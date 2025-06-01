from conan import ConanFile

required_conan_version = ">=2.1"


class LibjpegMetaConan(ConanFile):
    name = "libjpeg-meta"
    version = "latest"
    description = "Conan meta-package to select between libjpeg and its variants"
    topics = ("jpeg", "meta")
    options = {
        "provider": ["libjpeg", "libjpeg-turbo", "mozjpeg"],
    }
    default_options = {
        "provider": "libjpeg-turbo",
    }

    # Don't allow changes to this recipe to invalidate consuming recipe package IDs.
    package_id_embed_mode = "unrelated_mode"
    package_id_non_embed_mode = "unrelated_mode"
    package_id_unknown_mode = "unrelated_mode"
    build_mode = "unrelated_mode"

    def package_id(self):
        self.info.clear()

    def requirements(self):
        if self.options.provider == "libjpeg":
            self.requires("libjpeg/[>=9d]", transitive_headers=True, transitive_libs=True)
        elif self.options.provider == "libjpeg-turbo":
            self.requires("libjpeg-turbo/[>=2.0.6]", transitive_headers=True, transitive_libs=True)
        elif self.options.provider == "mozjpeg":
            self.requires("mozjpeg/[>=3.3.1]", transitive_headers=True, transitive_libs=True)

    def package_info(self):
        if self.options.provider == "libjpeg":
            self.cpp_info.components["jpeg"].requires = ["libjpeg::libjpeg"]
        elif self.options.provider == "libjpeg-turbo":
            self.cpp_info.components["jpeg"].requires = ["libjpeg-turbo::jpeg"]
            self.cpp_info.components["turbojpeg"].requires = ["libjpeg-turbo::turbojpeg"]
        elif self.options.provider == "mozjpeg":
            self.cpp_info.components["jpeg"].requires = ["mozjpeg::libjpeg"]
            self.cpp_info.components["turbojpeg"].requires = ["mozjpeg::libturbojpeg"]

        def _clear_dirs(cpp_info):
            cpp_info.includedirs = []
            cpp_info.libdirs = []
            cpp_info.bindirs = []
            cpp_info.resdirs = []
            cpp_info.frameworkdirs = []

        _clear_dirs(self.cpp_info)
        _clear_dirs(self.cpp_info.components["jpeg"])
        if self.options.provider != "libjpeg":
            _clear_dirs(self.cpp_info.components["turbojpeg"])
