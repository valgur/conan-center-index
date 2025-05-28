// Enumerate all Vulkan instance layers and optionally check
// that the ones passed as command line arguments are found.

#include <vulkan/vulkan.h>
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>


int main(int argc, char* argv[]) {
    uint32_t layerCount;
    vkEnumerateInstanceLayerProperties(&layerCount, nullptr);
    std::vector<VkLayerProperties> availableLayers(layerCount);
    vkEnumerateInstanceLayerProperties(&layerCount, availableLayers.data());

    std::cout << "Available Vulkan Instance Layers:" << std::endl;
    for (const auto& layer : availableLayers) {
        std::cout << "  " << layer.layerName << std::endl;
    }

    bool allLayersFound = true;
    for (int i = 1; i < argc; ++i) {
        std::string expectedLayer = argv[i];
        bool layerFound = false;
        for (const auto& layer : availableLayers) {
            if (layer.layerName == expectedLayer) {
                layerFound = true;
                break;
            }
        }
        if (!layerFound) {
            std::cerr << "Error: " << expectedLayer << " not found among available layers!" << std::endl;
            allLayersFound = false;
        } else {
            std::cout << "Found expected layer: " << expectedLayer << std::endl;
        }
    }

    return allLayersFound ? 0 : 1;
}
