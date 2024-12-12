#ifndef SERVER_H
#define SERVER_H

int send_file_to_client(const char* ip_address, const char* filename);
void send_patch_to_clients(const char *clients_filename, const char *patch_filename);
void start_server(int portno);

#endif // SERVER_H

