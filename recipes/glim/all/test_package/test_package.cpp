#include <glim/common/imu_integration.hpp>

#include <iostream>

int main() {
    glim::IMUIntegration imu_integration;
    std::cout << "Number of IMU values in queue: " << imu_integration.imu_data_in_queue().size() << std::endl;
}
