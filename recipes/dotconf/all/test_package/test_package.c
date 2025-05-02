#include <dotconf.h>

static const configoption_t options[] = {
	LAST_OPTION
};

int main() {
    dotconf_create("", options, NULL, CASE_INSENSITIVE);
}
