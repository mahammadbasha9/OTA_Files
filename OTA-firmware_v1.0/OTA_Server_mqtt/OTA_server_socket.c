/*#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <errno.h>
#include <ctype.h>

#define MAX_SIZE 1024
#define MAX_RETRIES 5  // Maximum number of retries for sending data
#define MAX_Clients 10

typedef struct {
    unsigned int upSize;
    char fileName[MAX_SIZE];
} updatePackageConfig;

typedef struct {
    int sockfd;
    struct sockaddr_in cli_addr;
} Client;

Client *clients[MAX_SIZE];
int clientCount = 0;
pthread_mutex_t clientMutex = PTHREAD_MUTEX_INITIALIZER;

void error(const char *msg) {
    perror(msg);
    exit(1);
}

void cleanupClient(int index) {
    if (clients[index] != NULL) {
        close(clients[index]->sockfd);
        free(clients[index]);
        clients[index] = NULL;  // Avoid dangling references
    }
}

// Add client to the list
void addClient(int sockfd, struct sockaddr_in cli_addr) {
    pthread_mutex_lock(&clientMutex);
    if (clientCount < MAX_SIZE) { // Ensure we don't exceed bounds
        clients[clientCount] = (Client *)malloc(sizeof(Client));
        if (clients[clientCount] == NULL) {
            pthread_mutex_unlock(&clientMutex);
            error("ERROR allocating memory for new client");
        }
        clients[clientCount]->sockfd = sockfd;
        clients[clientCount]->cli_addr = cli_addr;
        clientCount++;
    }
    pthread_mutex_unlock(&clientMutex);
}

// Retry sending data
int sendWithRetry(int sockfd, const void *buffer, size_t length) {
    int bytesSent;
    int retries = 0;

    while ((bytesSent = send(sockfd, buffer, length, 0)) < 0) {
        if (errno == EPIPE) {
            fprintf(stderr, "ERROR sending data: Broken pipe\n");
            return -1;
        } else if (errno == EINTR) {
            if (++retries >= MAX_RETRIES) {
                fprintf(stderr, "ERROR sending data: %s after %d retries\n", strerror(errno), retries);
                return -1;
            }
        } else {
            fprintf(stderr, "ERROR sending data: %s\n", strerror(errno));
            return -1;
        }
    }
    return bytesSent;
}

void sendPatchFile(Client *client, const char *filePath) {
    char buffer[MAX_SIZE];
    FILE *file;
    updatePackageConfig config;

    file = fopen(filePath, "rb");
    if (file == NULL) {
        perror("ERROR opening file");
        return;
    }
    fseek(file, 0, SEEK_END);
    config.upSize = ftell(file);
    fseek(file, 0, SEEK_SET);
    strncpy(config.fileName, filePath, MAX_SIZE);
    config.fileName[MAX_SIZE - 1] = '\0'; // Ensure null-termination

    // Send updatePackageConfig
    if (sendWithRetry(client->sockfd, &config, sizeof(config)) < 0) {
        fclose(file);
        return;
    }

    // Send file data
    memset(buffer, 0, MAX_SIZE);
    int bytesRead;
    while ((bytesRead = fread(buffer, 1, MAX_SIZE, file)) > 0) {
        if (sendWithRetry(client->sockfd, buffer, bytesRead) < 0) {
            fclose(file);
            return;
        }
        memset(buffer, 0, MAX_SIZE);
    }

    printf("Patch file sent successfully to client: %s:%d\n", inet_ntoa(client->cli_addr.sin_addr), ntohs(client->cli_addr.sin_port));
    fclose(file);
}

void *clientHandler(void *arg) {
    int sockfd = *(int *)arg;
    struct sockaddr_in cli_addr;
    socklen_t clilen = sizeof(cli_addr);

    getpeername(sockfd, (struct sockaddr *)&cli_addr, &clilen);
    addClient(sockfd, cli_addr);

    printf("Client Connected: %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));

    // Keep the client connected
    while (1) {
        usleep(100000); // Avoid busy-waiting
    }

    cleanupClient(clientCount - 1); // Cleanup on exit
    close(sockfd);
    free(arg);
    pthread_exit(NULL);
}

void startServer(int portno) {
    int sockfd, newsockfd;
    socklen_t clilen;
    struct sockaddr_in serv_addr, cli_addr;
    pthread_t tid_clients;

    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        error("ERROR opening socket");
    }

    int opt = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)); // Allow immediate reuse of the port

    bzero((char *)&serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(portno);

    if (bind(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        error("ERROR on binding");
    }

    listen(sockfd, MAX_Clients);
    printf("Server is running and listening on port %d\n", portno);

    while (1) {
        clilen = sizeof(cli_addr);
        newsockfd = accept(sockfd, (struct sockaddr *)&cli_addr, &clilen);
        if (newsockfd < 0) {
            error("ERROR on accept");
        }

        int *newsockfdPtr = malloc(sizeof(int));
        if (newsockfdPtr == NULL) {
            fprintf(stderr, "ERROR allocating memory for client socket: %s\n", strerror(errno));
            exit(EXIT_FAILURE);
        }
        *newsockfdPtr = newsockfd;

        if (pthread_create(&tid_clients, NULL, clientHandler, newsockfdPtr) != 0) {
            error("ERROR creating thread");
        }

        pthread_detach(tid_clients);
    }

    close(sockfd);
}

void send_patch_to_clients(const char *clientFilePath, const char *patchFilePath) {
    FILE *file = fopen(clientFilePath, "r");
    if (file == NULL) {
        error("ERROR opening client file");
    }

    char line[MAX_SIZE];
    while (fgets(line, sizeof(line), file)) {
        char clientName[MAX_SIZE], clientIP[MAX_SIZE], clientStatus[MAX_SIZE];
        sscanf(line, "%[^,],%[^,],%s", clientName, clientIP, clientStatus);

        if (strcmp(clientStatus, "Enable") == 0) {
            pthread_mutex_lock(&clientMutex);
            for (int i = 0; i < clientCount; i++) {
                if (clients[i] != NULL && strcmp(inet_ntoa(clients[i]->cli_addr.sin_addr), clientIP) == 0) {
                    sendPatchFile(clients[i], patchFilePath);
                    if (errno == EPIPE) {
                        cleanupClient(i);
                    }
                }
            }
            pthread_mutex_unlock(&clientMutex);
        }
    }

    fclose(file);
}

// Expose the startServer and sendPatch functions to be callable from Python
__attribute__((visibility("default"))) void start_server(int portno) {
    startServer(portno);
}

__attribute__((visibility("default"))) void send_patch(const char *clientFilePath, const char *patchFilePath) {
    send_patch_to_clients(clientFilePath, patchFilePath);
}
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <errno.h>

#define MAX_SIZE 1024
#define MAX_CLIENTS 10

typedef struct {
    unsigned int upSize;
    char fileName[MAX_SIZE];
} updatePackageConfig;

typedef struct {
    int sockfd;
    struct sockaddr_in cli_addr;
} Client;

Client *clients[MAX_SIZE];
int clientCount = 0;
pthread_mutex_t clientMutex = PTHREAD_MUTEX_INITIALIZER;

void error(const char *msg) {
    perror(msg);
    exit(1);
}

void cleanupClient(int index) {
    if (clients[index] != NULL) {
        close(clients[index]->sockfd);
        free(clients[index]);
        clients[index] = NULL;
    }
}

void addClient(int sockfd, struct sockaddr_in cli_addr) {
    pthread_mutex_lock(&clientMutex);
    if (clientCount < MAX_SIZE) {
        clients[clientCount] = (Client *)malloc(sizeof(Client));
        if (clients[clientCount] == NULL) {
            pthread_mutex_unlock(&clientMutex);
            error("ERROR allocating memory for new client");
        }
        clients[clientCount]->sockfd = sockfd;
        clients[clientCount]->cli_addr = cli_addr;
        clientCount++;
    }
    pthread_mutex_unlock(&clientMutex);
}

int sendWithRetry(int sockfd, const void *buffer, size_t length) {
    int bytesSent;
    int retries = 0;
    while ((bytesSent = send(sockfd, buffer, length, 0)) < 0) {
        if (errno == EPIPE) {
            fprintf(stderr, "ERROR sending data: Broken pipe\n");
            return -1;
        } else if (errno == EINTR) {
            if (++retries >= 5) {
                fprintf(stderr, "ERROR sending data after retries: %s\n", strerror(errno));
                return -1;
            }
        } else {
            fprintf(stderr, "ERROR sending data: %s\n", strerror(errno));
            return -1;
        }
    }
    return bytesSent;
}

void sendPatchFile(Client *client, const char *filePath) {
    FILE *file;
    updatePackageConfig config;

    file = fopen(filePath, "rb");
    if (file == NULL) {
        perror("ERROR opening file");
        return;
    }

    fseek(file, 0, SEEK_END);
    config.upSize = ftell(file);
    fseek(file, 0, SEEK_SET);
    strncpy(config.fileName, filePath, MAX_SIZE);
    config.fileName[MAX_SIZE - 1] = '\0';

    printf("Sending metadata: FileName = %s, FileSize = %u bytes\n", config.fileName, config.upSize);

    if (config.upSize == 0) {
        fprintf(stderr, "ERROR: File size is 0 bytes, not sending file.\n");
        fclose(file);
        return;
    }

    // Send the file size first
    if (sendWithRetry(client->sockfd, &config.upSize, sizeof(config.upSize)) < 0) {
        fclose(file);
        return;
    }

    // Send the file name next
    if (sendWithRetry(client->sockfd, config.fileName, sizeof(config.fileName)) < 0) {
        fclose(file);
        return;
    }

    // Now send the file content
    char buffer[MAX_SIZE];
    int bytesRead;
    while ((bytesRead = fread(buffer, 1, MAX_SIZE, file)) > 0) {
        printf("Sending chunk of size: %d bytes\n", bytesRead);
        if (sendWithRetry(client->sockfd, buffer, bytesRead) < 0) {
            fclose(file);
            return;
        }
    }

    printf("Patch file sent successfully to client: %s:%d\n",
           inet_ntoa(client->cli_addr.sin_addr),
           ntohs(client->cli_addr.sin_port));

    fclose(file);
}

void *clientHandler(void *arg) {
    int sockfd = *(int *)arg;
    struct sockaddr_in cli_addr;
    socklen_t clilen = sizeof(cli_addr);

    getpeername(sockfd, (struct sockaddr *)&cli_addr, &clilen);
    addClient(sockfd, cli_addr);

    printf("Client Connected: %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));

    while (1) {
        usleep(100000);
    }

    cleanupClient(clientCount - 1);
    close(sockfd);
    free(arg);
    pthread_exit(NULL);
}

void startServer(int portno) {
    int sockfd, newsockfd;
    socklen_t clilen;
    struct sockaddr_in serv_addr, cli_addr;
    pthread_t tid_clients;

    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        error("ERROR opening socket");
    }

    int opt = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    bzero((char *)&serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(portno);

    if (bind(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        error("ERROR on binding");
    }

    listen(sockfd, MAX_CLIENTS);
    printf("Server is running and listening on port %d\n", portno);

    while (1) {
        clilen = sizeof(cli_addr);
        newsockfd = accept(sockfd, (struct sockaddr *)&cli_addr, &clilen);
        if (newsockfd < 0) {
            error("ERROR on accept");
        }

        int *newsockfdPtr = malloc(sizeof(int));
        if (newsockfdPtr == NULL) {
            fprintf(stderr, "ERROR allocating memory for client socket: %s\n", strerror(errno));
            exit(EXIT_FAILURE);
        }
        *newsockfdPtr = newsockfd;

        if (pthread_create(&tid_clients, NULL, clientHandler, newsockfdPtr) != 0) {
            error("ERROR creating thread");
        }

        pthread_detach(tid_clients);
    }

    close(sockfd);
}


void send_patch_to_clients(const char *clientFilePath, const char *patchFilePath) {
    FILE *file = fopen(clientFilePath, "r");
    if (file == NULL) {
        error("ERROR opening client file");
    }

    char line[MAX_SIZE];
    while (fgets(line, sizeof(line), file)) {
        char clientName[MAX_SIZE], clientIP[MAX_SIZE], clientStatus[MAX_SIZE];
        sscanf(line, "%[^,],%[^,],%s", clientName, clientIP, clientStatus);

        if (strcmp(clientStatus, "Enable") == 0) {
            pthread_mutex_lock(&clientMutex);
            for (int i = 0; i < clientCount; i++) {
                if (clients[i] != NULL && strcmp(inet_ntoa(clients[i]->cli_addr.sin_addr), clientIP) == 0) {
                    sendPatchFile(clients[i], patchFilePath);
                    if (errno == EPIPE) {
                        cleanupClient(i);
                    }
                }
            }
            pthread_mutex_unlock(&clientMutex);
        }
    }

    fclose(file);
}

__attribute__((visibility("default"))) void start_server(int portno) {
    startServer(portno);
}

__attribute__((visibility("default"))) void send_patch(const char *clientFilePath, const char *patchFilePath) {
    send_patch_to_clients(clientFilePath, patchFilePath);
}

