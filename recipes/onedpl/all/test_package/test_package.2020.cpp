#include <pstl/algorithm>
#include <pstl/execution>
#include <vector>

int main() {
    std::vector<int> data(10000000);
    std::fill_n(pstl::execution::par_unseq, data.begin(), data.size(), -1);

    return 0;
}
