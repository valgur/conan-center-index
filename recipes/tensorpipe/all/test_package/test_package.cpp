#include <tensorpipe/tensorpipe.h>
#ifdef TP_WITH_CUDA
#include <tensorpipe/tensorpipe_cuda.h>
#endif

#include <memory>

int main() {
    auto context = std::make_shared<tensorpipe::Context>();
    context->registerTransport(0, "uv", tensorpipe::transport::uv::create());
    return 0;
}
