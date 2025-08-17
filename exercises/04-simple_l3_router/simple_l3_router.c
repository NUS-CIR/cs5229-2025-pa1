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
#include <rte_hash_crc.h>
#include <rte_table.h>
#include <rte_table_hash.h>
#include <rte_lpm.h>

// TODO: YOUR CODE HERE (optional)

#define RX_RING_SIZE 1024
#define TX_RING_SIZE 1024
#define NUM_MBUFS 8191
#define MBUF_CACHE_SIZE 250
#define BURST_SIZE 32

static struct rte_hash *arp_table = NULL;
static struct rte_lpm *lpm_table = NULL;

static struct rte_ether_addr router_mac;
static uint32_t router_ip[3];

// TODO: YOUR CODE HERE (optional)

void initialize_router_interfaces()
{
    RTE_LOG(INFO, USER1, "setup L3 router interfaces\n");

    rte_ether_unformat_addr("88:88:88:88:88:88", &router_mac);
    router_ip[0] = RTE_IPV4(10, 0, 0, 254);
    router_ip[1] = RTE_IPV4(192, 168, 1, 254);
    router_ip[2] = RTE_IPV4(172, 16, 0, 254);
}

void initialize_arp_table()
{
    RTE_LOG(INFO, USER1, "init ARP table\n");

    struct rte_hash_parameters arp_params = {
        .name = "arp_table",
        .entries = 1024,
        .key_len = sizeof(uint32_t), // IP address as key
        .hash_func = rte_hash_crc,
        .hash_func_init_val = 0,
        .socket_id = rte_socket_id(),
    };

    arp_table = rte_hash_create(&arp_params);
}

void initialize_lpm_table()
{
    RTE_LOG(INFO, USER1, "init LPM table\n");

    struct rte_lpm_config lpm_config = {
        .max_rules = 1024,
        .flags = 0,
        .number_tbl8s = 256};

    lpm_table = rte_lpm_create("lpm_table", rte_socket_id(), &lpm_config);
}

void populate_routing_table()
{
    RTE_LOG(INFO, USER1, "insert routes into LPM table\n");
    for (uint32_t i = 0; i < sizeof(router_ip) / sizeof(router_ip[0]); i++)
    {
        uint32_t ip = router_ip[i];
        int ret = rte_lpm_add(lpm_table, ip, 24, i);
        if (ret < 0)
        {
            RTE_LOG(ERR, USER1, "Failed to add route for IP %u.%u.%u.0/24\n",
                    ip >> 24 & 0xFF, (ip >> 16) & 0xFF,
                    (ip >> 8) & 0xFF);
        }
        else
        {
            RTE_LOG(INFO, USER1, "Added route for IP %u.%u.%u.0/24 with next hop via port %u\n",
                    ip >> 24 & 0xFF, (ip >> 16) & 0xFF,
                    (ip >> 8) & 0xFF, i);
        }
    }
}

void simple_l3_router_main_loop(void)
{
    RTE_LOG(INFO, USER1, "simple_l3_router main loop\n");

    // TODO: YOUR CODE HERE (optional)

    struct rte_mbuf *bufs[BURST_SIZE];
    while (1)
    {
        for (uint16_t port_id = 0; port_id < rte_eth_dev_count_avail(); port_id++)
        {
            uint16_t nb_rx = rte_eth_rx_burst(port_id, 0, bufs, BURST_SIZE);
            if (nb_rx > 0)
            {
                RTE_LOG(INFO, USER1, "Received %u packets on port %u\n", nb_rx, port_id);
                for (uint16_t i = 0; i < nb_rx; i++)
                {
                    struct rte_mbuf *m = bufs[i];
                    struct rte_ether_hdr *eth_hdr = rte_pktmbuf_mtod(m, struct rte_ether_hdr *);

                    // TODO: YOUR CODE HERE
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

    initialize_arp_table();
    initialize_lpm_table();
    initialize_router_interfaces();
    populate_routing_table();

    simple_l3_router_main_loop();
    return 0;
}
