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

#define RX_RING_SIZE 1024
#define TX_RING_SIZE 1024
#define NUM_MBUFS 8191
#define MBUF_CACHE_SIZE 250
#define BURST_SIZE 32

static struct rte_hash *mac_table = NULL;

void initialize_mac_table(void)
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
}

// TODO: YOUR CODE HERE (Optional)

void learning_switch_main_loop(void)
{
    RTE_LOG(INFO, USER1, "Starting learning switch main loop\n");

    while (1)
    {
        for (uint16_t port_id = 0; port_id < rte_eth_dev_count_avail(); port_id++)
        {
            struct rte_mbuf *bufs[BURST_SIZE];
            const uint16_t nb_rx = rte_eth_rx_burst(port_id, 0, bufs, BURST_SIZE);

            if (nb_rx == 0)
                continue;

            for (uint16_t i = 0; i < nb_rx; i++)
            {
                struct rte_mbuf *m = bufs[i];
                struct rte_ether_hdr *eth_hdr = rte_pktmbuf_mtod(m, struct rte_ether_hdr *);

                // TODO: YOUR CODE HERE
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

    initialize_mac_table();
    learning_switch_main_loop();
    return 0;
}
