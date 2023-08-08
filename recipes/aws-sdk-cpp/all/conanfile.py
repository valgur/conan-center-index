# Warnings:
#   Unexpected method '_internal_requirements'
#   Unexpected method '_use_aws_crt_cpp'
#   Unexpected method '_res_folder'
#   Unexpected method '_create_project_cmake_module'

# TODO: verify the Conan v2 migration

import os

from conan import ConanFile, conan_version
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.android import android_abi
from conan.tools.apple import (
    XCRun,
    fix_apple_shared_install_name,
    is_apple_os,
    to_apple_arch,
)
from conan.tools.build import (
    build_jobs,
    can_run,
    check_min_cppstd,
    cross_building,
    default_cppstd,
    stdcpp_library,
    valid_min_cppstd,
)
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
from conan.tools.env import (
    Environment,
    VirtualBuildEnv,
    VirtualRunEnv,
)
from conan.tools.files import (
    apply_conandata_patches,
    chdir,
    collect_libs,
    copy,
    download,
    export_conandata_patches,
    get,
    load,
    mkdir,
    patch,
    patches,
    rename,
    replace_in_file,
    rm,
    rmdir,
    save,
    symlinks,
    unzip,
)
from conan.tools.gnu import (
    Autotools,
    AutotoolsDeps,
    AutotoolsToolchain,
    PkgConfig,
    PkgConfigDeps,
)
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import (
    MSBuild,
    MSBuildDeps,
    MSBuildToolchain,
    NMakeDeps,
    NMakeToolchain,
    VCVars,
    check_min_vs,
    is_msvc,
    is_msvc_static_runtime,
    msvc_runtime_flag,
    unix_path,
    unix_path_package_info_legacy,
    vs_layout,
)
from conan.tools.scm import Version
from conan.tools.system import package_manager
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.53.0"


class AwsSdkCppConan(ConanFile):
    name = "aws-sdk-cpp"
    description = "AWS SDK for C++"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/aws/aws-sdk-cpp"
    topics = ("aws", "cpp", "cross-platform", "amazon", "cloud")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "min_size": [True, False],
        "access-management": [True, False],
        "accessanalyzer": [True, False],
        "acm": [True, False],
        "acm-pca": [True, False],
        "alexaforbusiness": [True, False],
        "amp": [True, False],
        "amplify": [True, False],
        "amplifybackend": [True, False],
        "apigateway": [True, False],
        "apigatewaymanagementapi": [True, False],
        "apigatewayv2": [True, False],
        "appconfig": [True, False],
        "appflow": [True, False],
        "appintegrations": [True, False],
        "application-autoscaling": [True, False],
        "application-insights": [True, False],
        "appmesh": [True, False],
        "appstream": [True, False],
        "appsync": [True, False],
        "athena": [True, False],
        "auditmanager": [True, False],
        "autoscaling": [True, False],
        "autoscaling-plans": [True, False],
        "awstransfer": [True, False],
        "backup": [True, False],
        "batch": [True, False],
        "braket": [True, False],
        "budgets": [True, False],
        "ce": [True, False],
        "chime": [True, False],
        "cloud9": [True, False],
        "clouddirectory": [True, False],
        "cloudformation": [True, False],
        "cloudfront": [True, False],
        "cloudhsm": [True, False],
        "cloudhsmv2": [True, False],
        "cloudsearch": [True, False],
        "cloudsearchdomain": [True, False],
        "cloudtrail": [True, False],
        "codeartifact": [True, False],
        "codebuild": [True, False],
        "codecommit": [True, False],
        "codedeploy": [True, False],
        "codeguru-reviewer": [True, False],
        "codeguruprofiler": [True, False],
        "codepipeline": [True, False],
        "codestar": [True, False],
        "codestar-connections": [True, False],
        "codestar-notifications": [True, False],
        "cognito-identity": [True, False],
        "cognito-idp": [True, False],
        "cognito-sync": [True, False],
        "comprehend": [True, False],
        "comprehendmedical": [True, False],
        "compute-optimizer": [True, False],
        "config": [True, False],
        "connect": [True, False],
        "connect-contact-lens": [True, False],
        "connectparticipant": [True, False],
        "cur": [True, False],
        "customer-profiles": [True, False],
        "databrew": [True, False],
        "dataexchange": [True, False],
        "datapipeline": [True, False],
        "datasync": [True, False],
        "dax": [True, False],
        "detective": [True, False],
        "devicefarm": [True, False],
        "devops-guru": [True, False],
        "directconnect": [True, False],
        "discovery": [True, False],
        "dlm": [True, False],
        "dms": [True, False],
        "docdb": [True, False],
        "ds": [True, False],
        "dynamodb": [True, False],
        "dynamodbstreams": [True, False],
        "ebs": [True, False],
        "ec2": [True, False],
        "ec2-instance-connect": [True, False],
        "ecr": [True, False],
        "ecr-public": [True, False],
        "ecs": [True, False],
        "eks": [True, False],
        "elastic-inference": [True, False],
        "elasticache": [True, False],
        "elasticbeanstalk": [True, False],
        "elasticfilesystem": [True, False],
        "elasticloadbalancing": [True, False],
        "elasticloadbalancingv2": [True, False],
        "elasticmapreduce": [True, False],
        "elastictranscoder": [True, False],
        "email": [True, False],
        "emr-containers": [True, False],
        "es": [True, False],
        "eventbridge": [True, False],
        "events": [True, False],
        "firehose": [True, False],
        "fms": [True, False],
        "forecast": [True, False],
        "forecastquery": [True, False],
        "frauddetector": [True, False],
        "fsx": [True, False],
        "gamelift": [True, False],
        "glacier": [True, False],
        "globalaccelerator": [True, False],
        "glue": [True, False],
        "greengrass": [True, False],
        "greengrassv2": [True, False],
        "groundstation": [True, False],
        "guardduty": [True, False],
        "health": [True, False],
        "healthlake": [True, False],
        "honeycode": [True, False],
        "iam": [True, False],
        "identity-management": [True, False],
        "identitystore": [True, False],
        "imagebuilder": [True, False],
        "importexport": [True, False],
        "inspector": [True, False],
        "iot": [True, False],
        "iot-data": [True, False],
        "iot-jobs-data": [True, False],
        "iot1click-devices": [True, False],
        "iot1click-projects": [True, False],
        "iotanalytics": [True, False],
        "iotdeviceadvisor": [True, False],
        "iotevents": [True, False],
        "iotevents-data": [True, False],
        "iotfleethub": [True, False],
        "iotsecuretunneling": [True, False],
        "iotsitewise": [True, False],
        "iotthingsgraph": [True, False],
        "iotwireless": [True, False],
        "ivs": [True, False],
        "kafka": [True, False],
        "kendra": [True, False],
        "kinesis": [True, False],
        "kinesis-video-archived-media": [True, False],
        "kinesis-video-media": [True, False],
        "kinesis-video-signaling": [True, False],
        "kinesisanalytics": [True, False],
        "kinesisanalyticsv2": [True, False],
        "kinesisvideo": [True, False],
        "kms": [True, False],
        "lakeformation": [True, False],
        "lambda": [True, False],
        "lex": [True, False],
        "lex-models": [True, False],
        "lexv2-models": [True, False],
        "lexv2-runtime": [True, False],
        "license-manager": [True, False],
        "lightsail": [True, False],
        "location": [True, False],
        "logs": [True, False],
        "lookoutvision": [True, False],
        "machinelearning": [True, False],
        "macie": [True, False],
        "macie2": [True, False],
        "managedblockchain": [True, False],
        "marketplace-catalog": [True, False],
        "marketplace-entitlement": [True, False],
        "marketplacecommerceanalytics": [True, False],
        "mediaconnect": [True, False],
        "mediaconvert": [True, False],
        "medialive": [True, False],
        "mediapackage": [True, False],
        "mediapackage-vod": [True, False],
        "mediastore": [True, False],
        "mediastore-data": [True, False],
        "mediatailor": [True, False],
        "meteringmarketplace": [True, False],
        "migrationhub-config": [True, False],
        "mobile": [True, False],
        "mobileanalytics": [True, False],
        "monitoring": [True, False],
        "mq": [True, False],
        "mturk-requester": [True, False],
        "mwaa": [True, False],
        "neptune": [True, False],
        "network-firewall": [True, False],
        "networkmanager": [True, False],
        "opsworks": [True, False],
        "opsworkscm": [True, False],
        "organizations": [True, False],
        "outposts": [True, False],
        "personalize": [True, False],
        "personalize-events": [True, False],
        "personalize-runtime": [True, False],
        "pi": [True, False],
        "pinpoint": [True, False],
        "pinpoint-email": [True, False],
        "polly": [True, False],
        "polly-sample": [True, False],
        "pricing": [True, False],
        "qldb": [True, False],
        "qldb-session": [True, False],
        "queues": [True, False],
        "quicksight": [True, False],
        "ram": [True, False],
        "rds": [True, False],
        "rds-data": [True, False],
        "redshift": [True, False],
        "redshift-data": [True, False],
        "rekognition": [True, False],
        "resource-groups": [True, False],
        "resourcegroupstaggingapi": [True, False],
        "robomaker": [True, False],
        "route53": [True, False],
        "route53domains": [True, False],
        "route53resolver": [True, False],
        "s3": [True, False],
        "s3-crt": [True, False],
        "s3-encryption": [True, False],
        "s3control": [True, False],
        "s3outposts": [True, False],
        "sagemaker": [True, False],
        "sagemaker-a2i-runtime": [True, False],
        "sagemaker-edge": [True, False],
        "sagemaker-featurestore-runtime": [True, False],
        "sagemaker-runtime": [True, False],
        "savingsplans": [True, False],
        "schemas": [True, False],
        "sdb": [True, False],
        "secretsmanager": [True, False],
        "securityhub": [True, False],
        "serverlessrepo": [True, False],
        "service-quotas": [True, False],
        "servicecatalog": [True, False],
        "servicecatalog-appregistry": [True, False],
        "servicediscovery": [True, False],
        "sesv2": [True, False],
        "shield": [True, False],
        "signer": [True, False],
        "sms": [True, False],
        "sms-voice": [True, False],
        "snowball": [True, False],
        "sns": [True, False],
        "sqs": [True, False],
        "ssm": [True, False],
        "sso": [True, False],
        "sso-admin": [True, False],
        "sso-oidc": [True, False],
        "states": [True, False],
        "storagegateway": [True, False],
        "sts": [True, False],
        "support": [True, False],
        "swf": [True, False],
        "synthetics": [True, False],
        "text-to-speech": [True, False],
        "textract": [True, False],
        "timestream-query": [True, False],
        "timestream-write": [True, False],
        "transcribe": [True, False],
        "transcribestreaming": [True, False],
        "transfer": [True, False],
        "translate": [True, False],
        "waf": [True, False],
        "waf-regional": [True, False],
        "wafv2": [True, False],
        "wellarchitected": [True, False],
        "workdocs": [True, False],
        "worklink": [True, False],
        "workmail": [True, False],
        "workmailmessageflow": [True, False],
        "workspaces": [True, False],
        "xray": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "min_size": False,
        "access-management": True,
        "accessanalyzer": False,
        "acm": False,
        "acm-pca": False,
        "alexaforbusiness": False,
        "amp": False,
        "amplify": False,
        "amplifybackend": False,
        "apigateway": False,
        "apigatewaymanagementapi": False,
        "apigatewayv2": False,
        "appconfig": False,
        "appflow": False,
        "appintegrations": False,
        "application-autoscaling": False,
        "application-insights": False,
        "appmesh": False,
        "appstream": False,
        "appsync": False,
        "athena": False,
        "auditmanager": False,
        "autoscaling": False,
        "autoscaling-plans": False,
        "awstransfer": False,
        "backup": False,
        "batch": False,
        "braket": False,
        "budgets": False,
        "ce": False,
        "chime": False,
        "cloud9": False,
        "clouddirectory": False,
        "cloudformation": False,
        "cloudfront": False,
        "cloudhsm": False,
        "cloudhsmv2": False,
        "cloudsearch": False,
        "cloudsearchdomain": False,
        "cloudtrail": False,
        "codeartifact": False,
        "codebuild": False,
        "codecommit": False,
        "codedeploy": False,
        "codeguru-reviewer": False,
        "codeguruprofiler": False,
        "codepipeline": False,
        "codestar": False,
        "codestar-connections": False,
        "codestar-notifications": False,
        "cognito-identity": False,
        "cognito-idp": False,
        "cognito-sync": False,
        "comprehend": False,
        "comprehendmedical": False,
        "compute-optimizer": False,
        "config": False,
        "connect": False,
        "connect-contact-lens": False,
        "connectparticipant": False,
        "cur": False,
        "customer-profiles": False,
        "databrew": False,
        "dataexchange": False,
        "datapipeline": False,
        "datasync": False,
        "dax": False,
        "detective": False,
        "devicefarm": False,
        "devops-guru": False,
        "directconnect": False,
        "discovery": False,
        "dlm": False,
        "dms": False,
        "docdb": False,
        "ds": False,
        "dynamodb": False,
        "dynamodbstreams": False,
        "ebs": False,
        "ec2": False,
        "ec2-instance-connect": False,
        "ecr": False,
        "ecr-public": False,
        "ecs": False,
        "eks": False,
        "elastic-inference": False,
        "elasticache": False,
        "elasticbeanstalk": False,
        "elasticfilesystem": False,
        "elasticloadbalancing": False,
        "elasticloadbalancingv2": False,
        "elasticmapreduce": False,
        "elastictranscoder": False,
        "email": False,
        "emr-containers": False,
        "es": False,
        "eventbridge": False,
        "events": False,
        "firehose": False,
        "fms": False,
        "forecast": False,
        "forecastquery": False,
        "frauddetector": False,
        "fsx": False,
        "gamelift": False,
        "glacier": False,
        "globalaccelerator": False,
        "glue": False,
        "greengrass": False,
        "greengrassv2": False,
        "groundstation": False,
        "guardduty": False,
        "health": False,
        "healthlake": False,
        "honeycode": False,
        "iam": False,
        "identity-management": True,
        "identitystore": False,
        "imagebuilder": False,
        "importexport": False,
        "inspector": False,
        "iot": False,
        "iot-data": False,
        "iot-jobs-data": False,
        "iot1click-devices": False,
        "iot1click-projects": False,
        "iotanalytics": False,
        "iotdeviceadvisor": False,
        "iotevents": False,
        "iotevents-data": False,
        "iotfleethub": False,
        "iotsecuretunneling": False,
        "iotsitewise": False,
        "iotthingsgraph": False,
        "iotwireless": False,
        "ivs": False,
        "kafka": False,
        "kendra": False,
        "kinesis": False,
        "kinesis-video-archived-media": False,
        "kinesis-video-media": False,
        "kinesis-video-signaling": False,
        "kinesisanalytics": False,
        "kinesisanalyticsv2": False,
        "kinesisvideo": False,
        "kms": False,
        "lakeformation": False,
        "lambda": False,
        "lex": False,
        "lex-models": False,
        "lexv2-models": False,
        "lexv2-runtime": False,
        "license-manager": False,
        "lightsail": False,
        "location": False,
        "logs": False,
        "lookoutvision": False,
        "machinelearning": False,
        "macie": False,
        "macie2": False,
        "managedblockchain": False,
        "marketplace-catalog": False,
        "marketplace-entitlement": False,
        "marketplacecommerceanalytics": False,
        "mediaconnect": False,
        "mediaconvert": False,
        "medialive": False,
        "mediapackage": False,
        "mediapackage-vod": False,
        "mediastore": False,
        "mediastore-data": False,
        "mediatailor": False,
        "meteringmarketplace": False,
        "migrationhub-config": False,
        "mobile": False,
        "mobileanalytics": False,
        "monitoring": True,
        "mq": False,
        "mturk-requester": False,
        "mwaa": False,
        "neptune": False,
        "network-firewall": False,
        "networkmanager": False,
        "opsworks": False,
        "opsworkscm": False,
        "organizations": False,
        "outposts": False,
        "personalize": False,
        "personalize-events": False,
        "personalize-runtime": False,
        "pi": False,
        "pinpoint": False,
        "pinpoint-email": False,
        "polly": False,
        "polly-sample": False,
        "pricing": False,
        "qldb": False,
        "qldb-session": False,
        "queues": True,
        "quicksight": False,
        "ram": False,
        "rds": False,
        "rds-data": False,
        "redshift": False,
        "redshift-data": False,
        "rekognition": False,
        "resource-groups": False,
        "resourcegroupstaggingapi": False,
        "robomaker": False,
        "route53": False,
        "route53domains": False,
        "route53resolver": False,
        "s3": False,
        "s3-crt": False,
        "s3-encryption": True,
        "s3control": False,
        "s3outposts": False,
        "sagemaker": False,
        "sagemaker-a2i-runtime": False,
        "sagemaker-edge": False,
        "sagemaker-featurestore-runtime": False,
        "sagemaker-runtime": False,
        "savingsplans": False,
        "schemas": False,
        "sdb": False,
        "secretsmanager": False,
        "securityhub": False,
        "serverlessrepo": False,
        "service-quotas": False,
        "servicecatalog": False,
        "servicecatalog-appregistry": False,
        "servicediscovery": False,
        "sesv2": False,
        "shield": False,
        "signer": False,
        "sms": False,
        "sms-voice": False,
        "snowball": False,
        "sns": False,
        "sqs": False,
        "ssm": False,
        "sso": False,
        "sso-admin": False,
        "sso-oidc": False,
        "states": False,
        "storagegateway": False,
        "sts": False,
        "support": False,
        "swf": False,
        "synthetics": False,
        "text-to-speech": True,
        "textract": False,
        "timestream-query": False,
        "timestream-write": False,
        "transcribe": False,
        "transcribestreaming": False,
        "transfer": True,
        "translate": False,
        "waf": False,
        "waf-regional": False,
        "wafv2": False,
        "wellarchitected": False,
        "workdocs": False,
        "worklink": False,
        "workmail": False,
        "workmailmessageflow": False,
        "workspaces": False,
        "xray": False,
    }

    @property
    def _internal_requirements(self):
        return {
            "access-management": ["iam", "cognito-identity"],
            "identity-management": ["cognito-identity", "sts"],
            "queues": ["sqs"],
            "s3-encryption": ["s3", "kms"],
            "text-to-speech": ["polly"],
            "transfer": ["s3"],
        }

    @property
    def _use_aws_crt_cpp(self):
        return Version(self.version) >= "1.9"

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if Version(self.version) < "1.9":
            delattr(self.options, "s3-crt")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("aws-c-common/0.9.0")
        if self._use_aws_crt_cpp:
            self.requires("aws-c-cal/0.5.20")
            self.requires("aws-c-http/0.6.22")
            self.requires("aws-c-io/0.13.4")
            self.requires("aws-crt-cpp/0.18.8")
        else:
            self.requires("aws-c-event-stream/0.2.15")
        if self.settings.os != "Windows":
            self.requires("openssl/[>=1.1 <4]")
            self.requires("libcurl/8.2.0")
        if self.settings.os in ["Linux", "FreeBSD"]:
            if self.options.get_safe("text-to-speech"):
                self.requires("pulseaudio/14.2")

    def package_id(self):
        for hl_comp in self._internal_requirements.keys():
            if getattr(self.options, hl_comp):
                for internal_requirement in self._internal_requirements[hl_comp]:
                    setattr(self.info.options, internal_requirement, True)

    def validate(self):
        if (
            self.options.shared
            and self.settings.compiler == "gcc"
            and Version(self.settings.compiler.version) < "6.0"
        ):
            raise ConanInvalidConfiguration(
                "Doesn't support gcc5 / shared. "
                "See https://github.com/conan-io/conan-center-index/pull/4401#issuecomment-802631744"
            )
        if (
            Version(self.version) < "1.9.234"
            and self.settings.compiler == "gcc"
            and Version(self.settings.compiler.version) >= "11.0"
            and self.settings.build_type == "Release"
        ):
            raise ConanInvalidConfiguration(
                "Versions prior to 1.9.234 don't support release builds on >= gcc 11 "
                "See https://github.com/aws/aws-sdk-cpp/issues/1505"
            )
        if self._use_aws_crt_cpp:
            if is_msvc_static_runtime(self):
                raise ConanInvalidConfiguration("Static runtime is not working for more recent releases")
        else:
            if is_apple_os(self) and self.settings.arch == "armv8":
                raise ConanInvalidConfiguration(
                    "This version doesn't support arm8. See https://github.com/aws/aws-sdk-cpp/issues/1542"
                )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_FIND_ROOT_PATH_MODE_PACKAGE"] = "NONE"

        build_only = ["core"]
        for sdk in self._sdks:
            if self.options.get_safe(sdk):
                build_only.append(sdk)
        tc.variables["BUILD_ONLY"] = ";".join(build_only)

        tc.variables["ENABLE_UNITY_BUILD"] = True
        tc.variables["ENABLE_TESTING"] = False
        tc.variables["AUTORUN_UNIT_TESTS"] = False
        tc.variables["BUILD_DEPS"] = False
        tc.variables["ENABLE_OPENSSL_ENCRYPTION"] = self.settings.os != "Windows"

        tc.variables["MINIMIZE_SIZE"] = self.options.min_size
        if is_msvc(self) and not self._use_aws_crt_cpp:
            tc.variables["FORCE_SHARED_CRT"] = not is_msvc_static_runtime(self)

        if cross_building(self):
            tc.variables["CURL_HAS_H2_EXITCODE"] = "0"
            tc.variables["CURL_HAS_H2_EXITCODE__TRYRUN_OUTPUT"] = ""
            tc.variables["CURL_HAS_TLS_PROXY_EXITCODE"] = "0"
            tc.variables["CURL_HAS_TLS_PROXY_EXITCODE__TRYRUN_OUTPUT"] = ""

        if is_msvc(self):
            tc.preprocessor_definitions["_SILENCE_CXX17_OLD_ALLOCATOR_MEMBERS_DEPRECATION_WARNING"] = ""

        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _res_folder(self):
        return "res"

    def _create_project_cmake_module(self):
        # package files needed to build other components (e.g. aws-cdi-sdk) with this SDK
        for file in [
            "cmake/compiler_settings.cmake",
            "cmake/initialize_project_version.cmake",
            "cmake/utilities.cmake",
            "cmake/sdk_plugin_conf.cmake",
            "toolchains/cmakeProjectConfig.cmake",
            "toolchains/pkg-config.pc.in",
            "aws-cpp-sdk-core/include/aws/core/VersionConfig.h",
        ]:
            copy(self, file, src=self.source_folder, dst=self._res_folder)
            replace_in_file(
                self,
                os.path.join(self.package_folder, self._res_folder, file),
                "CMAKE_CURRENT_SOURCE_DIR",
                "AWS_NATIVE_SDK_ROOT",
                strict=False,
            )

        # avoid getting error from hook
        with chdir(self, os.path.join(self.package_folder, self._res_folder)):
            rename(
                self,
                os.path.join("toolchains", "cmakeProjectConfig.cmake"),
                os.path.join("toolchains", "cmakeProjectConf.cmake"),
            )
            replace_in_file(
                self,
                os.path.join("cmake", "utilities.cmake"),
                "cmakeProjectConfig.cmake",
                "cmakeProjectConf.cmake",
            )

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        if is_msvc(self):
            copy(self, pattern="*.lib", dst=os.path.join(self.package_folder, "lib"), keep_path=False)
            rm(self, "*.lib", os.path.join(self.package_folder, "bin"), recursive=True)

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

        self._create_project_cmake_module()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "AWSSDK")

        # core component
        self.cpp_info.components["core"].set_property("cmake_target_name", "AWS::aws-sdk-cpp-core")
        self.cpp_info.components["core"].set_property("pkg_config_name", "aws-sdk-cpp-core")
        self.cpp_info.components["core"].libs = ["aws-cpp-sdk-core"]
        self.cpp_info.components["core"].requires = ["aws-c-common::aws-c-common-lib"]
        if self._use_aws_crt_cpp:
            self.cpp_info.components["core"].requires.extend(
                [
                    "aws-c-cal::aws-c-cal-lib",
                    "aws-c-http::aws-c-http-lib",
                    "aws-c-io::aws-c-io-lib",
                    "aws-crt-cpp::aws-crt-cpp-lib",
                ]
            )
        else:
            self.cpp_info.components["core"].requires.append("aws-c-event-stream::aws-c-event-stream-lib")

        # other components
        enabled_sdks = [sdk for sdk in self._sdks if self.options.get_safe(sdk)]
        for hl_comp in self._internal_requirements.keys():
            if getattr(self.options, hl_comp):
                for internal_requirement in self._internal_requirements[hl_comp]:
                    if internal_requirement not in enabled_sdks:
                        enabled_sdks.append(internal_requirement)

        for sdk in enabled_sdks:
            # TODO: there is no way to properly emulate COMPONENTS names for
            #       find_package(AWSSDK COMPONENTS <sdk>) in set_property()
            #       right now: see https://github.com/conan-io/conan/issues/10258
            self.cpp_info.components[sdk].set_property("cmake_target_name", "AWS::aws-sdk-cpp-{}".format(sdk))
            self.cpp_info.components[sdk].set_property("pkg_config_name", "aws-sdk-cpp-{}".format(sdk))
            self.cpp_info.components[sdk].requires = ["core"]
            if sdk in self._internal_requirements:
                self.cpp_info.components[sdk].requires.extend(self._internal_requirements[sdk])
            self.cpp_info.components[sdk].libs = ["aws-cpp-sdk-" + sdk]

            # TODO: to remove in conan v2 once cmake_find_package_* generators removed
            self.cpp_info.components[sdk].names["cmake_find_package"] = "aws-sdk-cpp-" + sdk
            self.cpp_info.components[sdk].names["cmake_find_package_multi"] = "aws-sdk-cpp-" + sdk
            component_alias = "aws-sdk-cpp-{}_alias".format(
                sdk
            )  # to emulate COMPONENTS names for find_package()
            self.cpp_info.components[component_alias].names["cmake_find_package"] = sdk
            self.cpp_info.components[component_alias].names["cmake_find_package_multi"] = sdk
            self.cpp_info.components[component_alias].requires = [sdk]

        # specific system_libs, frameworks and requires of components
        if self.settings.os == "Windows":
            self.cpp_info.components["core"].system_libs.extend(
                ["winhttp", "wininet", "bcrypt", "userenv", "version", "ws2_32"]
            )
            if self.options.get_safe("text-to-speech"):
                self.cpp_info.components["text-to-speech"].system_libs.append("winmm")
        else:
            self.cpp_info.components["core"].requires.extend(["libcurl::curl", "openssl::openssl"])

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["core"].system_libs.append("atomic")
            if self.options.get_safe("text-to-speech"):
                self.cpp_info.components["text-to-speech"].requires.append("pulseaudio::pulseaudio")

        if is_apple_os(self):
            if self.options.get_safe("text-to-speech"):
                self.cpp_info.components["text-to-speech"].frameworks.append("CoreAudio")

        lib_stdcpp = stdcpp_library(self)
        if lib_stdcpp:
            self.cpp_info.components["core"].system_libs.append(lib_stdcpp)

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "AWSSDK"
        self.cpp_info.filenames["cmake_find_package_multi"] = "AWSSDK"
        self.cpp_info.names["cmake_find_package"] = "AWS"
        self.cpp_info.names["cmake_find_package_multi"] = "AWS"
        self.cpp_info.components["core"].names["cmake_find_package"] = "aws-sdk-cpp-core"
        self.cpp_info.components["core"].names["cmake_find_package_multi"] = "aws-sdk-cpp-core"

        self.cpp_info.components["plugin_scripts"].requires = ["core"]
        self.cpp_info.components["plugin_scripts"].builddirs.extend(
            [os.path.join(self._res_folder, "cmake"), os.path.join(self._res_folder, "toolchains")]
        )
        self.cpp_info.components["plugin_scripts"].build_modules.append(
            os.path.join(self._res_folder, "cmake", "sdk_plugin_conf.cmake")
        )
