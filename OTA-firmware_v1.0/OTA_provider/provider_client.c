#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define BUF_SIZE 1024

void error_handling(char *message) {
    perror(message);
    exit(1);
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        fprintf(stderr, "Usage: %s <IP> <PORT> <DEVICE_NAME> <FILE_PATH>\n", argv[0]);
        exit(1);
    }

    char *ip_address = argv[1];
    int port = atoi(argv[2]);
    char *device_name = argv[3];
    char *file_path = realpath(argv[4], NULL);

    if (file_path == NULL) {
        error_handling("Invalid file path");
    }

    char *file_name = strrchr(file_path, '/');
    if (file_name == NULL) {
        file_name = file_path;
    } else {
        file_name++; // Skip the '/'
    }

    int sock;
    struct sockaddr_in server_addr;
    char buffer[BUF_SIZE];
    FILE *fp;

    sock = socket(PF_INET, SOCK_STREAM, 0);
    if (sock == -1) {
        error_handling("socket() error");
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = inet_addr(ip_address);
    server_addr.sin_port = htons(port);

    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) == -1) {
        error_handling("connect() error");
    }

    // Send device name length and device name
    uint32_t device_name_len = strlen(device_name);
    device_name_len = htonl(device_name_len); // Ensure network byte order
    if (write(sock, &device_name_len, sizeof(device_name_len)) != sizeof(device_name_len)) {
        error_handling("write() error: failed to send device name length");
    }

    if (write(sock, device_name, ntohl(device_name_len)) != ntohl(device_name_len)) {
        error_handling("write() error: failed to send device name");
    }

    // Send filename length and filename
    uint32_t file_name_len = strlen(file_name);
    file_name_len = htonl(file_name_len); // Ensure network byte order
    if (write(sock, &file_name_len, sizeof(file_name_len)) != sizeof(file_name_len)) {
        error_handling("write() error: failed to send filename length");
    }

    if (write(sock, file_name, ntohl(file_name_len)) != ntohl(file_name_len)) {
        error_handling("write() error: failed to send filename");
    }

    // Send the file data
    fp = fopen(file_path, "rb");
    if (fp == NULL) {
        error_handling("fopen() error");
    }

    int read_len;
    while ((read_len = fread(buffer, 1, BUF_SIZE, fp)) > 0) {
        if (write(sock, buffer, read_len) != read_len) {
            error_handling("write() error: failed to send file data");
        }
    }

    fclose(fp);
    close(sock);
    free(file_path);
    return 0;
}
