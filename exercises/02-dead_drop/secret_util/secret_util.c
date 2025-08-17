#include <stdio.h>
#include <stdint.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <stdlib.h>

#define SHM_NAME "/secret"
#define ENTRY_COUNT 1024

int main(int argc, char *argv[]) {
    int fd = shm_open(SHM_NAME, O_RDWR, 0);
    if (fd == -1) {
        perror("shm_open");
        return 1;
    }

    size_t size = ENTRY_COUNT * sizeof(uint32_t);
    uint32_t *data = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (data == MAP_FAILED) {
        perror("mmap");
        close(fd);
        return 1;
    }

    // if first arg is read, read the data based on the index in the second arg
    if (argc == 3 && strcmp(argv[1], "read") == 0) {
        int index = atoi(argv[2]);
        if (index < 0 || index >= ENTRY_COUNT) {
            fprintf(stderr, "Index out of bounds\n");
            munmap(data, size);
            close(fd);
            return 1;
        }
        printf("Data at mailbox %d in CHAR: ", index);
        // print using big endian format in char
        for (int i = sizeof(uint32_t) - 1; i >= 0; i--) {
            printf("%c", (data[index] >> (i * 8)) & 0xff);
        }
        // print using hexadecimal format
        printf(", in HEX: 0x");
        for (int i = sizeof(uint32_t) - 1; i >= 0; i--) {
            printf("%02x", (data[index] >> (i * 8)) & 0xff);
        }
        printf("\n");
    }

    // if first arg is write, write the data based on the index in the second arg
    else if (argc == 4 && strcmp(argv[1], "write") == 0) {
        int index = atoi(argv[2]);
        if (strlen(argv[3]) > 4) {
            fprintf(stderr, "Value too long, must be 4 characters or less\n");
            munmap(data, size);
            close(fd);
            return 1;
        }
        uint32_t value = 0;
        for (uint32_t i = 0; i < (uint32_t) strlen(argv[3]); i++) {
            value |= ((uint32_t)(unsigned char)argv[3][i]) << ((3 - i) * 8);
        }
        if (index < 0 || index >= ENTRY_COUNT) {
            fprintf(stderr, "Index out of bounds\n");
            munmap(data, size);
            close(fd);
            return 1;
        }
        data[index] = value;
        printf("Wrote %u to mailbox %d\n", value, index);
    }

    munmap(data, size);
    close(fd);
    return 0;
}