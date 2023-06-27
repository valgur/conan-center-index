#include <cpprest/containerstream.h>
#include <cpprest/filestream.h>
#include <was/blob.h>
#include <was/storage_account.h>

int main() {
    // Define the connection-string with your values.// Define the connection-string with Azurite.
    const utility::string_t storage_connection_string(U("UseDevelopmentStorage=true;"));
    // Retrieve storage account from connection string.
    azure::storage::cloud_storage_account storage_account =
        azure::storage::cloud_storage_account::parse(storage_connection_string);
}
