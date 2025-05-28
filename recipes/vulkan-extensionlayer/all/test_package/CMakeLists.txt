cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(VulkanLoader REQUIRED)

add_executable(check_vulkan_layers check_vulkan_layers.cpp)
target_link_libraries(check_vulkan_layers PRIVATE Vulkan::Loader)
