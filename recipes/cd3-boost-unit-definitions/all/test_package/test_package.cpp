#include <BoostUnitDefinitions/Units.hpp>
#include <cstdlib>
#include <iostream>

using namespace boost;
using namespace boost::units;

int main(void) {

    quantity<t::m> x = 2.5 * i::m;
    std::cout << x << " == " << quantity<t::in>(x) << std::endl;

    return EXIT_SUCCESS;
}
