import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class Sqlite3Conan(ConanFile):
    name = "sqlite3"
    description = "Self-contained, serverless, in-process SQL database engine."
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.sqlite.org"
    topics = ("sqlite", "database", "sql", "serverless")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_executable": [True, False],
        "threadsafe": [0, 1, 2],
        "enable_column_metadata": [True, False],
        "enable_dbstat_vtab": [True, False],
        "enable_explain_comments": [True, False],
        "enable_fts3": [True, False],
        "enable_fts3_parenthesis": [True, False],
        "enable_fts4": [True, False],
        "enable_fts5": [True, False],
        "enable_icu": [True, False],
        "enable_json1": [True, False],
        "enable_memsys5": [True, False],
        "enable_soundex": [True, False],
        "enable_preupdate_hook": [True, False],
        "enable_rtree": [True, False],
        "use_alloca": [True, False],
        "use_uri": [True, False],
        "omit_load_extension": [True, False],
        "omit_deprecated": [True, False],
        "enable_math_functions": [True, False],
        "enable_unlock_notify": [True, False],
        "enable_default_secure_delete": [True, False],
        "disable_gethostuuid": [True, False],
        "max_column": [None, "ANY"],
        "max_variable_number": [None, "ANY"],
        "max_blob_size": [None, "ANY"],
        "enable_default_vfs": [True, False],
        "enable_dbpage_vtab": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_executable": True,
        "threadsafe": 1,
        "enable_column_metadata": True,
        "enable_dbstat_vtab": False,
        "enable_explain_comments": False,
        "enable_fts3": False,
        "enable_fts3_parenthesis": False,
        "enable_fts4": False,
        "enable_fts5": False,
        "enable_icu": False,
        "enable_json1": False,
        "enable_memsys5": False,
        "enable_soundex": False,
        "enable_preupdate_hook": False,
        "enable_rtree": True,
        "use_alloca": False,
        "use_uri": False,
        "omit_load_extension": False,
        "omit_deprecated": False,
        "enable_math_functions": True,
        "enable_unlock_notify": True,
        "enable_default_secure_delete": False,
        "disable_gethostuuid": False,
        "max_column": None,             # Uses default value from source
        "max_variable_number": None,    # Uses default value from source
        "max_blob_size": None,          # Uses default value from source
        "enable_default_vfs": True,
        "enable_dbpage_vtab": False,
    }
    options_description = {
        ## Options from https://sqlite.org/compile.html
        "build_executable": "Build sqlite command line utility for accessing SQLite databases",
        "threadsafe": ("Whether or not code is included in SQLite to enable it to operate safely in a multithreaded environment. "
                       " The default is SQLITE_THREADSAFE=1 which is safe for use in a multithreaded environment."
                       " When compiled with SQLITE_THREADSAFE=0 all mutexing code is omitted and it is unsafe to use SQLite in a multithreaded program."
                       " When compiled with SQLITE_THREADSAFE=2, SQLite can be used in a multithreaded program so long as no two threads attempt"
                       " to use the same database connection (or any prepared statements derived from that database connection) at the same time."),
        "enable_column_metadata": "Enable additional APIs that provide convenient access to meta-data about tables and queries",
        "enable_dbstat_vtab": "Enable the DBSTAT virtual table",
        "enable_explain_comments": "Enable SQLite to insert comment text into the output of EXPLAIN",
        "enable_fts3": "Enable version 3 of the full-text search engine",
        "enable_fts3_parenthesis": ("Kodifies the query pattern parser in FTS3 such that it supports operators AND and NOT "
                                    "(in addition to the usual OR and NEAR) and also allows query expressions to contain nested parenthesis"),
        "enable_fts4": "Enable version 3 and 4 of the full-text search engine",
        "enable_fts5": "Enable version 5 of the full-text search engine",
        "enable_icu": "Enable support for the ICU extension",
        "enable_json1": "Enable JSON SQL functions",
        "enable_memsys5": "Enable MEMSYS5 memory allocator",
        "enable_soundex": "Enable the soundex() SQL function",
        "enable_preupdate_hook": "Enables APIs to handle any change to a rowid table",
        "enable_rtree": "Enable support for the R*Tree index extension",
        "use_alloca": "The alloca() memory allocator will be used in a few situations where it is appropriate.",
        "use_uri": "This option causes the URI filename process logic to be enabled by default.",
        "omit_load_extension": "Omits the entire extension loading mechanism from SQLite",
        "omit_deprecated": "Omits deprecated interfaces and features",
        "enable_math_functions": "Enables the built-in SQL math functions",
        "enable_unlock_notify": "Enable support for the unlock notify API",
        "enable_default_secure_delete": "Turns on secure deletion by default",
        "disable_gethostuuid": "Disable function gethostuuid",
        "max_column": "The maximum number of columns in a table / index / view",
        "max_variable_number": "The maximum value of a ?nnn wildcard that the parser will accept",
        "max_blob_size": "Set the maximum number of bytes in a string or BLOB",
        "enable_default_vfs": "Enable default VFS implementation",
        "enable_dbpage_vtab": ("The SQLITE_DBPAGE extension implements an eponymous-only virtual table that provides "
                               "direct access to the underlying database file by interacting with the pager. "
                               "SQLITE_DBPAGE is capable of both reading and writing any page of the database. "
                               "Because interaction is through the pager layer, all changes are transactional."),
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def config_options(self):
        if Version(self.version) < "3.35.0":
            del self.options.enable_math_functions

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.enable_icu:
            self.requires("icu/[*]")

    def validate(self):
        if self.options.build_executable:
            if not self.options.enable_default_vfs:
                # Need to provide custom VFS code: https://www.sqlite.org/custombuild.html
                raise ConanInvalidConfiguration("build_executable=True cannot be combined with enable_default_vfs=False")
            if self.options.omit_load_extension:
                raise ConanInvalidConfiguration("build_executable=True requires omit_load_extension=True")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        download(self, **self.conan_data["icon"], filename="art/sqlite370.ico")
        replace_in_file(self, "sqlite3.rc", r'..\\art\\', r'art\\')

    @property
    def _public_defines(self):
        defines = {}
        defines["SQLITE_THREADSAFE"] = self.options.threadsafe
        if self.settings.build_type == "Debug":
            defines["SQLITE_DEBUG"] = 1
            defines["SQLITE_ENABLE_SELECTTRACE"] = 1
            defines["SQLITE_ENABLE_WHERETRACE"] = 1
        if self.options.enable_json1:
            defines["SQLITE_ENABLE_JSON1"] = 1
        if self.options.enable_column_metadata:
            defines["SQLITE_ENABLE_COLUMN_METADATA"] = 1
        if self.options.enable_dbstat_vtab:
            defines["SQLITE_ENABLE_DBSTAT_VTAB"] = 1
        if self.options.enable_explain_comments:
            defines["SQLITE_ENABLE_EXPLAIN_COMMENTS"] = 1
        if self.options.enable_fts3:
            defines["SQLITE_ENABLE_FTS3"] = 1
        if self.options.enable_fts3_parenthesis:
            defines["SQLITE_ENABLE_FTS3_PARENTHESIS"] = 1
        if self.options.enable_fts4:
            defines["SQLITE_ENABLE_FTS4"] = 1
        if self.options.enable_fts5:
            defines["SQLITE_ENABLE_FTS5"] = 1
        if self.options.enable_icu:
            defines["SQLITE_ENABLE_ICU"] = 1
        if self.options.enable_preupdate_hook:
            defines["SQLITE_ENABLE_PREUPDATE_HOOK"] = 1
        if self.options.enable_rtree:
            defines["SQLITE_ENABLE_RTREE"] = 1
        if self.options.enable_unlock_notify:
            defines["SQLITE_ENABLE_UNLOCK_NOTIFY"] = 1
        if self.options.enable_default_secure_delete:
            defines["SQLITE_SECURE_DELETE"] = 1
        if self.options.enable_memsys5:
            defines["SQLITE_ENABLE_MEMSYS5"] = 1
        if self.options.enable_soundex:
            defines["SQLITE_SOUNDEX"] = 1
        if self.options.use_alloca:
            defines["SQLITE_USE_ALLOCA"] = 1
        if self.options.use_uri:
            defines["SQLITE_USE_URI"] = 1
        if self.options.omit_load_extension:
            defines["SQLITE_OMIT_LOAD_EXTENSION"] = 1
        if self.options.omit_deprecated:
            defines["SQLITE_OMIT_DEPRECATED"] = 1
        if self.options.get_safe("enable_math_functions"):
            defines["SQLITE_ENABLE_MATH_FUNCTIONS"] = 1
        if self.options.max_column:
            defines["SQLITE_MAX_COLUMN"] = self.options.max_column
        if self.options.max_variable_number:
            defines["SQLITE_MAX_VARIABLE_NUMBER"] = self.options.max_variable_number
        if self.options.max_blob_size:
            defines["SQLITE_MAX_LENGTH"] = self.options.max_blob_size
        if not self.options.enable_default_vfs:
            defines["SQLITE_OS_OTHER"] = 1
        if self.options.enable_dbpage_vtab:
            defines["SQLITE_ENABLE_DBPAGE_VTAB"] = 1
        return defines

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SQLITE3_VERSION"] = self.version
        tc.variables["SQLITE3_BUILD_EXECUTABLE"] = self.options.build_executable
        tc.variables["THREADSAFE"] = self.options.threadsafe
        tc.variables["ENABLE_FTS5"] = self.options.enable_fts5
        tc.variables["ENABLE_ICU"] = self.options.enable_icu
        tc.variables["OMIT_LOAD_EXTENSION"] = self.options.omit_load_extension
        tc.variables["ENABLE_MATH_FUNCTIONS"] = self.options.get_safe("enable_math_functions", False)

        private_defines = {}
        private_defines["HAVE_FDATASYNC"] = 1
        private_defines["HAVE_GMTIME_R"] = 1
        if self.settings.os != "Windows":
            private_defines["HAVE_LOCALTIME_R"] = 1
        if not (self.settings.os in ["Windows", "Android"] or is_apple_os(self)):
            private_defines["HAVE_POSIX_FALLOCATE"] = 1
        private_defines["HAVE_STRERROR_R"] = 1
        private_defines["HAVE_USLEEP"] = 1
        if self.options.disable_gethostuuid:
            private_defines["HAVE_GETHOSTUUID"] = 1

        tc.preprocessor_definitions.update(self._public_defines)
        tc.preprocessor_definitions.update(private_defines)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _extract_license(self):
        header = load(self, os.path.join(self.source_folder, "sqlite3.h"))
        license_content = header[3:header.find("***", 1)]
        return license_content

    def package(self):
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), self._extract_license())
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "SQLite3")
        self.cpp_info.set_property("cmake_target_name", "SQLite::SQLite3")
        self.cpp_info.set_property("pkg_config_name", "sqlite3")

        self.cpp_info.libs = ["sqlite3"]
        if self.options.enable_icu:
            self.cpp_info.requires = ["icu::icu"]
        if self.options.omit_load_extension:
            self.cpp_info.defines.append("SQLITE_OMIT_LOAD_EXTENSION")
        if self.settings.os in ["Linux", "FreeBSD"]:
            if self.options.threadsafe:
                self.cpp_info.system_libs.append("pthread")
            if not self.options.omit_load_extension:
                self.cpp_info.system_libs.append("dl")
            if self.options.enable_fts5 or self.options.get_safe("enable_math_functions"):
                self.cpp_info.system_libs.append("m")
        elif self.settings.os == "Windows":
            if self.options.shared:
                self.cpp_info.defines.append("SQLITE_API=__declspec(dllimport)")

        self.cpp_info.defines.extend([f"{k}={v}" for k, v in self._public_defines.items()])
