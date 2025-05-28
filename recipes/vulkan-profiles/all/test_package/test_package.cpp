#include <vulkan/vulkan_profiles.hpp>

int main()
{
    VpCapabilities capabilities = VK_NULL_HANDLE;
    VpCapabilitiesCreateInfo createInfo;
    createInfo.apiVersion = VK_API_VERSION_1_1;
    createInfo.flags = VP_PROFILE_CREATE_STATIC_BIT;
    createInfo.pVulkanFunctions = nullptr;
    vpCreateCapabilities(&createInfo, nullptr, &capabilities);
}
