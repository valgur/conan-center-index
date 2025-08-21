#include <stdexec/execution.hpp>
#include <exec/static_thread_pool.hpp>

int main() {
  exec::static_thread_pool ctx{8};
}
