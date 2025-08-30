#include <ng-log/logging.h>
#include <iostream>

int main(int argc, char** argv) {
    nglog::InitializeLogging(argv[0]);
    LOG(INFO) << "It works";
}
