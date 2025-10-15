#!/usr/bin/env python3

# Copyright 2023 Intel Corporation
# Copyright 2025 National University of Singapore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Andy Fingerhut, andy.fingerhut@gmail.com

import time
import logging

import ptf
import ptf.testutils as tu
from ptf.base_tests import BaseTest

# Links to many Python methods useful when writing automated tests:

# The package `ptf.testutils` contains many useful Python methods for
# writing automated tests, some of which are demonstrated below with
# calls prefixed by the local alias `tu.`.  You can see the
# definitions for all Python code in this package, including some
# documentation for these methods, here:

# https://github.com/p4lang/ptf/blob/master/src/ptf/testutils.py


######################################################################
# Configure logging
######################################################################

# Note: I am not an expert at configuring the Python logging library.
# Recommendations welcome on improvements here.

# The effect achieved by the code below seems to be that many DEBUG
# and higher priority logging messages go to the console, and also to
# a file named 'ptf.log'.  Some of the messages written to the
# 'ptf.log' file do not go to the console, and appear to be created
# from within the ptf library.

logger = logging.getLogger(None)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Examples of some kinds of calls that can be made to generate
# logging messages.
#logger.debug("10 logger.debug message")
#logger.info("20 logger.info message")
#logger.warn("30 logger.warn message")
#logger.error("40 logger.error message")
#logging.debug("10 logging.debug message")
#logging.info("20 logging.info message")
#logging.warn("30 logging.warn message")
#logging.error("40 logging.error message")

class HiddenSimpleL3RouterTest(BaseTest):
    def setUp(self):
        # Setting up PTF dataplane
        self.dataplane = ptf.dataplane_instance
        self.dataplane.flush()
        logging.debug("HiddenSimpleL3RouterTest.setUp()")

    def tearDown(self):
        logging.debug("HiddenSimpleL3RouterTest.tearDown()")


arp_request_packet = None
arp_request_packet_ok = False

from scapy.all import AsyncSniffer

def check_arp_request_pkt(pkt):
    global arp_request_packet
    global arp_request_packet_ok
    
    arp_request_packet = pkt
    # pkt.show()
    assert pkt.haslayer("Ether") and pkt.haslayer("ARP"), "Did not receive an ARP packet"
    assert pkt["Ether"].src == "88:88:88:88:88:88", "ARP packet has incorrect source MAC address"
    assert pkt["Ether"].dst == "ff:ff:ff:ff:ff:ff", "ARP packet has incorrect destination MAC address"
    assert pkt["ARP"].op == 1, "ARP packet is not an ARP request"
    assert pkt["ARP"].psrc == "172.16.0.254", "ARP packet has incorrect source IP address"
    assert pkt["ARP"].pdst == "172.16.0.1", "ARP packet has incorrect destination IP address"
    assert pkt["ARP"].hwsrc == "88:88:88:88:88:88", "ARP packet has incorrect source MAC address"
    assert pkt["ARP"].hwdst == "00:00:00:00:00:00", "ARP packet has incorrect destination MAC address"
    arp_request_packet_ok = True

class L3FwdWithRouterArpRequestTest(HiddenSimpleL3RouterTest):
    def runTest(self):
        h1_mac = '08:01:00:00:01:11'
        h3_mac = '08:03:00:00:01:11'
        
        rtr_mac = '88:88:88:88:88:88'
        rtr_ip_addr = '172.16.0.254'
        
        h1_ip_addr = '10.0.0.1'
        h3_ip_addr = '172.16.0.1'

        pkt = tu.simple_icmp_packet(eth_src=h1_mac, eth_dst=rtr_mac,
                                   ip_src=h1_ip_addr, ip_dst=h3_ip_addr)

        # arp_request_pkt = tu.simple_arp_packet(
        #     eth_src=rtr_mac,
        #     eth_dst='ff:ff:ff:ff:ff:ff',
        #     arp_op=1,
        #     ip_snd=rtr_ip_addr,
        #     ip_tgt=h3_ip_addr,
        #     hw_snd=rtr_mac,
        #     hw_tgt='00:00:00:00:00:00'
        # )

        ig_port = 0
        eg_port = 2

        t = AsyncSniffer(iface="veth5", prn=check_arp_request_pkt, count=1, timeout=2)
        t.start()
        time.sleep(1)  # give the sniffer a second to get ready

        tu.send_packet(self, ig_port, pkt)

        t.join()
        time.sleep(1)  # give the sniffer a second to get ready

        assert arp_request_packet_ok, "Did not receive a valid ARP request packet"
        assert arp_request_packet is not None, "Did not receive an ARP request packet"

        # tu.verify_packets(self, arp_request_pkt, [eg_port])

        arp_reply_pkt = tu.simple_arp_packet(
            eth_src=h3_mac,
            eth_dst=rtr_mac,
            arp_op=2,
            ip_snd=h3_ip_addr,
            ip_tgt=rtr_ip_addr,
            hw_snd=h3_mac,
            hw_tgt=rtr_mac
        )

        pkt = tu.simple_icmp_packet(eth_src=rtr_mac, eth_dst=h3_mac,
                                   ip_src=h1_ip_addr, ip_dst=h3_ip_addr, ip_ttl=63)

        tu.send_packet(self, eg_port, arp_reply_pkt)
        tu.verify_packets(self, pkt, [eg_port])

class MinimumFrameSizeTest(HiddenSimpleL3RouterTest):
    # Note: according to the IEEE 802.3 Ethernet standard, the minimum frame size is 64 bytes
    def runTest(self):
        global arp_request_packet
        assert arp_request_packet
        assert len(arp_request_packet) == 64, "ARP request packet is not padding to meet the minimum frame size"
