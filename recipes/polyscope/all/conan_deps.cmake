find_package(glm REQUIRED CONFIG)
find_package(imgui REQUIRED CONFIG)
find_package(nlohmann_json REQUIRED CONFIG)

if(POLYSCOPE_BACKEND_OPENGL3_GLFW)
    find_package(glfw3 REQUIRED CONFIG)
    link_libraries(imgui::glfw)
endif()

if(POLYSCOPE_BACKEND_OPENGL3_GLFW OR POLYSCOPE_BACKEND_OPENGL3_EGL)
    find_package(glad REQUIRED CONFIG)
    link_libraries(imgui::opengl3)
endif()
