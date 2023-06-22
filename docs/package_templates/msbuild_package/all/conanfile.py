from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    export_conandata_patches,
    get,
    replace_in_file,
    rm,
)
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, MSBuild, MSBuildDeps, MSBuildToolchain
import os


required_conan_version = ">=1.53.0"


class PackageConan(ConanFile):
    name = "package"
    description = "short description"
    # Use short name only, conform to SPDX License List: https://spdx.org/licenses/
    # In case not listed there, use "LicenseRef-<license-file-name>"
    license = ""
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/project/package"
    # no "conan" and project name in topics. Use topics from the upstream listed on GH
    topics = ("topic1", "topic2", "topic3")
    # package_type should usually be "library" (if there is shared option)
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

    # no exports_sources attribute, but export_sources(self) method instead
    # this allows finer grain exportation of patches per version
    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        # for plain C projects only
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        # prefer self.requires method instead of requires attribute
        self.requires("dependency/0.8.1")

    def validate(self):
        # in case it does not work in another configuration, it should validated here too
        if not is_msvc(self):
            raise ConanInvalidConfiguration(
                f"{self.ref} can be built only by Visual Studio and msvc."
            )

    # if another tool than the compiler or CMake is required to build the project (pkgconf, bison, flex etc)
    def build_requirements(self):
        self.tool_requires("tool/x.y.z")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @property
    def _msbuild_configuration(self):
        # Customize to Release when RelWithDebInfo or MinSizeRel, if upstream build files
        # don't have RelWithDebInfo and MinSizeRel.
        # Moreover:
        # - you may have to change these values if upstream build file uses custom configuration names.
        # - configuration of MSBuildToolchain/MSBuildDeps & build_type of MSBuild may have to be different.
        #   Its unusual, but it happens when there is a preSolution/postSolution mapping with different names.
        #   * build_type attribute of MSBuild should match preSolution
        #   * configuration attribute of MSBuildToolchain/MSBuildDeps should match postSolution
        return "Debug" if self.settings.build_type == "Debug" else "Release"

    def generate(self):
        tc = MSBuildToolchain(self)
        tc.configuration = self._msbuild_configuration
        tc.generate()

        # If there are requirements
        deps = MSBuildDeps(self)
        deps.configuration = self._msbuild_configuration
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        # remove bundled xxhash
        rm(self, "whateer.*", os.path.join(self.source_folder, "lib"))
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"), "...", "")

        # Allows to inject platform toolset, and props file generated by MSBuildToolchain & MSBuildDeps
        # TODO: to remove once https://github.com/conan-io/conan/pull/12817 available in conan client
        vcxproj_files = ["path/to/vcxproj_file1", "path/to/vcxproj_file2", "..."]
        platform_toolset = MSBuildToolchain(self).toolset
        import_conan_generators = ""
        for props_file in ["conantoolchain.props", "conandeps.props"]:
            props_path = os.path.join(self.generators_folder, props_file)
            if os.path.exists(props_path):
                import_conan_generators += f'<Import Project="{props_path}" />'
        for vcxproj_file in vcxproj_files:
            replace_in_file(
                self,
                vcxproj_file,
                # change this v142 value depending on actual value in vcxproj file
                "<PlatformToolset>v142</PlatformToolset>",
                f"<PlatformToolset>{platform_toolset}</PlatformToolset>",
            )
            if props_path:
                replace_in_file(
                    self,
                    vcxproj_file,
                    '<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />',
                    f'{import_conan_generators}<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />',
                )

    def build(self):
        self._patch_sources()  # It can be apply_conandata_patches(self) only in case no more patches are needed
        msbuild = MSBuild(self)
        msbuild.build_type = self._msbuild_configuration
        # customize according the solution file and compiler version
        msbuild.build(sln="project_2017.sln")

    def package(self):
        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )
        copy(
            self,
            "*.lib",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "lib"),
            keep_path=False,
        )
        copy(
            self,
            "*.dll",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "bin"),
            keep_path=False,
        )
        copy(
            self,
            "*.h",
            src=os.path.join(self.source_folder, "include"),
            dst=os.path.join(self.package_folder, "include"),
        )

    def package_info(self):
        self.cpp_info.libs = ["package_lib"]
