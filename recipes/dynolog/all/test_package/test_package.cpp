#include <glog/logging.h>
#include <dynolog/src/ipcfabric/FabricManager.h>

int main() {
    auto manger = dynolog::ipcfabric::FabricManager::factory();
}
