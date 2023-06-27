#include <net-snmp/library/snmp_api.h>
#include <net-snmp/net-snmp-config.h>
#include <stddef.h>

int main(int argc, char const *argv[]) {
    (void)argc;
    (void)argv;

    netsnmp_free(NULL);

    return 0;
}
