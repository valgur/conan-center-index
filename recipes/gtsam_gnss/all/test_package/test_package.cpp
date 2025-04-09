#include <gtsam_gnss/ClockFactor_CC.h>

int main() {
    auto noise = gtsam::noiseModel::Isotropic::Sigma(2, 1.0);
    gtsam_gnss::ClockFactor_CC clock_factor('a', 'b', noise);
}
