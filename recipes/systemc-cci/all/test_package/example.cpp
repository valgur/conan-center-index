#include <cci_configuration>
#include <cci_utils/broker.h>

int sc_main() {
    cci::cci_register_broker(new cci_utils::broker("Global Broker"));
    return 0;
}
