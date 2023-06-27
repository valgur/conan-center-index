#if defined(_WIN32)
#define NOMINMAX
#endif
#include <amqpcpp.h>

#include <iostream>
#include <string>

int main() {
    const std::string s = "Hello, World!";
    AMQP::ByteBuffer buffer(s.data(), s.size());
    if (buffer.size() == 13)
        std::cout << "Done" << std::endl;
    else
        std::cout << "Wrong buffer of " << buffer.size() << std::endl;
    return 0;
}
