#include <rapids_logger/logger.hpp>
#include <iostream>

int main() {
    rapids_logger::logger logger{"LOGGER_TEST", std::cout};
    logger.info("Hello World!");
}
