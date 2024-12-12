/*#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <netdb.h>
#include <sys/stat.h>
#include <errno.h>
#include <sys/time.h>

#define MAX_SIZE 1032
#define RECEIVED_FILE_PATH "/OTA/Delta_packages/received.patch"
#define TIMEOUT_SECONDS 5 

#pragma pack(1) // Ensure no padding in the struct
typedef struct {
    unsigned int upSize;
    char fileName[MAX_SIZE];
} updatePackageConfig;
#pragma pack(0)

void error(const char *msg) {
    perror(msg);
    exit(1);
}

FILE *checkFileExistWrite() {
    // Create the directory if it doesn't exist
    if (mkdir("/OTA", 0755) && errno != EEXIST) {
        perror("Cannot create /OTA directory");
        return NULL;
    }
    if (mkdir("/OTA/Delta_packages", 0755) && errno != EEXIST) {
        perror("Cannot create /OTA/Delta_packages directory");
        return NULL;
    }

    FILE *fp;
    if ((fp = fopen(RECEIVED_FILE_PATH, "wb")) != NULL) {
        return fp;
    } else {
        perror("Cannot open PatchFile for writing");
        return NULL;
    }
}

int main(int argc, char *argv[]) {
    int sockfd;
    char Buffer[MAX_SIZE];
    struct sockaddr_in serverAddress;
    struct hostent *server;

    if (argc < 3) {
        fprintf(stderr, "Usage: %s <hostname> <port>\n", argv[0]);
        exit(1);
    }

    FILE *fd_UP = checkFileExistWrite();
    if (fd_UP == NULL) {
        exit(1);
    }

    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        error("Socket creation failed");
    }

    server = gethostbyname(argv[1]);
    if (server == NULL) {
        fprintf(stderr, "No such host\n");
        exit(1);
    }

    bzero((char *)&serverAddress, sizeof(serverAddress));
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_port = htons(atoi(argv[2]));
    bcopy((char *)server->h_addr, (char *)&serverAddress.sin_addr.s_addr, server->h_length);

    if (connect(sockfd, (struct sockaddr *)&serverAddress, sizeof(serverAddress)) < 0) {
        error("Connection failed");
    }

    printf("Connected to server %s:%s\n", argv[1], argv[2]);

    printf("Receiving update package configuration from server...\n");
    bzero(Buffer, sizeof(Buffer));
    int n = recv(sockfd, Buffer, sizeof(updatePackageConfig), 0);
    if (n < 0) {
        error("Error receiving from server");
    } else if (n == 0) {
        printf("Connection closed by server\n");
        close(sockfd);
        fclose(fd_UP);
        exit(0);
    }

    updatePackageConfig config;
    memcpy(&config, Buffer, sizeof(updatePackageConfig));

    // Validate the received configuration
    printf("Received package configuration:\n");
    printf("File Name: %s\n", config.fileName);
    printf("File Size: %u bytes\n", config.upSize);

    unsigned int fileSize = config.upSize;

    if (fileSize == 0 || fileSize > 1073741824) { // Sanity check for file size (max 1GB)
        printf("Invalid file size received: %u, exiting\n", fileSize);
        close(sockfd);
        fclose(fd_UP);
        exit(0);
    }

    printf("Receiving patch file: %s, size: %u bytes\n", config.fileName, fileSize);

    // Allocate buffer for the entire file
    char *fileBuffer = malloc(fileSize);
    if (fileBuffer == NULL) {
        perror("Failed to allocate memory");
        close(sockfd);
        fclose(fd_UP);
        exit(1);
    }

    struct timeval timeout;
    timeout.tv_sec = TIMEOUT_SECONDS;
    timeout.tv_usec = 0;
    fd_set read_fds;

    unsigned int bytesReceived = 0;
    while (bytesReceived < fileSize) {
        FD_ZERO(&read_fds);
        FD_SET(sockfd, &read_fds);

        int activity = select(sockfd + 1, &read_fds, NULL, NULL, &timeout);

        if (activity == -1) {
            perror("select() failed");
            free(fileBuffer);
            close(sockfd);
            fclose(fd_UP);
            exit(1);
        } else if (activity == 0) {
            printf("No data received for %d seconds, assuming file is fully received for testing purposes\n", TIMEOUT_SECONDS);
            break;
        } else {
            if (FD_ISSET(sockfd, &read_fds)) {
                n = recv(sockfd, fileBuffer + bytesReceived, fileSize - bytesReceived, 0);
                if (n < 0) {
                    perror("Error receiving from server");
                    free(fileBuffer);
                    close(sockfd);
                    fclose(fd_UP);
                    exit(1);
                } else if (n == 0) {
                    printf("Connection closed by server\n");
                    break;
                }
                bytesReceived += n;
                printf("Received %u/%u bytes\n", bytesReceived, fileSize); // Progress indicator
            }

            if (bytesReceived == fileSize) {
                fwrite(fileBuffer, 1, fileSize, fd_UP);
                fflush(fd_UP); // Ensure data is written to the file system
                printf("Patch file received successfully\n");

                // Execute Client_GUI1.py with the appropriate command
                printf("Executing client_ui.py...\n");
                if (system("python3 client_ui.py") == -1) {
                    perror("Error executing client_ui.py");
                }

            } else {
                printf("Incomplete file received. Expected: %u, Received: %u\n", fileSize, bytesReceived);
            }

            free(fileBuffer);
            close(sockfd);
            fclose(fd_UP);

            return 0;
        }
    }
}*/


/*#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define MAX_SIZE 1024

int main(int argc, char *argv[]) {
    int sockfd, portno;
    struct sockaddr_in serv_addr;
    unsigned int fileSize;
    char fileName[MAX_SIZE];
    char buffer[MAX_SIZE];
    FILE *file;

    if (argc < 3) {
        fprintf(stderr, "Usage: %s <server_ip> <port>\n", argv[0]);
        exit(1);
    }

    portno = atoi(argv[2]);
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("ERROR opening socket");
        exit(1);
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(portno);
    if (inet_pton(AF_INET, argv[1], &serv_addr.sin_addr) <= 0) {
        perror("ERROR invalid server IP");
        close(sockfd);
        exit(1);
    }

    if (connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        perror("ERROR connecting");
        close(sockfd);
        exit(1);
    }

    printf("Connected to server %s:%d\n", argv[1], portno);

    // Receive file size
    if (recv(sockfd, &fileSize, sizeof(fileSize), 0) <= 0) {
        perror("ERROR receiving file size");
        close(sockfd);
        exit(1);
    }
    printf("Received file size: %u bytes\n", fileSize);

    if (fileSize == 0) {
        fprintf(stderr, "Error: Received file size is 0 bytes. Exiting...\n");
        close(sockfd);
        exit(1);
    }

    // Receive file name (but we will ignore it for the saved filename)
    memset(fileName, 0, MAX_SIZE);
    if (recv(sockfd, fileName, sizeof(fileName), 0) <= 0) {
        perror("ERROR receiving file name");
        close(sockfd);
        exit(1);
    }

    // Open the file for writing at the specified path
    file = fopen("/OTA/Delta_packages/received_patch.patch", "wb");
    if (file == NULL) {
        perror("ERROR opening file");
        close(sockfd);
        exit(1);
    }

    // Receive file content
    int bytesReceived;
    unsigned int totalBytesReceived = 0;
    while (totalBytesReceived < fileSize) {
        bytesReceived = recv(sockfd, buffer, MAX_SIZE, 0);
        if (bytesReceived <= 0) {
            perror("ERROR receiving file content");
            fclose(file);
            close(sockfd);
            exit(1);
        }

        fwrite(buffer, 1, bytesReceived, file);
        totalBytesReceived += bytesReceived;
        printf("Received chunk of size: %d bytes, Total received: %u bytes\n", bytesReceived, totalBytesReceived);
    }

    printf("File received successfully and saved as: /OTA/Delta_packages/received_patch.patch\n");

    fclose(file);

    // Call the Python script immediately after the file is received
    printf("Executing Python script client_ui.py...\n");
    int result = system("python3 client_ui.py");  // Change the path as necessary

    if (result == -1) {
        perror("ERROR executing Python script");
        close(sockfd);
        exit(1);
    }

    printf("Python script executed successfully.\n");

    close(sockfd);
    return 0;
}*/


/*#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define MAX_SIZE 1024

int main(int argc, char *argv[]) {
    int sockfd, portno;
    struct sockaddr_in serv_addr;
    unsigned int fileSize;
    char fileName[MAX_SIZE];
    char buffer[MAX_SIZE];
    FILE *file;

    if (argc < 3) {
        fprintf(stderr, "Usage: %s <server_ip> <port>\n", argv[0]);
        exit(1);
    }

    portno = atoi(argv[2]);
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("ERROR opening socket");
        exit(1);
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(portno);
    if (inet_pton(AF_INET, argv[1], &serv_addr.sin_addr) <= 0) {
        perror("ERROR invalid server IP");
        close(sockfd);
        exit(1);
    }

    if (connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        perror("ERROR connecting");
        close(sockfd);
        exit(1);
    }

    printf("Connected to server %s:%d\n", argv[1], portno);

    // Receive file size
    if (recv(sockfd, &fileSize, sizeof(fileSize), 0) <= 0) {
        perror("ERROR receiving file size");
        close(sockfd);
        exit(1);
    }
    printf("Received file size: %u bytes\n", fileSize);

    if (fileSize == 0) {
        fprintf(stderr, "Error: Received file size is 0 bytes. Exiting...\n");
        close(sockfd);
        exit(1);
    }

    // Receive file name (but we will ignore it for the saved filename)
    memset(fileName, 0, MAX_SIZE);
    if (recv(sockfd, fileName, sizeof(fileName), 0) <= 0) {
        perror("ERROR receiving file name");
        close(sockfd);
        exit(1);
    }

    // Open the file for writing at the specified path
    file = fopen("/OTA/Delta_packages/received_patch.patch", "wb");
    if (file == NULL) {
        perror("ERROR opening file");
        close(sockfd);
        exit(1);
    }

    // Receive file content
    int bytesReceived;
    unsigned int totalBytesReceived = 0;
    while (totalBytesReceived < fileSize) {
        bytesReceived = recv(sockfd, buffer, MAX_SIZE, 0);
        if (bytesReceived <= 0) {
            perror("ERROR receiving file content");
            fclose(file);
            close(sockfd);
            exit(1);
        }

        fwrite(buffer, 1, bytesReceived, file);
        totalBytesReceived += bytesReceived;
        printf("Received chunk of size: %d bytes, Total received: %u bytes\n", bytesReceived, totalBytesReceived);
    }

    printf("File received successfully and saved as: /OTA/Delta_packages/received_patch.patch\n");

    fclose(file);

    // Call the Python script immediately after the file is received
    printf("Executing Python script client_ui.py...\n");
    int result = system("python3 /path/to/client_ui.py");  // Change the path as necessary

    if (result == -1) {
        perror("ERROR executing Python script");
        close(sockfd);
        exit(1);
    }

    printf("Python script executed successfully.\n");

    close(sockfd);
    return 0;
}*/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define MAX_SIZE 1024

int main(int argc, char *argv[]) {
    int sockfd, portno;
    struct sockaddr_in serv_addr;
    unsigned int fileSize;
    char fileName[MAX_SIZE];
    char buffer[MAX_SIZE];
    FILE *file;

    if (argc < 3) {
        fprintf(stderr, "Usage: %s <server_ip> <port>\n", argv[0]);
        exit(1);
    }

    portno = atoi(argv[2]);
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("ERROR opening socket");
        exit(1);
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(portno);
    if (inet_pton(AF_INET, argv[1], &serv_addr.sin_addr) <= 0) {
        perror("ERROR invalid server IP");
        close(sockfd);
        exit(1);
    }

    if (connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        perror("ERROR connecting");
        close(sockfd);
        exit(1);
    }

    printf("Connected to server %s:%d\n", argv[1], portno);

    // Receive file size
    if (recv(sockfd, &fileSize, sizeof(fileSize), 0) <= 0) {
        perror("ERROR receiving file size");
        close(sockfd);
        exit(1);
    }
    printf("Received file size: %u bytes\n", fileSize);

    if (fileSize == 0) {
        fprintf(stderr, "Error: Received file size is 0 bytes. Exiting...\n");
        close(sockfd);
        exit(1);
    }

    // Receive file name (but we will ignore it for the saved filename)
    memset(fileName, 0, MAX_SIZE);
    if (recv(sockfd, fileName, sizeof(fileName), 0) <= 0) {
        perror("ERROR receiving file name");
        close(sockfd);
        exit(1);
    }
    //printf("Received file name: %s (ignoring for local file storage)\n", fileName);

    // Open the file for writing at the specified path
    file = fopen("/OTA/Delta_packages/received_patch.patch", "wb");
    if (file == NULL) {
        perror("ERROR opening file");
        close(sockfd);
        exit(1);
    }

    // Receive file content
    int bytesReceived;
    unsigned int totalBytesReceived = 0;
    while (totalBytesReceived < fileSize) {
        bytesReceived = recv(sockfd, buffer, MAX_SIZE, 0);
        if (bytesReceived <= 0) {
            perror("ERROR receiving file content");
            fclose(file);
            close(sockfd);
            exit(1);
        }

        fwrite(buffer, 1, bytesReceived, file);
        totalBytesReceived += bytesReceived;
        printf("Received chunk of size: %d bytes, Total received: %u bytes\n", bytesReceived, totalBytesReceived);
    }

    printf("File received successfully and saved as: /OTA/Delta_packages/received_patch.patch\n");

    fclose(file);
    close(sockfd);
    return 0;
}
