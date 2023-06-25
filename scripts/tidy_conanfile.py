import inspect
import io
import os
import re
import sys
import warnings
from pathlib import Path
from textwrap import indent

import black
from conan import ConanFile


class ConanFileDetails:
    def __init__(self, conanfile_path):
        conanfile_path = Path(conanfile_path)
        conanfile = conanfile_path.read_text(encoding="utf-8")
        conanfile = black.format_file_contents(conanfile, fast=False, mode=black.FileMode())
        eval(compile(conanfile, str(conanfile_path), "exec"), globals(), locals())
        conanfile_class = [
            value
            for value in locals().values()
            if inspect.isclass(value) and issubclass(value, ConanFile) and value != ConanFile
        ][0]

        methods = {}
        props = {}
        attrs = {}
        for attr, value in conanfile_class.__dict__.items():
            if attr.startswith("__"):
                continue
            # Get the source file this attribute was defined in
            if hasattr(value, "__call__") and Path(inspect.getsourcefile(value)) == conanfile_path:
                methods[attr] = inspect.getsource(value)
            elif isinstance(value, property) and Path(inspect.getsourcefile(value.fget)) == conanfile_path:
                props[attr] = inspect.getsource(value.fget)
            elif value is not None:
                attrs[attr] = value

        self.head: str = re.split(r"class\s+\w+\(ConanFile\):", conanfile, flags=re.MULTILINE)[0]
        self.class_name: str = conanfile_class.__name__
        self.attrs: dict[str, object] = attrs
        self.props: dict[str, str] = props
        self.methods: dict[str, str] = methods

    @property
    def is_header_only(self):
        if "package_type" in self.attrs:
            return self.attrs["package_type"] == "header-only"
        if self.attrs.get("no_copy_source") is True:
            return True
        if "package_id" in self.methods:
            return (
                "self.info.header_only()" in self.methods["package_id"]
                or "self.info.clear()" in self.methods["package_id"]
            )
        return False

    @property
    def generators(self):
        if "generate" not in self.methods:
            return set()
        return set(re.findall(r"(\w+(?:Deps|Toolchain))", self.methods["generate"]))

    @property
    def build_system(self):
        generators = self.generators
        build = self.methods.get("build", "")
        if generators.intersection({"AutotoolsDeps", "AutotoolsToolchain"}) or "Autotools" in build:
            return "Autotools"
        if generators.intersection({"BazelDeps", "BazelToolchain"}) or "Bazel" in build:
            return "Bazel"
        if generators.intersection({"CMakeDeps", "CMakeToolchain"}) or "CMake" in build:
            return "CMake"
        if generators.intersection({"MesonToolchain"}) or "Meson" in build:
            return "Meson"
        if generators.intersection({"MSBuildDeps", "MSBuildToolchain"}) or "MSBuild" in build:
            return "MSBuild"
        if generators.intersection({"XCodeDeps", "XCodeToolchain"}) or "XCode" in build:
            return "XCode"
        return None


def tidy_conanfile(conanfile_path, write=True):
    conanfile_path = Path(conanfile_path)
    rel_conanfile_path = str(conanfile_path).split(f"recipes{os.sep}", 1)[-1]
    details = ConanFileDetails(conanfile_path)

    is_header_only = details.is_header_only

    # tuple of (attr, is_required)
    attr_order = [
        ("name", True),
        ("description", True),
        ("license", True),
        ("url", True),
        ("homepage", True),
        ("topics", True),
        ("package_type", True),
        ("settings", True),
        ("options", not is_header_only),
        ("default_options", not is_header_only),
        ("options_description", False),
        ("no_copy_source", is_header_only),
        ("provides", False),
        ("deprecated", False),
    ]
    expected_attrs = {attr for attr, is_required in attr_order}
    disallowed_attrs = [
        "version",
        "user",
        "channel",
        "author",
        "requires",
        "build_requires",
        "tool_requires",
        "test_requires",
        "python_requires",
        "python_requires_extend",
        "exports",
        "exports_sources",
        "conan_data",
        "info",
        "package_id_embed_mode",
        "package_id_non_embed_mode",
        "package_id_unknown_mode",
        "generators",
        "build_policy",
        "win_bash",
        "win_bash_run",
        "source_folder",
        "export_sources_folder",
        "build_folder",
        "package_folder",
        "recipe_folder",
        "folders",
        "cpp",
        "layouts",
        "cpp_info",
        "buildenv_info",
        "runenv_info",
        "conf_info",
        "dependencies",
        "conf",
        "revision_mode",
        "upload_policy",
        "required_conan_version",
        "short_paths",
        "source_subfolder",
        "_source_subfolder",
        "build_subfolder",
        "_build_subfolder",
    ]

    def prepend_to_method(method, prepend):
        return method.replace("self):\n", f"self):\n{indent(prepend, '    ')}\n")

    if is_header_only:
        details.attrs["package_type"] = "header-only"
        details.attrs["no_copy_source"] = True
        if "header-only" not in details.attrs["topics"]:
            details.attrs["topics"] = tuple(list(details.attrs["topics"]) + ["header-only"])
        if "self.cpp_info.bindirs = []" not in details.methods["package_id"]:
            details.methods["package_id"] = prepend_to_method(
                details.methods["package_id"], "self.cpp_info.bindirs = []\nself.cpp_info.libdirs = []"
            )
        if "package_id" not in details.methods:
            details.methods["package_id"] = indent("def package_id(self):\n    self.info.clear()\n", "    ")
        else:
            details.methods["package_id"] = details.methods["package_id"].replace(
                "self.info.header_only()", "self.info.clear()"
            )
    else:
        if "package_type" not in details.attrs:
            details.attrs["package_type"] = "library"
        if "options" not in details.attrs:
            details.attrs["options"] = {}
            details.attrs["default_options"] = {}
        if "shared" not in details.attrs["options"]:
            details.attrs["options"]["shared"] = [True, False]
            details.attrs["default_options"]["shared"] = False
        if "fPIC" not in details.attrs["options"]:
            details.attrs["options"]["fPIC"] = [True, False]
            details.attrs["default_options"]["fPIC"] = True
    details.attrs["settings"] = ("os", "arch", "compiler", "build_type")
    details.attrs["url"] = "https://github.com/conan-io/conan-center-index"

    def reorder_opts(opts):
        new_opts = {}
        if "shared" in opts:
            new_opts["shared"] = opts["shared"]
            del opts["shared"]
        if "fPIC" in opts:
            new_opts["fPIC"] = opts["fPIC"]
            del opts["fPIC"]
        new_opts.update(opts)
        return new_opts

    if "options" in details.attrs:
        details.attrs["options"] = reorder_opts(details.attrs["options"])
        details.attrs["default_options"] = reorder_opts(details.attrs["default_options"])

    result = io.StringIO()

    result.write(details.head)
    result.write(f"class {details.class_name}(ConanFile):\n")
    for attr, is_required in attr_order:
        if attr in details.attrs:
            value = details.attrs[attr]
            # Add a comma for formatting with black
            src = re.sub(r"}$", ",}", repr(value))
            result.write(f"    {attr} = {src}\n")
        elif is_required:
            warnings.warn(f"Missing required attribute '{attr}' in {rel_conanfile_path}")
    result.write("\n")
    for attr, value in details.attrs.items():
        if attr in expected_attrs:
            continue
        if attr in disallowed_attrs:
            warnings.warn(f"Disallowed attribute '{attr} = {value:r}' in {rel_conanfile_path}")
            continue

    methods = details.props
    methods.update(details.methods)
    methods_order = [
        ("_min_cppstd", False),
        ("_compilers_minimum_version", False),
        ("_settings_build", False),
        ("export", False),
        ("export_sources", False),
        ("config_options", not is_header_only),
        ("configure", not is_header_only),
        ("layout", True),
        ("requirements", False),
        ("package_id", is_header_only),
        ("validate", False),
        ("validate_build", False),
        ("build_requirements", False),
        ("system_requirements", False),
        ("source", True),
        ("generate", not is_header_only),
        ("_patch_sources", False),
        ("build", not is_header_only),
        ("test", False),
        ("package", True),
        ("package_info", True),
    ]
    expected_methods = {method for method, is_required in methods_order}

    if "layout" not in methods:
        if details.build_system == "CMake":
            methods["layout"] = indent(
                'def layout(self):\n    cmake_layout(self, src_folder="src")\n', "    "
            )
        else:
            methods["layout"] = indent(
                'def layout(self):\n    basic_layout(self, src_folder="src")\n', "    "
            )

    result.write("\n")
    for method, body in methods.items():
        if method not in expected_methods:
            warnings.warn(f"Unexpected method '{method}' in {rel_conanfile_path}")
            result.write(body)
            result.write("\n")

    for method, is_required in methods_order:
        if method in methods:
            result.write(methods[method])
            result.write("\n")
        elif is_required:
            warnings.warn(f"Missing required method '{method}' in {rel_conanfile_path}")
            result.write(indent(f"def {method}(self):\n    # TODO: fill in {method}()\n    pass\n", "    "))

    processed_source = result.getvalue()
    processed_source = black.format_str(processed_source, mode=black.FileMode())

    if write:
        conanfile_path.write_text(processed_source)
    else:
        print(processed_source, end="")


if __name__ == "__main__":
    conanfile_path = sys.argv[1]
    tidy_conanfile(conanfile_path, write=True)
