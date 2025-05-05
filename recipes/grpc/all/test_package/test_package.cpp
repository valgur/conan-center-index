#include <grpcpp/grpcpp.h>
#include "helloworld.grpc.pb.h"

int main() {
    helloworld::HelloRequest request;
    helloworld::HelloReply reply;
    helloworld::Greeter greeter;
    std::cout << "gPRC version: " << grpc::Version() << "\n";
}
