#include <gudev/gudev.h>

int main()
{
	const gchar *subsystems[] = { NULL };
	GUdevClient *client = g_udev_client_new(subsystems);
}
