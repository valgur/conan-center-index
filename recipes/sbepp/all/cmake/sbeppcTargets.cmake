if(NOT TARGET sbepp::sbeppc)
    find_program(SBEPP_SBEPPC_EXECUTABLE
        NAMES sbeppc
        PATHS ENV PATH
        NO_DEFAULT_PATH
    )
    if(SBEPP_SBEPPC_EXECUTABLE)
        get_filename_component(SBEPP_SBEPPC_EXECUTABLE "${SBEPP_SBEPPC_EXECUTABLE}" ABSOLUTE)
        add_executable(sbepp::sbeppc IMPORTED)
        set_property(TARGET sbepp::sbeppc PROPERTY IMPORTED_LOCATION ${SBEPP_SBEPPC_EXECUTABLE})
    endif()
endif()
