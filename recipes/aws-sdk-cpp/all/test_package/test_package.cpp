#include <AwsSdkCppPlugin.h>
#include <aws/core/Aws.h>
#include <memory>

int main() {
    using namespace Aws;
    SDKOptions options;
    InitAPI(options);
    AwsSdkCppPlugin Plugin;
    ShutdownAPI(options);
    return 0;
}
