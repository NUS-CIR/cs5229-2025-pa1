#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>

#include <rte_eal.h>
#include <rte_ethdev.h>
#include <rte_mbuf.h>
#include <rte_log.h>
#include <rte_common.h>
#include <rte_ether.h>
#include <rte_ip.h>
#include <rte_hash.h>
#include <rte_table.h>
#include <rte_hash_crc.h>

#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

#define RX_RING_SIZE 1024
#define TX_RING_SIZE 1024
#define NUM_MBUFS 8191
#define MBUF_CACHE_SIZE 250
#define BURST_SIZE 32

struct rte_hash *mac_table = NULL;

#define DEAD_DROP_BOX_SIZE 65536
#define SHM_NAME "/secret"
#define UDP_PORT_SECRET 0xFFFF

enum SECRET_OP_CODES
{
    DROPOFF = 1,
    PICKUP = 2,
    SUCCESS = 65535,
    FAILURE = 0
};

uint32_t *dead_drop_box;
uint32_t *dead_drop_box_checksum;

struct secret_hdr
{
    uint16_t opCode;     // Operation code
    uint16_t mailboxNum; // Mailbox number
    uint32_t message;    // Message content
};

void *create_shm(void)
{
    int fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    if (fd == -1)
    {
        perror("shm_open");
        return NULL;
    }

    if (ftruncate(fd, sizeof(uint32_t) * DEAD_DROP_BOX_SIZE) == -1)
    {
        perror("ftruncate");
        return NULL;
    }

    void *addr = mmap(0, sizeof(uint32_t) * DEAD_DROP_BOX_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (addr == MAP_FAILED)
    {
        perror("mmap");
        return NULL;
    }

    close(fd); // fd not needed after mmap
    return addr;
}

// TODO: YOUR CODE HERE (Optional)

void initialize_mac_address_table()
{
    if (mac_table == NULL)
    {
        struct rte_hash_parameters hash_params = {
            .name = "mac_table",
            .entries = 1024,
            .key_len = sizeof(struct rte_ether_addr),
            .hash_func = rte_hash_crc,
            .hash_func_init_val = 0,
            .socket_id = rte_socket_id(),
        };
        mac_table = rte_hash_create(&hash_params);
    }

    struct rte_ether_addr *mac1 = malloc(sizeof(struct rte_ether_addr));
    struct rte_ether_addr *mac2 = malloc(sizeof(struct rte_ether_addr));
    rte_ether_unformat_addr("08:00:00:00:01:11", mac1);
    rte_ether_unformat_addr("08:00:00:00:02:22", mac2);

    uint16_t *mac1_data = malloc(sizeof(uint16_t));
    uint16_t *mac2_data = malloc(sizeof(uint16_t));
    *mac1_data = 0; // Port 0
    *mac2_data = 1; // Port 1
    if (rte_hash_add_key_data(mac_table, mac1, mac1_data) < 0 ||
        rte_hash_add_key_data(mac_table, mac2, mac2_data) < 0)
    {
        RTE_LOG(ERR, USER1, "Failed to add MAC addresses to hash table\n");
        free(mac1_data);
        free(mac2_data);
        return;
    }
    RTE_LOG(INFO, USER1, "Initialized MAC table with two entries\n");
}

void initialize_dead_drop_boxes()
{
    dead_drop_box = (uint32_t *)create_shm();
    if (dead_drop_box == NULL)
    {
        rte_exit(EXIT_FAILURE, "Failed to create shared memory\n");
    }
    dead_drop_box_checksum = malloc(sizeof(uint32_t) * DEAD_DROP_BOX_SIZE);
    memset(dead_drop_box_checksum, 0, sizeof(uint32_t) * DEAD_DROP_BOX_SIZE);
}

void dead_drop_main_loop(void)
{
    RTE_LOG(INFO, USER1, "Starting main loop...\n");
    while (1)
    {
        for (uint16_t port_id = 0; port_id < rte_eth_dev_count_avail(); port_id++)
        {
            struct rte_mbuf *bufs[BURST_SIZE];
            uint16_t nb_rx = rte_eth_rx_burst(port_id, 0, bufs, BURST_SIZE);
            if (nb_rx == 0)
            {
                continue; // No packets received
            }

            for (uint16_t i = 0; i < nb_rx; i++)
            {
                struct rte_mbuf *mbuf = bufs[i];
                struct rte_ether_hdr *eth_hdr = rte_pktmbuf_mtod(mbuf, struct rte_ether_hdr *);
                if (eth_hdr->ether_type != rte_cpu_to_be_16(RTE_ETHER_TYPE_IPV4))
                {
                    rte_pktmbuf_free(mbuf);
                    return;
                }

                struct rte_ipv4_hdr *ipv4_hdr = (struct rte_ipv4_hdr *)(eth_hdr + 1);
                if (ipv4_hdr->next_proto_id == IPPROTO_UDP)
                {
                    struct rte_udp_hdr *udp_hdr = (struct rte_udp_hdr *)(ipv4_hdr + 1);

                    // TODO: YOUR CODE HERE
                }

                uint16_t *destination_port = NULL;
                RTE_LOG(INFO, USER1, "Destination MAC: %02x:%02x:%02x:%02x:%02x:%02x\n",
                        eth_hdr->dst_addr.addr_bytes[0], eth_hdr->dst_addr.addr_bytes[1],
                        eth_hdr->dst_addr.addr_bytes[2], eth_hdr->dst_addr.addr_bytes[3],
                        eth_hdr->dst_addr.addr_bytes[4], eth_hdr->dst_addr.addr_bytes[5]);
                if (rte_hash_lookup_data(mac_table, &eth_hdr->dst_addr, (void **)&destination_port) < 0)
                {
                    RTE_LOG(ERR, USER1, "MAC address not found in hash table\n");
                    rte_pktmbuf_free(mbuf);
                }

                if (destination_port != NULL)
                {
                    if (rte_eth_tx_burst(*destination_port, 0, &mbuf, 1) < 1)
                    {
                        RTE_LOG(ERR, USER1, "Failed to send packet on port %u\n", *destination_port);
                        rte_pktmbuf_free(mbuf);
                    }
                    else
                    {
                        RTE_LOG(INFO, USER1, "Packet sent to port %u\n", *destination_port);
                    }
                }
            }
        }
    }
}

int main(int argc, char **argv)
{
    int ret = rte_eal_init(argc, argv);
    if (ret < 0)
        rte_exit(EXIT_FAILURE, "EAL init failed\n");

    uint16_t num_ports = rte_eth_dev_count_avail();
    if (num_ports == 0)
        rte_exit(EXIT_FAILURE, "No Ethernet ports available\n");
    RTE_LOG(INFO, USER1, "Number of available ports: %u\n", num_ports);

    struct rte_mempool *mbuf_pool = rte_pktmbuf_pool_create("MBUF_POOL", NUM_MBUFS,
                                                            MBUF_CACHE_SIZE, 0, RTE_MBUF_DEFAULT_BUF_SIZE, rte_socket_id());

    if (!mbuf_pool)
        rte_exit(EXIT_FAILURE, "mbuf_pool creation failed\n");

    for (uint16_t port_id = 0; port_id < num_ports; port_id++)
    {
        struct rte_eth_conf port_conf = {0};
        if (rte_eth_dev_configure(port_id, 1, 1, &port_conf) != 0)
            rte_exit(EXIT_FAILURE, "Failed to configure device\n");

        if (rte_eth_rx_queue_setup(port_id, 0, RX_RING_SIZE, rte_socket_id(), NULL, mbuf_pool) != 0)
            rte_exit(EXIT_FAILURE, "Failed to setup RX queue\n");

        if (rte_eth_tx_queue_setup(port_id, 0, TX_RING_SIZE, rte_socket_id(), NULL) != 0)
            rte_exit(EXIT_FAILURE, "Failed to setup TX queue\n");

        if (rte_eth_dev_start(port_id) < 0)
            rte_exit(EXIT_FAILURE, "Failed to start device\n");
    }

    initialize_mac_address_table();
    initialize_dead_drop_boxes();

    dead_drop_main_loop();
    return 0;
}
