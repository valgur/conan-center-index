if(NOT TARGET flatbuffers::flatc)
    find_program(FLATBUFFERS_FLATC_EXECUTABLE
        NAMES flatc
        PATHS ENV PATH
        NO_DEFAULT_PATH
    )
    if(FLATBUFFERS_FLATC_EXECUTABLE)
        get_filename_component(FLATBUFFERS_FLATC_EXECUTABLE "${FLATBUFFERS_FLATC_EXECUTABLE}" ABSOLUTE)
        add_executable(flatbuffers::flatc IMPORTED)
        set_property(TARGET flatbuffers::flatc PROPERTY IMPORTED_LOCATION ${FLATBUFFERS_FLATC_EXECUTABLE})
    endif()
endif()
