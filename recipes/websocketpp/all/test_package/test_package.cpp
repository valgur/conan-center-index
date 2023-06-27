#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>

int main() { websocketpp::server<websocketpp::config::asio> server; }
