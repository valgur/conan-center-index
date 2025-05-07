#include <asio.hpp>

int main()
{
	auto && service = asio::io_context{};
	(void)service;
}
