#include <oneapi/dpl/algorithm>
#include <oneapi/dpl/execution>
#include <vector>

int main() {
    std::vector<int> data(10000000);
    auto policy = oneapi::dpl::execution::par_unseq;
    std::fill_n(policy, data.begin(), data.size(), -1);

    return 0;
}
