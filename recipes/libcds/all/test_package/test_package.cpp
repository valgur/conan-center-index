#include <cds/gc/hp.h>
#include <cds/init.h>

int main() {
    cds::Initialize();
    {
        cds::gc::HP hpGC;
        cds::threading::Manager::attachThread();
    }
    cds::Terminate();
    return 0;
}
