#include <rmm/mr/device/cuda_async_memory_resource.hpp>

int main()
{
    rmm::mr::cuda_async_memory_resource mr{rmm::percent_of_free_device_memory(1)};
}
