#include <sycl/sycl.hpp>

int main() {
    sycl::queue q{sycl::default_selector_v, sycl::property::queue::in_order{}};
    q.submit([&](sycl::handler& cgh) {});
}
