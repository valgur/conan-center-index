#include <simple-websocket-server/server_ws.hpp>
#include <simple-websocket-server/client_ws.hpp>

using WsServer = SimpleWeb::SocketServer<SimpleWeb::WS>;
using WsClient = SimpleWeb::SocketClient<SimpleWeb::WS>;

int main() {
    WsServer server;
    WsClient client("");
}
