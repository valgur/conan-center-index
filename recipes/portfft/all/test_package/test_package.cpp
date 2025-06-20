#include <portfft/portfft.hpp>

int main() {
  constexpr portfft::domain domain = portfft::get_domain<float>::value;
  portfft::descriptor<float, domain> desc({16});
}
