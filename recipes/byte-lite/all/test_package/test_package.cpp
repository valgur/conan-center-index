#include "nonstd/byte.hpp"

#include <stdexcept>

using namespace nonstd;

int main()
{
    byte b1{0x5a};
    byte b2{0xa5};

    byte r1 = b1 ^ b2; if( 0xff != to_integer<unsigned int>( r1 ) ) throw std::exception();
    byte r2 = b1 ^ b2; if( 0xff != to_integer<unsigned int>( r2 ) ) throw std::exception();
}
