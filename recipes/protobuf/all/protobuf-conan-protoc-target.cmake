if(NOT TARGET protobuf::protoc)
    find_program(PROTOC_PROGRAM NAMES protoc PATHS ENV PATH NO_DEFAULT_PATH)
    get_filename_component(PROTOC_PROGRAM "${PROTOC_PROGRAM}" ABSOLUTE)
    # Give opportunity to users to provide an external protoc executable
    # (this is a feature of official FindProtobuf.cmake)
    set(Protobuf_PROTOC_EXECUTABLE ${PROTOC_PROGRAM} CACHE FILEPATH "The protoc compiler")
    add_executable(protobuf::protoc IMPORTED)
    set_property(TARGET protobuf::protoc PROPERTY IMPORTED_LOCATION ${Protobuf_PROTOC_EXECUTABLE})
endif()
