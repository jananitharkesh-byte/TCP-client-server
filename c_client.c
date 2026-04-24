#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "ws2_32.lib")

#define SERVER_IP "127.0.0.1"
#define SERVER_PORT 9000
#define BUFFER_SIZE 8192

int main() {
    WSADATA wsa;
    WSAStartup(MAKEWORD(2,2), &wsa);

    int sock;
    struct sockaddr_in server_addr;
    char buffer[BUFFER_SIZE];
    char filename[256];

    // 1. Create socket
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCKET) {
        printf("Socket creation failed\n");
        return 1;
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    server_addr.sin_addr.s_addr = inet_addr(SERVER_IP);

    // 2. Connect to server
    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        printf("Connection failed\n");
        closesocket(sock);
        WSACleanup();
        return 1;
    }

    printf("Connected to RFMP server at %s:%d\n", SERVER_IP, SERVER_PORT);

    // 3. Send Start-Packet (non-secured)
    snprintf(buffer, sizeof(buffer), "(SS, RFMP, v1.0, 0)");
    send(sock, buffer, strlen(buffer), 0);

    // 4. Receive CC packet
    int bytes_received = recv(sock, buffer, sizeof(buffer)-1, 0);
    if (bytes_received <= 0) {
        printf("Server did not respond.\n");
        closesocket(sock);
        WSACleanup();
        return 1;
    }
    buffer[bytes_received] = '\0';
    printf("Server: %s\n", buffer);

    // 5. Ask user for filename to read
    printf("Enter filename to read: ");
    scanf("%255s", filename);

    // 6. Send openRead command
    snprintf(buffer, sizeof(buffer), "(CM, openRead, %s)", filename);
    send(sock, buffer, strlen(buffer), 0);

    // 7. Receive file content from server
    bytes_received = recv(sock, buffer, sizeof(buffer)-1, 0);
    if (bytes_received <= 0) {
        printf("No response from server.\n");
        closesocket(sock);
        WSACleanup();
        return 1;
    }
    buffer[bytes_received] = '\0';
    printf("Server response:\n%s\n", buffer);

    // 8. Close connection
    send(sock, "(End)", 5, 0);
    closesocket(sock);
    printf("Connection closed.\n");

    WSACleanup();

    return 0;
}
