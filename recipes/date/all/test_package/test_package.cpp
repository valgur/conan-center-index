#include <date/date.h>
#include <date/tz.h>

#include <iostream>

int main() {
    using namespace date;
    auto date1 = 2015_y / March / 22;

#ifndef DATE_HEADER_ONLY
    try {
        auto tz = date::current_zone()->name();
        std::cout << "timezone: " << tz << std::endl;
    } catch (const std::exception &e) {
        std::cout << "exception caught " << e.what() << std::endl;
    }
#endif
}
