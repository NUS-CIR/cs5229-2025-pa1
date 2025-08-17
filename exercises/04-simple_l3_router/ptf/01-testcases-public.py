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

class SimpleL3RouterTest(BaseTest):
    def setUp(self):
        # Setting up PTF dataplane
        self.dataplane = ptf.dataplane_instance
        self.dataplane.flush()
        logging.debug("SimpleL3RouterTest.setUp()")

    def tearDown(self):
        logging.debug("SimpleL3RouterTest.tearDown()")

class ArpTest(SimpleL3RouterTest):
    def runTest(self):
        arp_request_pkt = tu.simple_arp_packet(
            eth_src='08:01:00:00:01:11',
            eth_dst='ff:ff:ff:ff:ff:ff',
            arp_op=1,
            ip_snd='10.0.0.1',
            ip_tgt='10.0.0.254',
            hw_snd='08:01:00:00:01:11',
            hw_tgt='00:00:00:00:00:00'
        )
        arp_reply_pkt = tu.simple_arp_packet(
            eth_src='88:88:88:88:88:88',
            eth_dst='08:01:00:00:01:11',
            arp_op=2,
            ip_snd='10.0.0.254',
            ip_tgt='10.0.0.1',
            hw_snd='88:88:88:88:88:88',
            hw_tgt='08:01:00:00:01:11'
        )

        ig_port = 0
        eg_port = 0

        tu.send_packet(self, ig_port, arp_request_pkt)
        tu.verify_packets(self, arp_reply_pkt, [eg_port])

        arp_request_pkt = tu.simple_arp_packet(
            eth_src='08:02:00:00:01:11',
            eth_dst='ff:ff:ff:ff:ff:ff',
            arp_op=1,
            ip_snd='192.168.1.1',
            ip_tgt='192.168.1.254',
            hw_snd='08:02:00:00:01:11',
            hw_tgt='00:00:00:00:00:00'
        )
        arp_reply_pkt = tu.simple_arp_packet(
            eth_src='88:88:88:88:88:88',
            eth_dst='08:02:00:00:01:11',
            arp_op=2,
            ip_snd='192.168.1.254',
            ip_tgt='192.168.1.1',
            hw_snd='88:88:88:88:88:88',
            hw_tgt='08:02:00:00:01:11'
        )

        ig_port = 1
        eg_port = 1

        tu.send_packet(self, ig_port, arp_request_pkt)
        tu.verify_packets(self, arp_reply_pkt, [eg_port])

class L3FwdTest(SimpleL3RouterTest):
    def runTest(self):
        h1_mac = '08:01:00:00:01:11'
        h2_mac = '08:02:00:00:01:11'
        rtr_mac = '88:88:88:88:88:88'
        
        ip_src_addr = '10.0.0.1'
        ip_dst_addr = '192.168.1.1'

        ig_port = 0
        eg_port = 1

        pkt = tu.simple_icmp_packet(eth_src=h1_mac, eth_dst=rtr_mac,
                                   ip_src=ip_src_addr, ip_dst=ip_dst_addr)

        exp_pkt = tu.simple_icmp_packet(eth_src=rtr_mac, eth_dst=h2_mac,
                                       ip_src=ip_src_addr, ip_dst=ip_dst_addr, ip_ttl=63)

        tu.send_packet(self, ig_port, pkt)
        tu.verify_packets(self, exp_pkt, [eg_port])
