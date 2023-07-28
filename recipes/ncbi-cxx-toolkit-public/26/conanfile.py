# TODO: verify the Conan v2 migration

import os

from conan import ConanFile, conan_version
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.android import android_abi
from conan.tools.apple import XCRun, fix_apple_shared_install_name, is_apple_os, to_apple_arch
from conan.tools.build import build_jobs, can_run, check_min_cppstd, cross_building, default_cppstd, stdcpp_library, valid_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import Environment, VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import apply_conandata_patches, chdir, collect_libs, copy, download, export_conandata_patches, get, load, mkdir, patch, patches, rename, replace_in_file, rm, rmdir, save, symlinks, unzip
from conan.tools.gnu import Autotools, AutotoolsDeps, AutotoolsToolchain, PkgConfig, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import MSBuild, MSBuildDeps, MSBuildToolchain, NMakeDeps, NMakeToolchain, VCVars, check_min_vs, is_msvc, is_msvc_static_runtime, msvc_runtime_flag, unix_path, unix_path_package_info_legacy, vs_layout
from conan.tools.scm import Version
from conan.tools.system import package_manager
import os

required_conan_version = ">=1.53.0"


class NcbiCxxToolkit(ConanFile):
    name = "ncbi-cxx-toolkit-public"
    description = (
        "NCBI C++ Toolkit -- a cross-platform application framework and "
        "a collection of libraries for working with biological data."
    )
    license = "Public-domain"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://ncbi.github.io/cxx-toolkit"
    topics = ("ncbi", "biotechnology", "bioinformatics", "genbank", "gene", "genome",
              "genetic", "sequence", "alignment", "blast", "biological", "toolkit", "c++")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_projects": ["ANY"],
        "with_targets": ["ANY"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_projects": "",
        "with_targets": "",
    }
    NCBI_to_Conan_requires = {
        "BerkeleyDB":   "libdb/5.3.28",
        "BZ2":          "bzip2/1.0.8",
        "CASSANDRA":    "cassandra-cpp-driver/2.15.3",
        "GIF":          "giflib/5.2.1",
        "JPEG":         "libjpeg/9r",
        "LMDB":         "lmdb/0.9.29",
        "LZO":          "lzo/2.10",
        "MySQL":        "libmysqlclient/8.0.31",
        "NGHTTP2":      "libnghttp2/1.55.1",
        "PCRE":         "pcre/8.45",
        "PNG":          "libpng/1.6.40",
        "SQLITE3":      "sqlite3/3.37.2",
        "TIFF":         "libtiff/4.3.0",
        "XML":          "libxml2/2.9.12",
        "XSLT":         "libxslt/1.1.34",
        "UV":           "libuv/1.45.0",
        "Z":            "zlib/1.2.11",
        "OpenSSL":      "openssl/1.1.1l",
        "ZSTD":         "zstd/1.5.2"
    }

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        return {
            "Visual Studio": "16",
            "msvc": "192",
            "gcc": "7",
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
        NCBIreqs = self._get_RequiresMapKeys()
        for req in NCBIreqs:
            pkg = self._translate_ReqKey(req)
            if pkg is not None:
                self.requires(pkg)

    def _get_RequiresMapKeys(self):
        return self.NCBI_to_Conan_requires.keys()

    def _translate_ReqKey(self, key):
        if key in self.NCBI_to_Conan_requires.keys():
            if key == "BerkeleyDB" and self.settings.os == "Windows":
                return None
            if key == "CASSANDRA" and (self.settings.os == "Windows" or self.settings.os == "Macos"):
                return None
            if key == "NGHTTP2" and self.settings.os == "Windows":
                return None
            return self.NCBI_to_Conan_requires[key]
        return None

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD", "Macos", "Windows"]:
            raise ConanInvalidConfiguration("This operating system is not supported")
        if hasattr(self, "settings_build") and cross_building(self, skip_x64_x86=True):
            raise ConanInvalidConfiguration("Cross compilation is not supported")
        if self.options.shared and is_msvc_static_runtime(self):
            raise ConanInvalidConfiguration(f"Static MSVC runtime (MT) with shared=True is not supported")
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["NCBI_PTBCFG_PACKAGING"] = "TRUE"
        if self.options.with_projects != "":
            tc.variables["NCBI_PTBCFG_PROJECT_LIST"] = self.options.with_projects
        if self.options.with_targets != "":
            tc.variables["NCBI_PTBCFG_PROJECT_TARGETS"] = self.options.with_targets
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        # Visual Studio sometimes runs "out of heap space"
        if is_msvc(self):
            cmake.parallel = False
        cmake.build()

    def package(self):
        copy(self, "LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=os.path.join(self.source_folder, "doc", "public"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.components["ORIGLIBS"].system_libs = ["ws2_32", "dbghelp"]
            self.cpp_info.components["NETWORKLIBS"].system_libs = []
        elif self.settings.os == "Linux":
            self.cpp_info.components["ORIGLIBS"].system_libs = ["dl", "rt", "m", "pthread"]
            self.cpp_info.components["NETWORKLIBS"].system_libs = ["resolv"]
        elif self.settings.os == "Macos":
            self.cpp_info.components["ORIGLIBS"].system_libs = ["dl", "c", "m", "pthread"]
            self.cpp_info.components["NETWORKLIBS"].system_libs = ["resolv"]

        NCBIreqs = self._get_RequiresMapKeys()
        for req in NCBIreqs:
            pkg = self._translate_ReqKey(req)
            if pkg is not None:
                pkg = pkg[: pkg.find("/")]
                ref = pkg + "::" + pkg
                self.cpp_info.components[req].requires = [ref]
                self.cpp_info.components["ORIGLIBS"].requires.append(ref)
            else:
                self.cpp_info.components[req].libs = []

        allexports = {}
        impfile = os.path.join(self.package_folder, "res", "ncbi-cpp-toolkit.imports")
        if os.path.isfile(impfile):
            allexports = set(open(impfile).read().split())

        def _add_lib_component(name, requires):
            if name in allexports:
                self.cpp_info.components[name].libs = [name]
                self.cpp_info.components[name].requires = requires

        # ============================================================================
        if self.settings.os == "Windows" and self.options.shared:
            # 12--------------------------------------------------------------------------
            _add_lib_component("blast_app_util", ["ncbi_blastinput"])
            _add_lib_component("vdb2blast", ["ncbi_blastinput", "VDB"])
            _add_lib_component("xbma_refiner_gui", ["ncbi_algo_structure", "wx_tools", "wxWidgets"])
            _add_lib_component("xngalign", ["ncbi_blastinput", "xmergetree"])
            # 11--------------------------------------------------------------------------
            _add_lib_component("blast_unit_test_util", ["ncbi_algo", "test_boost", "Boost"])
            _add_lib_component("igblast", ["ncbi_algo"])
            _add_lib_component("ncbi_algo_ms", ["ncbi_algo"])
            _add_lib_component("ncbi_algo_structure", ["ncbi_mmdb", "ncbi_algo"])
            _add_lib_component("ncbi_blastinput", ["ncbi_xloader_blastdb_rmt", "ncbi_algo"])
            _add_lib_component("xaligncleanup", ["ncbi_algo"])
            # 10--------------------------------------------------------------------------
            _add_lib_component("ncbi_algo", ["sqlitewrapp", "ncbi_align_format", "utrtprof"])
            _add_lib_component("xalntool", ["ncbi_align_format"])
            # 9--------------------------------------------------------------------------
            # _add_lib_component("data_loaders_util", ["ncbi_xdbapi_ftds", "ncbi_xloader_asn_cache", "ncbi_xloader_blastdb", "ncbi_xloader_genbank", "ncbi_xloader_lds2", "ncbi_xreader_pubseqos", "ncbi_xreader_pubseqos2", "ncbi_xloader_csra", "ncbi_xloader_wgs"])
            _add_lib_component("data_loaders_util", ["ncbi_xdbapi_ftds", "ncbi_xloader_asn_cache", "ncbi_xloader_blastdb", "ncbi_xloader_genbank", "ncbi_xloader_lds2", "ncbi_xreader_pubseqos", "ncbi_xreader_pubseqos2"])
            _add_lib_component("hgvs", ["ncbi_xloader_genbank", "Boost"])
            _add_lib_component("ncbi_align_format", ["ncbi_xloader_genbank", "ncbi_web"])
            _add_lib_component("ncbi_xobjsimple", ["ncbi_xloader_genbank"])
            _add_lib_component("xflatfile", ["ncbi_xdbapi_ftds", "ncbi_xloader_genbank"])
            # 8--------------------------------------------------------------------------
            _add_lib_component("ncbi_xloader_genbank", ["ncbi_xreader_cache", "ncbi_xreader_id1", "ncbi_xreader_id2", "psg_client"])
            # 7--------------------------------------------------------------------------
            _add_lib_component("blast_sra_input", ["sraread", "VDB"])
            _add_lib_component("ncbi_xloader_blastdb_rmt", ["ncbi_xloader_blastdb"])
            _add_lib_component("ncbi_xloader_cdd", ["cdd_access"])
            _add_lib_component("ncbi_xloader_csra", ["sraread", "VDB"])
            _add_lib_component("ncbi_xloader_lds2", ["ncbi_lds2"])
            _add_lib_component("ncbi_xloader_snp", ["sraread", "dbsnp_ptis", "VDB", "GRPC"])
            _add_lib_component("ncbi_xloader_sra", ["sraread", "VDB"])
            _add_lib_component("ncbi_xloader_vdbgraph", ["sraread", "VDB"])
            _add_lib_component("ncbi_xloader_wgs", ["sraread", "VDB"])
            _add_lib_component("ncbi_xreader_cache", ["ncbi_xreader"])
            _add_lib_component("ncbi_xreader_gicache", ["ncbi_xreader", "LMDB"])
            _add_lib_component("ncbi_xreader_id1", ["ncbi_xreader"])
            _add_lib_component("ncbi_xreader_id2", ["ncbi_xreader"])
            _add_lib_component("ncbi_xreader_pubseqos", ["ncbi_dbapi_driver", "ncbi_xreader"])
            _add_lib_component("ncbi_xreader_pubseqos2", ["ncbi_dbapi_driver", "ncbi_xreader", "eMyNCBI_result"])
            # 6--------------------------------------------------------------------------
            _add_lib_component("cdd_access", ["ncbi_seqext"])
            _add_lib_component("eMyNCBI_result", ["ncbi_seqext"])
            _add_lib_component("fix_pub", ["eutils_client", "ncbi_seqext"])
            _add_lib_component("gene_info_writer", ["ncbi_seqext"])
            _add_lib_component("ncbi_lds2", ["ncbi_seqext", "sqlitewrapp", "SQLITE3"])
            _add_lib_component("ncbi_validator", ["ncbi_seqext"])
            _add_lib_component("ncbi_xdiscrepancy", ["macro", "ncbi_seqext"])
            _add_lib_component("ncbi_xloader_asn_cache", ["asn_cache", "ncbi_seqext"])
            _add_lib_component("ncbi_xloader_bam", ["bamread", "ncbi_seqext", "VDB"])
            _add_lib_component("ncbi_xloader_blastdb", ["ncbi_seqext"])
            _add_lib_component("ncbi_xloader_patcher", ["ncbi_seqext"])
            _add_lib_component("ncbi_xreader", ["ncbi_seqext"])
            _add_lib_component("psg_client", ["ncbi_seqext", "xxconnect2", "UV", "NGHTTP2"])
            _add_lib_component("sraread", ["ncbi_seqext", "VDB"])
            _add_lib_component("xalgoblastdbindex_search", ["ncbi_seqext"])
            _add_lib_component("xbiosample_util", ["xmlwrapp", "ncbi_seqext", "macro"])
            _add_lib_component("xmergetree", ["ncbi_seqext"])
            # 5--------------------------------------------------------------------------
            _add_lib_component("dbsnp_tooltip_service", ["ncbi_trackmgr"])
            _add_lib_component("ncbi_seqext", ["ncbi_misc", "ncbi_eutils", "ncbi_trackmgr", "LMDB"])
            _add_lib_component("pcassay2", ["ncbi_misc"])
            _add_lib_component("searchbyrsid", ["ncbi_trackmgr"])
            _add_lib_component("trackmgrgridcli", ["ncbi_trackmgr", "LZO"])
            _add_lib_component("xcddalignview", ["ncbi_mmdb"])
            # 4--------------------------------------------------------------------------
            _add_lib_component("asn_cache", ["ncbi_bdb", "ncbi_seq"])
            _add_lib_component("bamread", ["ncbi_seq", "VDB"])
            _add_lib_component("dbsnp_ptis", ["ncbi_seq", "grpc_integration", "PROTOBUF", "GRPC", "Z"])
            _add_lib_component("eutils_client", ["ncbi_seq", "xmlwrapp"])
            _add_lib_component("gencoll_client", ["ncbi_seq", "sqlitewrapp", "SQLITE3"])
            _add_lib_component("homologene", ["ncbi_seq"])
            _add_lib_component("local_taxon", ["ncbi_seq", "sqlitewrapp", "SQLITE3"])
            _add_lib_component("macro", ["ncbi_seq"])
            _add_lib_component("ncbi_misc", ["ncbi_seq"])
            _add_lib_component("ncbi_mmdb", ["ncbi_seq"])
            _add_lib_component("ncbi_trackmgr", ["ncbi_seq"])
            _add_lib_component("seqalign_util", ["ncbi_seq", "test_boost", "Boost"])
            # 3--------------------------------------------------------------------------
            # _add_lib_component("dbapi_sample_base", ["ncbi_xdbapi_ftds", "ncbi_xdbapi_ftds100", "ncbi_xdbapi_ctlib", "ncbi_xdbapi_odbc", "Sybase", "ODBC"])
            _add_lib_component("dbapi_sample_base", ["ncbi_xdbapi_ftds", "ncbi_xdbapi_ftds100"])
            _add_lib_component("ncbi_seq", ["ncbi_pub"])
            _add_lib_component("odbc_ftds100", ["tds_ftds100", "ncbi_xdbapi_odbc", "ODBC"])
            _add_lib_component("python_ncbi_dbapi", ["ncbi_dbapi", "PYTHON"])
            _add_lib_component("sdbapi", ["ncbi_dbapi", "dbapi_util_blobstore", "ncbi_xdbapi_ftds", "ncbi_xdbapi_ftds100"])
            # 2--------------------------------------------------------------------------
            _add_lib_component("ctransition_nlmzip", ["ctransition"])
            _add_lib_component("dbapi_util_blobstore", ["ncbi_dbapi_driver"])
            _add_lib_component("hydra_client", ["xmlwrapp"])
            _add_lib_component("ncbi_dbapi", ["ncbi_dbapi_driver"])
            _add_lib_component("ncbi_pub", ["ncbi_general"])
            _add_lib_component("ncbi_xcache_bdb", ["ncbi_bdb", "BerkeleyDB"])
            _add_lib_component("ncbi_xdbapi_ctlib", ["ncbi_dbapi_driver", "Sybase"])
            _add_lib_component("ncbi_xdbapi_ftds", ["ncbi_dbapi_driver", "ct_ftds100"])
            _add_lib_component("ncbi_xdbapi_ftds100", ["ct_ftds100", "ncbi_dbapi_driver"])
            _add_lib_component("ncbi_xdbapi_mysql", ["ncbi_dbapi_driver"])
            _add_lib_component("ncbi_xdbapi_odbc", ["ncbi_dbapi_driver", "ODBC", "SQLServer"])
            _add_lib_component("ncbi_xgrid2cgi", ["ncbi_web"])
            _add_lib_component("netstorage", ["ncbi_xcache_netcache"])
            _add_lib_component("pmcidconv_client", ["xmlwrapp"])
            _add_lib_component("psg_cache", ["psg_protobuf", "psg_cassandra", "LMDB", "PROTOBUF"])
            _add_lib_component("sample_asn", ["ncbi_general"])
            _add_lib_component("xasn", ["ncbi_web", "NCBI_C"])
            _add_lib_component("xfcgi_mt", ["ncbi_web"])
            _add_lib_component("xmlreaders", ["xmlwrapp"])
            _add_lib_component("xsoap_server", ["ncbi_web", "xsoap"])
            # 1--------------------------------------------------------------------------
            _add_lib_component("asn_sample_lib", ["ncbi_core"])
            _add_lib_component("basic_sample_lib", ["ncbi_core"])
            _add_lib_component("ct_ftds100", ["tds_ftds100"])
            _add_lib_component("ctransition", ["ncbi_core"])
            _add_lib_component("dtd_sample_lib", ["ncbi_core"])
            _add_lib_component("grpc_integration", ["ncbi_core", "GRPC", "Z"])
            _add_lib_component("gumbelparams", ["ncbi_core"])
            _add_lib_component("jaeger_tracer", ["ncbi_core"])
            _add_lib_component("jsd_sample_lib", ["ncbi_core"])
            _add_lib_component("msbuild_dataobj", ["ncbi_core"])
            _add_lib_component("ncbi_bdb", ["ncbi_core", "BerkeleyDB"])
            _add_lib_component("ncbi_dbapi_driver", ["ncbi_core"])
            _add_lib_component("ncbi_eutils", ["ncbi_core"])
            _add_lib_component("ncbi_general", ["ncbi_core"])
            _add_lib_component("ncbi_image", ["ncbi_core", "Z", "JPEG", "PNG", "GIF", "TIFF"])
            _add_lib_component("ncbi_web", ["ncbi_core"])
            _add_lib_component("ncbi_xblobstorage_netcache", ["ncbi_core"])
            _add_lib_component("ncbi_xcache_netcache", ["ncbi_core"])
            _add_lib_component("psg_cassandra", ["ncbi_core"])
            _add_lib_component("psg_diag", ["ncbi_core"])
            _add_lib_component("soap_dataobj", ["ncbi_core"])
            _add_lib_component("sqlitewrapp", ["ncbi_core", "SQLITE3"])
            _add_lib_component("sybdb_ftds100", ["tds_ftds100"])
            _add_lib_component("test_boost", ["ncbi_core", "Boost"])
            _add_lib_component("test_mt", ["ncbi_core"])
            _add_lib_component("utrtprof", ["ncbi_core"])
            _add_lib_component("varrep", ["ncbi_core"])
            _add_lib_component("wx_tools", ["ncbi_core", "wxWidgets"])
            _add_lib_component("xalgovmerge", ["ncbi_core"])
            _add_lib_component("xcser", ["ncbi_core"])
            _add_lib_component("xctools", ["ncbi_core", "NCBI_C"])
            _add_lib_component("xfcgi", ["ncbi_core", "FASTCGI"])
            _add_lib_component("xmlwrapp", ["ncbi_core", "XML", "XSLT"])
            _add_lib_component("xpbacktest", ["ncbi_core"])
            _add_lib_component("xregexp_template_tester", ["ncbi_core", "PCRE"])
            _add_lib_component("xsd_sample_lib", ["ncbi_core"])
            _add_lib_component("xsoap", ["ncbi_core"])
            _add_lib_component("xxconnect2", ["ncbi_core", "UV", "NGHTTP2"])
            # 0--------------------------------------------------------------------------
            _add_lib_component("clog", ["ORIGLIBS"])
            _add_lib_component("edit_imgt_file", ["ORIGLIBS"])
            _add_lib_component("lapackwrapp", ["ORIGLIBS"])
            _add_lib_component("ncbi_core", ["PCRE", "Z", "BZ2", "LZO", "ORIGLIBS"])
            _add_lib_component("psg_protobuf", ["PROTOBUF", "ORIGLIBS"])
            _add_lib_component("task_server", ["Boost", "ORIGLIBS"])
            _add_lib_component("tds_ftds100", ["ORIGLIBS"])
            _add_lib_component("test_dll", ["ORIGLIBS"])
        else:
            # ============================================================================
            # 18--------------------------------------------------------------------------
            _add_lib_component("xaligncleanup", ["xalgoalignsplign", "prosplign"])
            _add_lib_component("xbma_refiner_gui", ["xbma_refiner", "wx_tools", "wxWidgets"])
            # 17--------------------------------------------------------------------------
            _add_lib_component("blast_app_util", ["blastdb", "xnetblast", "blastinput", "xblastformat"])
            _add_lib_component("prosplign", ["xalgoalignutil"])
            _add_lib_component("vdb2blast", ["xblast", "blastinput", "VDB"])
            _add_lib_component("xalgoalignsplign", ["xalgoalignnw", "xalgoalignutil"])
            _add_lib_component("xbma_refiner", ["xcd_utils", "xstruct_util", "cdd"])
            _add_lib_component("xngalign", ["blastinput", "xalgoalignnw", "xalgoalignutil", "xmergetree"])
            # 16--------------------------------------------------------------------------
            _add_lib_component("blastinput", ["seqset", "xnetblast", "align_format", "ncbi_xloader_blastdb_rmt", "xblast"])
            _add_lib_component("cobalt", ["xalgoalignnw", "xalgophytree", "xblast"])
            _add_lib_component("igblast", ["xalnmgr", "xblast"])
            _add_lib_component("proteinkmer", ["xblast"])
            _add_lib_component("xalgoalignutil", ["xalgoseq", "xblast", "xqueryparse"])
            _add_lib_component("xalgocontig_assembly", ["xalgoalignnw", "xalnmgr", "xblast"])
            _add_lib_component("xblastformat", ["blastxml", "blastxml2", "align_format", "xblast", "xformat"])
            _add_lib_component("xcd_utils", ["blast_services", "entrez2cli", "id1cli", "ncbimime", "taxon1", "xblast", "xregexp"])
            _add_lib_component("xstruct_util", ["xblast", "xstruct_dp"])
            # 15--------------------------------------------------------------------------
            _add_lib_component("phytree_format", ["align_format", "xalgophytree", "blastdb", "scoremat"])
            _add_lib_component("xalgoseqqa", ["entrez2cli", "seqtest", "xalgognomon"])
            _add_lib_component("xalntool", ["align_format"])
            _add_lib_component("xblast", ["xalgoblastdbindex", "xalgodustmask", "xalgowinmask", "xnetblastcli", "seq", "blastdb", "utrtprof"])
            _add_lib_component("xobjwrite", ["variation_utils", "xformat", "xobjread"])
            _add_lib_component("xvalidate", ["taxon1", "valerr", "xformat", "xobjedit", "submit", "taxon3"])
            # 14--------------------------------------------------------------------------
            _add_lib_component("align_format", ["blast_services", "gene_info", "ncbi_xloader_genbank", "seqdb", "taxon1", "xalnmgr", "xcgi", "xhtml", "xobjread"])
            _add_lib_component("blast_unit_test_util", ["blastdb", "xnetblast", "blast", "ncbi_xloader_genbank", "test_boost", "xobjutil", "Boost"])
            # _add_lib_component("data_loaders_util", ["ncbi_xdbapi_ftds", "ncbi_xloader_asn_cache", "ncbi_xloader_blastdb", "ncbi_xloader_genbank", "ncbi_xloader_lds2", "ncbi_xreader_pubseqos", "ncbi_xreader_pubseqos2", "ncbi_xloader_csra", "ncbi_xloader_wgs"])
            _add_lib_component("data_loaders_util", ["ncbi_xdbapi_ftds", "ncbi_xloader_asn_cache", "ncbi_xloader_blastdb", "ncbi_xloader_genbank", "ncbi_xloader_lds2", "ncbi_xreader_pubseqos", "ncbi_xreader_pubseqos2"])
            _add_lib_component("hgvs", ["entrez2cli", "ncbi_xloader_genbank", "objcoords", "variation", "xobjread", "xobjutil", "xregexp", "seq", "Boost"])
            _add_lib_component("ncbi_xloader_blastdb_rmt", ["blast_services", "ncbi_xloader_blastdb"])
            _add_lib_component("xalgognomon", ["xalgoseq"])
            _add_lib_component("xalgowinmask", ["submit", "seqmasks_io"])
            _add_lib_component("xdiscrepancy", ["xcompress", "macro", "xcleanup", "xobjedit"])
            _add_lib_component("xflatfile", ["xcleanup", "xlogging", "ncbi_xdbapi_ftds", "taxon1", "ncbi_xloader_genbank"])
            _add_lib_component("xformat", ["gbseq", "mlacli", "xalnmgr", "xcleanup"])
            _add_lib_component("xobjsimple", ["ncbi_xloader_genbank", "seqset"])
            _add_lib_component("xprimer", ["gene_info", "ncbi_xloader_genbank", "xalgoalignnw", "xalnmgr"])
            # 13--------------------------------------------------------------------------
            _add_lib_component("blastdb_format", ["seqdb", "xobjutil", "seqset"])
            _add_lib_component("fix_pub", ["mlacli", "eutils_client", "xobjedit"])
            _add_lib_component("gene_info_writer", ["gene_info", "seqdb"])
            _add_lib_component("ncbi_xloader_bam", ["bamread", "xobjreadex", "seqset", "VDB"])
            _add_lib_component("ncbi_xloader_blastdb", ["seqdb", "seqset"])
            _add_lib_component("ncbi_xloader_genbank", ["libgeneral", "ncbi_xreader_cache", "ncbi_xreader_id1", "ncbi_xreader_id2", "psg_client"])
            _add_lib_component("seqmasks_io", ["seqdb", "xobjread", "xobjutil"])
            _add_lib_component("writedb", ["seqdb", "xobjread", "LMDB"])
            _add_lib_component("xalgoblastdbindex", ["blast", "seqdb", "xobjread", "xobjutil"])
            _add_lib_component("xalgophytree", ["biotree", "fastme", "xalnmgr"])
            _add_lib_component("xalgoseq", ["taxon1", "xalnmgr", "xregexp"])
            _add_lib_component("xbiosample_util", ["xmlwrapp", "xobjedit", "taxon3", "seqset", "macro", "valid"])
            _add_lib_component("xcleanup", ["xobjedit"])
            _add_lib_component("xomssa", ["blast", "omssa", "pepXML", "seqdb", "xcompress", "xconnect", "xregexp"])
            # 12--------------------------------------------------------------------------
            _add_lib_component("blast_services", ["xnetblastcli"])
            _add_lib_component("blast_sra_input", ["sraread", "blastdb", "VDB"])
            _add_lib_component("ncbi_xloader_cdd", ["cdd_access", "xcompress", "seq", "xobjmgr"])
            _add_lib_component("ncbi_xloader_csra", ["sraread", "seqset", "VDB"])
            _add_lib_component("ncbi_xloader_lds2", ["lds2", "xobjmgr", "seq"])
            _add_lib_component("ncbi_xloader_snp", ["sraread", "seqset", "seq", "dbsnp_ptis", "grpc_integration", "VDB", "GRPC"])
            _add_lib_component("ncbi_xloader_sra", ["sraread", "seqset", "VDB"])
            _add_lib_component("ncbi_xloader_vdbgraph", ["sraread", "seqset", "VDB"])
            _add_lib_component("ncbi_xloader_wgs", ["sraread", "seqset", "VDB"])
            _add_lib_component("ncbi_xreader_cache", ["ncbi_xreader"])
            _add_lib_component("ncbi_xreader_gicache", ["ncbi_xreader", "LMDB"])
            _add_lib_component("ncbi_xreader_id1", ["ncbi_xreader"])
            _add_lib_component("ncbi_xreader_id2", ["ncbi_xreader"])
            _add_lib_component("ncbi_xreader_pubseqos", ["dbapi_driver", "ncbi_xreader"])
            _add_lib_component("ncbi_xreader_pubseqos2", ["dbapi_driver", "ncbi_xreader", "eMyNCBI_result"])
            _add_lib_component("seqalign_util", ["blastdb", "seq", "test_boost", "Boost"])
            _add_lib_component("seqdb", ["blastdb", "xobjmgr", "LMDB"])
            _add_lib_component("variation_utils", ["variation", "xobjutil", "blastdb", "genome_collection"])
            _add_lib_component("xalnmgr", ["tables", "xobjutil", "seqset"])
            _add_lib_component("xcddalignview", ["seq", "ncbimime"])
            _add_lib_component("xobjedit", ["eutils", "esearch", "esummary", "mlacli", "taxon3", "valid", "xobjread", "xobjutil", "xlogging"])
            _add_lib_component("xobjimport", ["xobjutil"])
            _add_lib_component("xobjreadex", ["xobjread", "xobjutil", "seqset"])
            _add_lib_component("xunittestutil", ["xobjutil"])
            # 11--------------------------------------------------------------------------
            _add_lib_component("blastdb", ["xnetblast"])
            _add_lib_component("cdd_access", ["id2", "xconnect"])
            _add_lib_component("eMyNCBI_result", ["seqset", "id2"])
            _add_lib_component("id2_split", ["xcompress", "xobjmgr"])
            _add_lib_component("id2cli", ["id2", "xconnect"])
            _add_lib_component("lds2", ["xcompress", "xobjread", "sqlitewrapp", "SQLITE3"])
            _add_lib_component("ncbi_xloader_asn_cache", ["libgeneral", "asn_cache", "xobjmgr"])
            _add_lib_component("ncbi_xloader_patcher", ["xobjmgr"])
            _add_lib_component("ncbi_xreader", ["id1", "id2", "xcompress", "xconnect", "xobjmgr"])
            _add_lib_component("ncbimime", ["cdd"])
            _add_lib_component("psg_client", ["id2", "seqsplit", "xconnserv", "xxconnect2", "UV", "NGHTTP2"])
            _add_lib_component("snputil", ["variation", "xobjmgr", "seqset"])
            _add_lib_component("sraread", ["xobjmgr", "VDB"])
            _add_lib_component("uudutil", ["gbproj", "xcompress", "xconnserv"])
            _add_lib_component("xalgoalignnw", ["tables", "xobjmgr", "seq"])
            _add_lib_component("xalgoblastdbindex_search", ["seqset", "xobjmgr"])
            _add_lib_component("xalgodustmask", ["seqset", "xobjmgr"])
            _add_lib_component("xalgosegmask", ["blast", "xobjmgr", "seqset"])
            _add_lib_component("xid_mapper", ["xobjmgr", "seqset", "sqlitewrapp"])
            _add_lib_component("xmergetree", ["xobjmgr", "seqset"])
            _add_lib_component("xnetblastcli", ["xconnect", "xnetblast"])
            _add_lib_component("xobjutil", ["submit", "xobjmgr"])
            # 10--------------------------------------------------------------------------
            _add_lib_component("cdd", ["cn3d", "scoremat"])
            _add_lib_component("gbproj", ["submit", "xconnect"])
            _add_lib_component("id1cli", ["id1", "xconnect"])
            _add_lib_component("id2", ["seqsplit"])
            _add_lib_component("xnetblast", ["scoremat"])
            _add_lib_component("xobjmgr", ["genome_collection", "seqedit", "seqsplit", "submit"])
            _add_lib_component("xobjread", ["submit", "xlogging"])
            # 9--------------------------------------------------------------------------
            _add_lib_component("asn_cache", ["bdb", "seqset", "xcompress"])
            _add_lib_component("bamread", ["seqset", "xcompress", "VDB"])
            _add_lib_component("cn3d", ["mmdb"])
            _add_lib_component("dbsnp_tooltip_service", ["trackmgr"])
            _add_lib_component("gencoll_client", ["genome_collection", "sqlitewrapp", "xcompress", "xconnect", "SQLITE3"])
            _add_lib_component("id1", ["seqset"])
            _add_lib_component("local_taxon", ["taxon1", "sqlitewrapp", "SQLITE3"])
            _add_lib_component("proj", ["pubmed", "seqset"])
            _add_lib_component("remapcli", ["remap", "xconnect"])
            _add_lib_component("scoremat", ["seqset"])
            _add_lib_component("searchbyrsid", ["trackmgr"])
            _add_lib_component("seqedit", ["seqset"])
            _add_lib_component("seqsplit", ["seqset"])
            _add_lib_component("submit", ["seqset"])
            _add_lib_component("trackmgrcli", ["trackmgr", "xconnect"])
            _add_lib_component("trackmgrgridcli", ["trackmgr", "xcompress", "xconnserv", "LZO"])
            _add_lib_component("valerr", ["xser", "seqset"])
            # 8--------------------------------------------------------------------------
            _add_lib_component("dbsnp_ptis", ["seq", "grpc_integration", "PROTOBUF", "GRPC", "Z"])
            _add_lib_component("entrezgene", ["seq"])
            _add_lib_component("eutils_client", ["seq", "xmlwrapp"])
            _add_lib_component("genome_collection", ["seq"])
            _add_lib_component("homologene", ["seq"])
            _add_lib_component("macro", ["seq"])
            _add_lib_component("mlacli", ["mla", "xconnect"])
            _add_lib_component("mmdb", ["seq"])
            _add_lib_component("omssa", ["seq"])
            _add_lib_component("pcassay", ["seq", "pcsubstance"])
            _add_lib_component("pcassay2", ["seq", "pcsubstance"])
            _add_lib_component("remap", ["seq"])
            _add_lib_component("seqset", ["seq"])
            _add_lib_component("seqtest", ["seq"])
            _add_lib_component("taxon1", ["seq", "xconnect"])
            _add_lib_component("taxon3", ["seq", "xconnect"])
            _add_lib_component("trackmgr", ["seq"])
            _add_lib_component("variation", ["seq"])
            # 7--------------------------------------------------------------------------
            _add_lib_component("mla", ["medlars", "pubmed", "pub"])
            _add_lib_component("pcsubstance", ["pub"])
            _add_lib_component("seq", ["pub", "seqcode", "sequtil"])
            # 6--------------------------------------------------------------------------
            _add_lib_component("pub", ["medline"])
            _add_lib_component("pubmed", ["medline"])
            # 5--------------------------------------------------------------------------
            _add_lib_component("medlars", ["biblio"])
            _add_lib_component("medline", ["biblio"])
            _add_lib_component("netstorage", ["ncbi_xcache_netcache"])
            # 4--------------------------------------------------------------------------
            _add_lib_component("biblio", ["libgeneral"])
            _add_lib_component("biotree", ["libgeneral"])
            _add_lib_component("entrez2cli", ["entrez2", "xconnect"])
            _add_lib_component("eutils", ["einfo", "esearch", "egquery", "epost", "elink", "esummary", "espell", "ehistory", "uilist", "xconnect"])
            _add_lib_component("ncbi_xblobstorage_netcache", ["xconnserv"])
            _add_lib_component("ncbi_xcache_netcache", ["xconnserv"])
            _add_lib_component("sample_asn", ["libgeneral"])
            _add_lib_component("sdbapi", ["dbapi", "dbapi_util_blobstore", "ncbi_xdbapi_ftds", "ncbi_xdbapi_ftds100", "xutil", "xconnect"])
            _add_lib_component("valid", ["libgeneral", "xregexp"])
            _add_lib_component("xgridcgi", ["xcgi", "xconnserv", "xhtml"])
            _add_lib_component("xobjmanip", ["libgeneral"])
            _add_lib_component("xsoap_server", ["xcgi", "xsoap"])
            # 3--------------------------------------------------------------------------
            _add_lib_component("access", ["xser"])
            _add_lib_component("asn_sample_lib", ["xser"])
            _add_lib_component("blastxml", ["xser"])
            _add_lib_component("blastxml2", ["xser"])
            _add_lib_component("ctransition_nlmzip", ["ctransition", "xcompress"])
            # _add_lib_component("dbapi_sample_base", ["ncbi_xdbapi_ftds", "ncbi_xdbapi_ftds100", "dbapi_driver", "xutil", "ncbi_xdbapi_ctlib", "Sybase", "ODBC"])
            _add_lib_component("dbapi_sample_base", ["ncbi_xdbapi_ftds", "ncbi_xdbapi_ftds100", "dbapi_driver", "xutil"])
            _add_lib_component("dbapi_util_blobstore", ["dbapi_driver", "xcompress"])
            _add_lib_component("docsum", ["xser"])
            _add_lib_component("dtd_sample_lib", ["xser"])
            _add_lib_component("egquery", ["xser"])
            _add_lib_component("ehistory", ["xser"])
            _add_lib_component("einfo", ["xser"])
            _add_lib_component("elink", ["xser"])
            _add_lib_component("entrez2", ["xser"])
            _add_lib_component("epost", ["xser"])
            _add_lib_component("esearch", ["xser"])
            _add_lib_component("espell", ["xser"])
            _add_lib_component("esummary", ["xser"])
            _add_lib_component("featdef", ["xser"])
            _add_lib_component("gbseq", ["xser"])
            if "general" in allexports:
                self.cpp_info.components["libgeneral"].libs = ["$<1:general>"]
                self.cpp_info.components["libgeneral"].requires = ["xser"]
            if "generalasn" in allexports:
                self.cpp_info.components["libgeneral"].libs = ["generalasn"]
                self.cpp_info.components["libgeneral"].requires = ["xser"]
            _add_lib_component("genesbyloc", ["xser"])
            _add_lib_component("hydra_client", ["xmlwrapp"])
            _add_lib_component("insdseq", ["xser"])
            _add_lib_component("jsd_sample_lib", ["xser"])
            _add_lib_component("linkout", ["xser"])
            _add_lib_component("mim", ["xser"])
            _add_lib_component("msbuild_dataobj", ["xser"])
            _add_lib_component("ncbi_xcache_bdb", ["bdb", "BerkeleyDB"])
            _add_lib_component("objcoords", ["xser"])
            _add_lib_component("objprt", ["xser"])
            _add_lib_component("pepXML", ["xser"])
            _add_lib_component("pmcidconv_client", ["xmlwrapp"])
            _add_lib_component("python_ncbi_dbapi", ["dbapi", "xutil", "PYTHON"])
            _add_lib_component("seqcode", ["xser"])
            _add_lib_component("soap_dataobj", ["xser"])
            _add_lib_component("tinyseq", ["xser"])
            _add_lib_component("uilist", ["xser"])
            _add_lib_component("varrep", ["xser"])
            _add_lib_component("xalgotext", ["xcompress"])
            _add_lib_component("xcgi_redirect", ["xcgi", "xhtml"])
            _add_lib_component("xconnserv", ["xthrserv"])
            _add_lib_component("xcser", ["xser"])
            _add_lib_component("xfcgi_mt", ["xcgi", "FASTCGIPP"])
            _add_lib_component("xmlreaders", ["xmlwrapp"])
            _add_lib_component("xsd_sample_lib", ["xser"])
            _add_lib_component("xsoap", ["xconnect", "xser"])
            # 2--------------------------------------------------------------------------
            _add_lib_component("bdb", ["xutil", "BerkeleyDB"])
            _add_lib_component("dbapi", ["dbapi_driver"])
            _add_lib_component("grpc_integration", ["xutil", "GRPC", "Z"])
            _add_lib_component("gumbelparams", ["tables", "xutil"])
            _add_lib_component("ncbi_xdbapi_ctlib", ["dbapi_driver", "Sybase"])
            _add_lib_component("ncbi_xdbapi_ftds", ["dbapi_driver", "ct_ftds100"])
            _add_lib_component("ncbi_xdbapi_ftds100", ["ct_ftds100", "dbapi_driver"])
            _add_lib_component("ncbi_xdbapi_mysql", ["dbapi_driver", "MySQL"])
            _add_lib_component("ncbi_xdbapi_odbc", ["dbapi_driver", "ODBC"])
            _add_lib_component("psg_cache", ["xncbi", "psg_protobuf", "psg_cassandra", "LMDB", "PROTOBUF", "CASSANDRA"])
            _add_lib_component("wx_tools", ["xutil", "wxWidgets"])
            _add_lib_component("xasn", ["xhtml", "NCBI_C"])
            _add_lib_component("xcgi", ["xutil"])
            _add_lib_component("xcompress", ["xutil", "Z", "BZ2", "LZO"])
            _add_lib_component("xfcgi", ["xutil", "FASTCGI"])
            _add_lib_component("xmlwrapp", ["xconnect", "XML", "XSLT"])
            _add_lib_component("xregexp_template_tester", ["xregexp", "PCRE"])
            _add_lib_component("xser", ["xutil"])
            _add_lib_component("xstruct_thread", ["xutil"])
            _add_lib_component("xthrserv", ["xconnect", "xutil"])
            _add_lib_component("xxconnect2", ["xconnect", "UV", "NGHTTP2"])
            # 1--------------------------------------------------------------------------
            _add_lib_component("basic_sample_lib", ["xncbi"])
            _add_lib_component("blast", ["composition_adjustment", "connect", "tables"])
            _add_lib_component("connssl", ["connect"])
            _add_lib_component("ct_ftds100", ["tds_ftds100"])
            _add_lib_component("ctransition", ["xncbi"])
            _add_lib_component("dbapi_driver", ["xncbi"])
            _add_lib_component("gene_info", ["xncbi"])
            _add_lib_component("jaeger_tracer", ["xncbi", "JAEGER"])
            _add_lib_component("odbc_ftds100", ["tds_ftds100"])
            _add_lib_component("psg_cassandra", ["connect", "xncbi", "CASSANDRA"])
            _add_lib_component("psg_diag", ["xncbi"])
            _add_lib_component("sequtil", ["xncbi"])
            _add_lib_component("sqlitewrapp", ["xncbi", "SQLITE3"])
            _add_lib_component("sybdb_ftds100", ["tds_ftds100"])
            _add_lib_component("test_boost", ["xncbi", "Boost"])
            _add_lib_component("test_mt", ["xncbi"])
            _add_lib_component("utrtprof", ["xncbi"])
            _add_lib_component("xalgovmerge", ["xncbi"])
            _add_lib_component("xconnect", ["xncbi"])
            _add_lib_component("xctools", ["connect", "xncbi", "NCBI_C"])
            _add_lib_component("xdiff", ["xncbi"])
            _add_lib_component("xhtml", ["xncbi"])
            _add_lib_component("ximage", ["xncbi", "Z", "JPEG", "PNG", "GIF", "TIFF"])
            _add_lib_component("xlogging", ["xncbi"])
            _add_lib_component("xpbacktest", ["xncbi"])
            _add_lib_component("xqueryparse", ["xncbi"])
            _add_lib_component("xregexp", ["xncbi", "PCRE"])
            _add_lib_component("xstruct_dp", ["xncbi"])
            _add_lib_component("xutil", ["xncbi"])
            _add_lib_component("xxconnect", ["xncbi", "NCBI_C"])
            # 0--------------------------------------------------------------------------
            _add_lib_component("clog", ["ORIGLIBS"])
            _add_lib_component("composition_adjustment", ["ORIGLIBS"])
            _add_lib_component("connect", ["NETWORKLIBS", "ORIGLIBS"])
            _add_lib_component("edit_imgt_file", ["ORIGLIBS"])
            _add_lib_component("fastme", ["ORIGLIBS"])
            _add_lib_component("lapackwrapp", ["LAPACK", "ORIGLIBS"])
            _add_lib_component("psg_protobuf", ["PROTOBUF", "ORIGLIBS"])
            _add_lib_component("tables", ["ORIGLIBS"])
            _add_lib_component("task_server", ["Boost", "ORIGLIBS"])
            _add_lib_component("tds_ftds100", ["ORIGLIBS"])
            _add_lib_component("test_dll", ["ORIGLIBS"])
            _add_lib_component("xncbi", ["ORIGLIBS"])
        # ----------------------------------------------------------------------------
        if self.settings.os == "Windows":
            self.cpp_info.components["ORIGLIBS"].defines.append("_UNICODE")
            self.cpp_info.components["ORIGLIBS"].defines.append("_CRT_SECURE_NO_WARNINGS=1")
        else:
            self.cpp_info.components["ORIGLIBS"].defines.append("_MT")
            self.cpp_info.components["ORIGLIBS"].defines.append("_REENTRANT")
            self.cpp_info.components["ORIGLIBS"].defines.append("_THREAD_SAFE")
            self.cpp_info.components["ORIGLIBS"].defines.append("_LARGEFILE_SOURCE")
            self.cpp_info.components["ORIGLIBS"].defines.append("_LARGEFILE64_SOURCE")
            self.cpp_info.components["ORIGLIBS"].defines.append("_FILE_OFFSET_BITS=64")
        if self.options.shared:
            self.cpp_info.components["ORIGLIBS"].defines.append("NCBI_DLL_BUILD")
        if self.settings.build_type == "Debug":
            self.cpp_info.components["ORIGLIBS"].defines.append("_DEBUG")
        else:
            self.cpp_info.components["ORIGLIBS"].defines.append("NDEBUG")
        self.cpp_info.components["ORIGLIBS"].builddirs.append("res")
        self.cpp_info.components["ORIGLIBS"].build_modules = ["res/build-system/cmake/CMake.NCBIpkg.conan.cmake"]
