import hashlib
import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    export_conandata_patches,
    get,
    load,
)

required_conan_version = ">=1.60.0"


port_include_directories = {
    "BCC_16BIT_DOS_FLSH186": [
        os.path.join("BCC", "16BitDOS", "common"),
        os.path.join("BCC", "16BitDOS", "Flsh186"),
    ],
    "BCC_16BIT_DOS_PC": [
        os.path.join("BCC", "16BitDOS", "common"),
        os.path.join("BCC", "16BitDOS", "PC"),
    ],
    "CCS_ARM_CM3": [os.path.join("CCS", "ARM_CM3")],
    "CCS_ARM_CM4F": [os.path.join("CCS", "ARM_CM4F")],
    "CCS_ARM_CR4": [os.path.join("CCS", "ARM_Cortex-R4")],
    "CCS_MSP430X": [os.path.join("CCS", "MSP430X")],
    "CODEWARRIOR_COLDFIRE_V1": [os.path.join("CodeWarrior", "ColdFire_V1")],
    "CODEWARRIOR_COLDFIRE_V2": [os.path.join("CodeWarrior", "ColdFire_V2")],
    "CODEWARRIOR_HCS12": [os.path.join("CodeWarrior", "HCS12")],
    "GCC_ARM_CA9": [os.path.join("GCC", "ARM_CA9")],
    "GCC_Arm_AARCH64": [os.path.join("GCC", "Arm_AARCH64")],
    "GCC_Arm_AARCH64_SRE": [os.path.join("GCC", "Arm_AARCH64_SRE")],
    "GCC_ARM_CM0": [os.path.join("GCC", "ARM_CM0")],
    "GCC_ARM_CM3": [os.path.join("GCC", "ARM_CM3")],
    "GCC_ARM_CM3_MPU": [os.path.join("GCC", "ARM_CM3_MPU")],
    "GCC_ARM_CM4_MPU": [os.path.join("GCC", "ARM_CM4_MPU")],
    "GCC_ARM_CM4F": [os.path.join("GCC", "ARM_CM4F")],
    "GCC_ARM_CM7": [os.path.join("GCC", "ARM_CM7", "r0p1")],
    "GCC_ARM_CM23_NONSECURE": [os.path.join("GCC", "ARM_CM23", "non_secure")],
    "GCC_ARM_CM23_SECURE": [os.path.join("GCC", "ARM_CM23", "secure")],
    "GCC_ARM_CM23_NTZ_NONSECURE": [os.path.join("GCC", "ARM_CM23_NTZ", "non_secure")],
    "GCC_ARM_CM33_NONSECURE": [os.path.join("GCC", "ARM_CM33", "non_secure")],
    "GCC_ARM_CM33_SECURE": [os.path.join("GCC", "ARM_CM33", "secure")],
    "GCC_ARM_CM33_NTZ_NONSECURE": [os.path.join("GCC", "ARM_CM33_NTZ", "non_secure")],
    "GCC_ARM_CM33_TFM": [os.path.join("GCC", "ARM_CM33_NTZ", "non_secure")],
    "GCC_ARM_CM35P_NONSECURE": [os.path.join("GCC", "ARM_CM35P", "non_secure")],
    "GCC_ARM_CM35P_SECURE": [os.path.join("GCC", "ARM_CM35P", "secure")],
    "GCC_ARM_CM35P_NTZ_NONSECURE": [os.path.join("GCC", "ARM_CM35P_NTZ", "non_secure")],
    "GCC_ARM_CM55_NONSECURE": [os.path.join("GCC", "ARM_CM55", "non_secure")],
    "GCC_ARM_CM55_SECURE": [os.path.join("GCC", "ARM_CM55", "secure")],
    "GCC_ARM_CM55_NTZ_NONSECURE": [os.path.join("GCC", "ARM_CM55_NTZ", "non_secure")],
    "GCC_ARM_CM55_TFM": [os.path.join("GCC", "ARM_CM55_NTZ", "non_secure")],
    "GCC_ARM_CM85_NONSECURE": [os.path.join("GCC", "ARM_CM85", "non_secure")],
    "GCC_ARM_CM85_SECURE": [os.path.join("GCC", "ARM_CM85", "secure")],
    "GCC_ARM_CM85_NTZ_NONSECURE": [os.path.join("GCC", "ARM_CM85_NTZ", "non_secure")],
    "GCC_ARM_CM85_TFM": [os.path.join("GCC", "ARM_CM85_NTZ", "non_secure")],
    "GCC_ARM_CR5": [os.path.join("GCC", "ARM_CR5")],
    "GCC_ARM_CRX_MPU": [os.path.join("GCC", "ARM_CRx_MPU")],
    "GCC_ARM_CRX_NOGIC": [os.path.join("GCC", "ARM_CRx_No_GIC")],
    "GCC_ARM7_AT91FR40008": [os.path.join("GCC", "ARM7_AT91FR40008")],
    "GCC_ARM7_AT91SAM7S": [os.path.join("GCC", "ARM7_AT91SAM7S")],
    "GCC_ARM7_LPC2000": [os.path.join("GCC", "ARM7_LPC2000")],
    "GCC_ARM7_LPC23XX": [os.path.join("GCC", "ARM7_LPC23xx")],
    "GCC_ATMEGA323": [os.path.join("GCC", "ATMega323")],
    "GCC_AVR32_UC3": [os.path.join("GCC", "AVR32_UC3")],
    "GCC_COLDFIRE_V2": [os.path.join("GCC", "ColdFire_V2")],
    "GCC_CORTUS_APS3": [os.path.join("GCC", "CORTUS_APS3")],
    "GCC_H8S2329": [os.path.join("GCC", "H8S2329")],
    "GCC_HCS12": [os.path.join("GCC", "HCS12")],
    "GCC_IA32_FLAT": [os.path.join("GCC", "IA32_flat")],
    "GCC_MICROBLAZE": [os.path.join("GCC", "MicroBlaze")],
    "GCC_MICROBLAZE_V8": [os.path.join("GCC", "MicroBlazeV8")],
    "GCC_MICROBLAZE_V9": [os.path.join("GCC", "MicroBlazeV9")],
    "GCC_MSP430F449": [os.path.join("GCC", "MSP430F449")],
    "GCC_NIOSII": [os.path.join("GCC", "NiosII")],
    "GCC_PPC405_XILINX": [os.path.join("GCC", "PPC405_Xilinx")],
    "GCC_PPC440_XILINX": [os.path.join("GCC", "PPC440_Xilinx")],
    "GCC_RISC_V": [
        os.path.join("GCC", "RISC-V"),
        os.path.join(
            "GCC",
            "RISC-V",
            "chip_specific_extensions",
            "RISCV_MTIME_CLINT_no_extensions",
        ),
    ],
    "GCC_RISC_V_PULPINO_VEGA_RV32M1RM": [
        os.path.join("GCC", "RISC-V"),
        os.path.join(
            "GCC", "RISC-V", "chip_specific_extensions", "Pulpino_Vega_RV32M1RM"
        ),
    ],
    "GCC_RISC_V_GENERIC": [
        os.path.join("GCC", "RISC-V"),
    ],
    "GCC_RL78": [os.path.join("GCC", "RL78")],
    "GCC_RX100": [os.path.join("GCC", "RX100")],
    "GCC_RX200": [os.path.join("GCC", "RX200")],
    "GCC_RX600": [os.path.join("GCC", "RX600")],
    "GCC_RX600_V2": [os.path.join("GCC", "RX600v2")],
    "GCC_RX700_V3_DPFPU": [os.path.join("GCC", "RX700v3_DPFPU")],
    "GCC_STR75X": [os.path.join("GCC", "STR75x")],
    "GCC_TRICORE_1782": [os.path.join("GCC", "TriCore_1782STR75x")],
    "GCC_ARC_EM_HS": [os.path.join("ThirdParty", "GCC", "ARC_EM_HS")],
    "GCC_ARC_V1": [os.path.join("ThirdParty", "GCC", "ARC_v1")],
    "GCC_ATMEGA": [os.path.join("ThirdParty", "GCC", "ATmega")],
    "GCC_POSIX": [
        os.path.join("ThirdParty", "GCC", "Posix"),
        os.path.join("ThirdParty", "GCC", "Posix", "utils"),
    ],
    "GCC_RP2040": [os.path.join("ThirdParty", "GCC", "RP2040", "include")],
    "GCC_XTENSA_ESP32": [
        os.path.join("ThirdParty", "GCC", "Xtensa_ESP32"),
        os.path.join("ThirdParty", "GCC", "Xtensa_ESP32", "include"),
    ],
    "GCC_AVRDX": [
        os.path.join("ThirdParty", "Partner-Supported-Ports", "GCC", "AVR_AVRDx")
    ],
    "GCC_AVR_MEGA0": [
        os.path.join("ThirdParty", "Partner-Supported-Ports", "GCC", "AVR_Mega0")
    ],
    "IAR_78K0K": [os.path.join("IAR", "78K0R")],
    "IAR_ARM_CA5_NOGIC": [os.path.join("IAR", "ARM_CA5_No_GIC")],
    "IAR_ARM_CA9": [os.path.join("IAR", "ARM_CA9")],
    "IAR_ARM_CM0": [os.path.join("IAR", "ARM_CM0")],
    "IAR_ARM_CM3": [os.path.join("IAR", "ARM_CM3")],
    "IAR_ARM_CM4F": [os.path.join("IAR", "ARM_CM4F")],
    "IAR_ARM_CM4F_MPU": [os.path.join("IAR", "ARM_CM4F_MPU")],
    "IAR_ARM_CM7": [os.path.join("IAR", "ARM_CM7", "r0p1")],
    "IAR_ARM_CM23_NONSECURE": [os.path.join("IAR", "ARM_CM23", "non_secure")],
    "IAR_ARM_CM23_SECURE": [os.path.join("IAR", "ARM_CM23", "secure")],
    "IAR_ARM_CM23_NTZ_NONSECURE": [os.path.join("IAR", "ARM_CM23_NTZ", "non_secure")],
    "IAR_ARM_CM33_NONSECURE": [os.path.join("IAR", "ARM_CM33", "non_secure")],
    "IAR_ARM_CM33_SECURE": [os.path.join("IAR", "ARM_CM33", "secure")],
    "IAR_ARM_CM33_NTZ_NONSECURE": [os.path.join("IAR", "ARM_CM33_NTZ", "non_secure")],
    "IAR_ARM_CM35P_NONSECURE": [os.path.join("IAR", "ARM_CM35P", "non_secure")],
    "IAR_ARM_CM35P_SECURE": [os.path.join("IAR", "ARM_CM35P", "secure")],
    "IAR_ARM_CM35P_NTZ_NONSECURE": [os.path.join("IAR", "ARM_CM35P_NTZ", "non_secure")],
    "IAR_ARM_CM55_NONSECURE": [os.path.join("IAR", "ARM_CM55", "non_secure")],
    "IAR_ARM_CM55_SECURE": [os.path.join("IAR", "ARM_CM55", "secure")],
    "IAR_ARM_CM55_NTZ_NONSECURE": [os.path.join("IAR", "ARM_CM55_NTZ", "non_secure")],
    "IAR_ARM_CM85_NONSECURE": [os.path.join("IAR", "ARM_CM85", "non_secure")],
    "IAR_ARM_CM85_SECURE": [os.path.join("IAR", "ARM_CM85", "secure")],
    "IAR_ARM_CM85_NTZ_NONSECURE": [os.path.join("IAR", "ARM_CM85_NTZ", "non_secure")],
    "IAR_ARM_CRX_NOGIC": [os.path.join("IAR", "ARM_CRx_No_GIC")],
    "IAR_ATMEGA323": [os.path.join("IAR", "ATMega323")],
    "IAR_ATMEL_SAM7S64": [os.path.join("IAR", "AtmelSAM7S64")],
    "IAR_ATMEL_SAM9XE": [os.path.join("IAR", "AtmelSAM9XE")],
    "IAR_AVR_AVRDX": [os.path.join("IAR", "AVR_AVRDx")],
    "IAR_AVR_MEGA0": [os.path.join("IAR", "AVR_Mega0")],
    "IAR_AVR32_UC3": [os.path.join("IAR", "AVR32_UC3")],
    "IAR_LPC2000": [os.path.join("IAR", "LPC2000")],
    "IAR_MSP430": [os.path.join("IAR", "MSP430")],
    "IAR_MSP430X": [os.path.join("IAR", "MSP430X")],
    "IAR_RISC_V": [
        os.path.join("IAR", "RISC-V"),
        os.path.join(
            "IAR", "RISC-V", "chip_specific_extensions", "RV32I_CLINT_no_extensions"
        ),
    ],
    "IAR_RISC_V_GENERIC": [
        os.path.join("IAR", "RISC-V"),
    ],
    "IAR_RL78": [os.path.join("IAR", "RL78")],
    "IAR_RX100": [os.path.join("IAR", "RX100")],
    "IAR_RX600": [os.path.join("IAR", "RX600")],
    "IAR_RX700_V3_DPFPU": [os.path.join("IAR", "RX700v3_DPFPU")],
    "IAR_RX_V2": [os.path.join("IAR", "RXv2")],
    "IAR_STR71X": [os.path.join("IAR", "STR71x")],
    "IAR_STR75X": [os.path.join("IAR", "STR75x")],
    "IAR_STR91X": [os.path.join("IAR", "STR91x")],
    "IAR_V850ES_FX3": [os.path.join("IAR", "V850ES")],
    "IAR_V850ES_HX3": [os.path.join("IAR", "V850ES")],
    "MIKROC_ARM_CM4F": [os.path.join("MikroC", "ARM_CM4F")],
    "MPLAB_PIC18F": [os.path.join("MPLAB", "PIC18F")],
    "MPLAB_PIC24": [os.path.join("MPLAB", "PIC24_dsPIC")],
    "MPLAB_PIC32MEC14XX": [os.path.join("MPLAB", "PIC32MEC14xx")],
    "MPLAB_PIC32MX": [os.path.join("MPLAB", "PIC32MX")],
    "MPLAB_PIC32MZ": [os.path.join("MPLAB", "PIC32MZ")],
    "MSVC_MINGW": ["MSVC-MingW"],
    "OWATCOM_16BIT_DOS_FLSH186": [
        os.path.join("oWatcom", "16BitDOS", "common"),
        os.path.join("oWatcom", "16BitDOS", "Flsh186"),
    ],
    "OWATCOM_16BIT_DOS_PC": [
        os.path.join("oWatcom", "16BitDOS", "common"),
        os.path.join("oWatcom", "16BitDOS", "PC"),
    ],
    "PARADIGM_TERN_EE_LARGE": [os.path.join("Paradigm", "Tern_EE", "large_untested")],
    "PARADIGM_TERN_EE_SMALL": [os.path.join("Paradigm", "Tern_EE", "small")],
    "RENESAS_RX100": [os.path.join("Renesas", "RX100")],
    "RENESAS_RX200": [os.path.join("Renesas", "RX200")],
    "RENESAS_RX600": [os.path.join("Renesas", "RX600")],
    "RENESAS_RX600_V2": [os.path.join("Renesas", "RX600v2")],
    "RENESAS_RX700_V3_DPFPU": [os.path.join("Renesas", "RX700v3_DPFPU")],
    "RENESAS_SH2A_FPU": [os.path.join("Renesas", "SH2A_FPU")],
    "ROWLEY_MSP430F449": [os.path.join("Rowley", "MSP430F449")],
    "RVDS_ARM_CA9": [os.path.join("RVDS", "ARM_CA9")],
    "RVDS_ARM_CM0": [os.path.join("RVDS", "ARM_CM0")],
    "RVDS_ARM_CM3": [os.path.join("RVDS", "ARM_CM3")],
    "RVDS_ARM_CM4_MPU": [os.path.join("RVDS", "ARM_CM4_MPU")],
    "RVDS_ARM_CM4F": [os.path.join("RVDS", "ARM_CM4F")],
    "RVDS_ARM_CM7": [os.path.join("RVDS", "ARM_CM7", "r0p1")],
    "RVDS_ARM7_LPC21XX": [os.path.join("RVDS", "ARM7_LPC21xx")],
    "SDCC_CYGNAL": [os.path.join("SDCC", "Cygnal")],
    "SOFTUNE_MB91460": [os.path.join("Softune", "MB91460")],
    "SOFTUNE_MB96340": [os.path.join("Softune", "MB96340")],
    "TASKING_ARM_CM4F": [os.path.join("Tasking", "ARM_CM4F")],
    "TEMPLATE": ["template"],
    "CDK_THEAD_CK802": [os.path.join("ThirdParty", "CDK", "T-HEAD_CK802")],
    "XCC_XTENSA": [os.path.join("ThirdParty", "XCC", "Xtensa")],
    "WIZC_PIC18": [os.path.join("WizC", "PIC18")],
}


class FreeRTOSKernelConan(ConanFile):
    name = "freertos-kernel"
    description = "The FreeRTOS Kernel library"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.freertos.org/"
    license = "MIT"
    settings = "os", "arch", "compiler", "build_type"
    topics = ("freertos", "realtime", "rtos")
    package_type = "library"
    short_paths = True
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
        "port": [
            "A_CUSTOM_PORT",
            "BCC_16BIT_DOS_FLSH186",
            "BCC_16BIT_DOS_PC",
            "CCS_ARM_CM3",
            "CCS_ARM_CM4F",
            "CCS_ARM_CR4",
            "CCS_MSP430X",
            "CODEWARRIOR_COLDFIRE_V1",
            "CODEWARRIOR_COLDFIRE_V2",
            "CODEWARRIOR_HCS12",
            "GCC_ARM_CA9",
            "GCC_Arm_AARCH64",
            "GCC_Arm_AARCH64_SRE",
            "GCC_ARM_CM0",
            "GCC_ARM_CM3",
            "GCC_ARM_CM3_MPU",
            "GCC_ARM_CM4_MPU",
            "GCC_ARM_CM4F",
            "GCC_ARM_CM7",
            "GCC_ARM_CM23_NONSECURE",
            "GCC_ARM_CM23_SECURE",
            "GCC_ARM_CM23_NTZ_NONSECURE",
            "GCC_ARM_CM33_NONSECURE",
            "GCC_ARM_CM33_SECURE",
            "GCC_ARM_CM33_NTZ_NONSECURE",
            "GCC_ARM_CM33_TFM",
            "GCC_ARM_CM35P_NONSECURE",
            "GCC_ARM_CM35P_SECURE",
            "GCC_ARM_CM35P_NTZ_NONSECURE",
            "GCC_ARM_CM55_NONSECURE",
            "GCC_ARM_CM55_SECURE",
            "GCC_ARM_CM55_NTZ_NONSECURE",
            "GCC_ARM_CM55_TFM",
            "GCC_ARM_CM85_NONSECURE",
            "GCC_ARM_CM85_SECURE",
            "GCC_ARM_CM85_NTZ_NONSECURE",
            "GCC_ARM_CM85_TFM",
            "GCC_ARM_CR5",
            "GCC_ARM_CRX_MPU",
            "GCC_ARM_CRX_NOGIC",
            "GCC_ARM7_AT91FR40008",
            "GCC_ARM7_AT91SAM7S",
            "GCC_ARM7_LPC2000",
            "GCC_ARM7_LPC23XX",
            "GCC_ATMEGA323",
            "GCC_AVR32_UC3",
            "GCC_COLDFIRE_V2",
            "GCC_CORTUS_APS3",
            "GCC_H8S2329",
            "GCC_HCS12",
            "GCC_IA32_FLAT",
            "GCC_MICROBLAZE",
            "GCC_MICROBLAZE_V8",
            "GCC_MICROBLAZE_V9",
            "GCC_MSP430F449",
            "GCC_NIOSII",
            "GCC_PPC405_XILINX",
            "GCC_PPC440_XILINX",
            "GCC_RISC_V",
            "GCC_RISC_V_PULPINO_VEGA_RV32M1RM",
            "GCC_RISC_V_GENERIC",
            "GCC_RL78",
            "GCC_RX100",
            "GCC_RX200",
            "GCC_RX600",
            "GCC_RX600_V2",
            "GCC_RX700_V3_DPFPU",
            "GCC_STR75X",
            "GCC_TRICORE_1782",
            "GCC_ARC_EM_HS",
            "GCC_ARC_V1",
            "GCC_ATMEGA",
            "GCC_POSIX",
            "GCC_RP2040",
            "GCC_XTENSA_ESP32",
            "GCC_AVRDX",
            "GCC_AVR_MEGA0",
            "IAR_78K0K",
            "IAR_ARM_CA5_NOGIC",
            "IAR_ARM_CA9",
            "IAR_ARM_CM0",
            "IAR_ARM_CM3",
            "IAR_ARM_CM4F",
            "IAR_ARM_CM4F_MPU",
            "IAR_ARM_CM7",
            "IAR_ARM_CM23_NONSECURE",
            "IAR_ARM_CM23_SECURE",
            "IAR_ARM_CM23_NTZ_NONSECURE",
            "IAR_ARM_CM33_NONSECURE",
            "IAR_ARM_CM33_SECURE",
            "IAR_ARM_CM33_NTZ_NONSECURE",
            "IAR_ARM_CM35P_NONSECURE",
            "IAR_ARM_CM35P_SECURE",
            "IAR_ARM_CM35P_NTZ_NONSECURE",
            "IAR_ARM_CM55_NONSECURE",
            "IAR_ARM_CM55_SECURE",
            "IAR_ARM_CM55_NTZ_NONSECURE",
            "IAR_ARM_CM85_NONSECURE",
            "IAR_ARM_CM85_SECURE",
            "IAR_ARM_CM85_NTZ_NONSECURE",
            "IAR_ARM_CRX_NOGIC",
            "IAR_ATMEGA323",
            "IAR_ATMEL_SAM7S64",
            "IAR_ATMEL_SAM9XE",
            "IAR_AVR_AVRDX",
            "IAR_AVR_MEGA0",
            "IAR_AVR32_UC3",
            "IAR_LPC2000",
            "IAR_MSP430",
            "IAR_MSP430X",
            "IAR_RISC_V",
            "IAR_RISC_V_GENERIC",
            "IAR_RL78",
            "IAR_RX100",
            "IAR_RX600",
            "IAR_RX700_V3_DPFPU",
            "IAR_RX_V2",
            "IAR_STR71X",
            "IAR_STR75X",
            "IAR_STR91X",
            "IAR_V850ES_FX3",
            "IAR_V850ES_HX3",
            "MIKROC_ARM_CM4F",
            "MPLAB_PIC18F",
            "MPLAB_PIC24",
            "MPLAB_PIC32MEC14XX",
            "MPLAB_PIC32MX",
            "MPLAB_PIC32MZ",
            "MSVC_MINGW",
            "OWATCOM_16BIT_DOS_FLSH186",
            "OWATCOM_16BIT_DOS_PC",
            "PARADIGM_TERN_EE_LARGE",
            "PARADIGM_TERN_EE_SMALL",
            "RENESAS_RX100",
            "RENESAS_RX200",
            "RENESAS_RX600",
            "RENESAS_RX600_V2",
            "RENESAS_RX700_V3_DPFPU",
            "RENESAS_SH2A_FPU",
            "ROWLEY_MSP430F449",
            "RVDS_ARM_CA9",
            "RVDS_ARM_CM0",
            "RVDS_ARM_CM3",
            "RVDS_ARM_CM4_MPU",
            "RVDS_ARM_CM4F",
            "RVDS_ARM_CM7",
            "RVDS_ARM7_LPC21XX",
            "SDCC_CYGNAL",
            "SOFTUNE_MB91460",
            "SOFTUNE_MB96340",
            "TASKING_ARM_CM4F",
            "TEMPLATE",
            "CDK_THEAD_CK802",
            "XCC_XTENSA",
            "WIZC_PIC18",
        ],
        "risc_v_chip_extension": [
            "Pulpino_Vega_RV32M1RM",
            "RISCV_MTIME_CLINT_no_extensions",
            "RISCV_no_extensions",
            "RV32I_CLINT_no_extensions",
        ],
        "heap": ["1", "2", "3", "4", "5"],
        "config": [None, "ANY"],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
        "port": "GCC_POSIX",
        "heap": "4",
        "risc_v_chip_extension": "RISCV_no_extensions",
        "config": None,
    }

    def config_options(self):
        if self.settings.os in ["baremetal", "Windows"]:
            self.options.rm_safe("fPIC")
            self.options.port = "MSVC_MINGW"

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

        if self.options.port not in ["GCC_RISC_V_GENERIC", "IAR_RISC_V_GENERIC"]:
            self.options.rm_safe("risc_v_chip_extension")
        else:
            if self.options.port == "IAR_RISC_V_GENERIC":
                self.options.risc_v_chip_extension = "RV32I_CLINT_no_extensions"

    def package_id(self):
        if self.info.options.get_safe("config"):
            config_hash = hashlib.sha256(
                load(self, str(self.info.options.config)).encode("utf-8")
            )
            self.info.options.config = config_hash

    def validate(self):
        if (
            self.options.port == "IAR_RISC_V_GENERIC"
            and self.options.get_safe("risc_v_chip_extension")
            != "RV32I_CLINT_no_extensions"
        ):
            raise ConanInvalidConfiguration(
                "Only the RV32I_CLINT_no_extensions RISC-V extension can be enabled when using the IAR_RISC_V_GENERIC port"
            )

    def layout(self):
        cmake_layout(self, src_folder="src")

    def export_sources(self):
        export_conandata_patches(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["FREERTOS_HEAP"] = self.options.heap
        tc.variables["FREERTOS_PORT"] = self.options.port
        if self.options.get_safe("risc_v_chip_extension"):
            tc.variables["FREERTOS_RISCV_EXTENSION"] = (
                self.options.risc_v_chip_extension
            )
        tc.variables["_FREERTOS_CONFIG_DIR"] = self.build_folder.replace("\\", "/")
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        if self.options.get_safe("config"):
            copy(
                self,
                "FreeRTOSConfig.h",
                os.path.dirname(str(self.options.config)),
                self.build_folder,
                keep_path=False,
            )
        else:
            copy(
                self,
                "FreeRTOSConfig.h",
                os.path.join(self.source_folder, "examples", "template_configuration"),
                self.build_folder,
                keep_path=False,
            )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(
            self,
            "*.h",
            os.path.join(self.source_folder, "include"),
            os.path.join(self.package_folder, "include"),
            keep_path=False,
        )
        if self.options.get_safe("risc_v_chip_extension"):
            for risc_v_generic_port in ["GCC", "IAR"]:
                port_include_directories[
                    f"{risc_v_generic_port}_RISC_V_GENERIC"
                ].append(
                    os.path.join(
                        risc_v_generic_port,
                        "RISC-V",
                        "chip_specific_extensions",
                        str(self.options.risc_v_chip_extension),
                    )
                )
        for include_directory in port_include_directories[str(self.options.port)]:
            copy(
                self,
                "*.h",
                os.path.join(self.source_folder, "portable", include_directory),
                os.path.join(self.package_folder, "include"),
                keep_path=False,
            )
        copy(
            self,
            "*freertos_kernel.dll",
            self.build_folder,
            os.path.join(self.package_folder, "bin"),
        )
        copy(
            self,
            "*freertos_kernel.lib",
            self.build_folder,
            os.path.join(self.package_folder, "lib"),
        )
        copy(
            self,
            "*freertos_kernel.so*",
            self.build_folder,
            os.path.join(self.package_folder, "lib"),
        )
        copy(
            self,
            "*freertos_kernel.dylib",
            self.build_folder,
            os.path.join(self.package_folder, "lib"),
        )
        copy(
            self,
            "*freertos_kernel.a",
            self.build_folder,
            os.path.join(self.package_folder, "lib"),
        )
        copy(
            self,
            "LICENSE.md",
            self.source_folder,
            os.path.join(self.package_folder, "licenses"),
        )
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.libs = ["freertos_kernel"]

        if self.settings.os in ["FreeBSD", "Linux"]:
            self.cpp_info.system_libs.append("pthread")
