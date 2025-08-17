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

import os
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

class DeadDropTest(BaseTest):
    def setUp(self):
        # Setting up PTF dataplane
        self.dataplane = ptf.dataplane_instance
        self.dataplane.flush()
        logging.debug("DeadDropTest.setUp()")

    def tearDown(self):
        logging.debug("DeadDropTest.tearDown()")

class FwdTest(DeadDropTest):
    def runTest(self):
        in_smac = '08:00:00:00:01:11'
        in_dmac = '08:00:00:00:02:22'

        ip_src_addr = '10.0.0.1'
        ip_dst_addr = '10.0.0.2'

        ig_port = 0
        eg_port = 1

        pkt = tu.simple_tcp_packet(eth_src=in_smac, eth_dst=in_dmac,
                                   ip_src=ip_src_addr, ip_dst=ip_dst_addr)
        tu.send_packet(self, ig_port, pkt)
        tu.verify_packets(self, pkt, [eg_port])

        in_smac = '08:00:00:00:02:22'
        in_dmac = '08:00:00:00:01:11'

        ip_src_addr = '10.0.0.2'
        ip_dst_addr = '10.0.0.1'

        ig_port = 1 
        eg_port = 0

        pkt = tu.simple_tcp_packet(eth_src=in_smac, eth_dst=in_dmac,
                                   ip_src=ip_dst_addr, ip_dst=ip_src_addr)
        tu.send_packet(self, ig_port, pkt)
        tu.verify_packets(self, pkt, [eg_port])

from scapy.all import *

class SecretOpcode(Enum):
    DROPOFF = 1
    PICKUP = 2
    SUCCESS = 65535
    FAILURE = 0

class Secret(Packet):
    name = "Secret"
    fields_desc = [
        BitField("opCode", 0, 16),
        BitField("mailboxNum", 0, 16),
        BitField("message", 0, 32)
    ]
bind_layers(UDP, Secret, sport=0xFFFF, dport=0xFFFF)

class NonSwitchIpTest(DeadDropTest):
    def runTest(self):
        # DropOff
        in_smac = '08:00:00:00:01:11'
        in_dmac = '08:00:00:00:FF:FE'

        ip_src_addr = '10.0.0.1'
        ip_dst_addr = '10.0.0.253'

        ig_port = 0

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF) / Secret(opCode=SecretOpcode.DROPOFF.value, mailboxNum=0, message=0xdeadbeef)
        tu.send_packet(self, ig_port, pkt)
        tu.verify_no_other_packets(self)

        # PickUp
        in_smac = '08:00:00:00:02:22'
        in_dmac = '08:00:00:00:FF:FE'

        ip_src_addr = '10.0.0.2'
        ip_dst_addr = '1.1.1.1'
        ig_port = 1

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF) / Secret(opCode=SecretOpcode.PICKUP.value, mailboxNum=0, message=0)
        tu.send_packet(self, ig_port, pkt)
        tu.verify_no_other_packets(self)

class NonSecretUdpTest(DeadDropTest):
    def runTest(self):
        # DropOff
        in_smac = '08:00:00:00:01:11'
        in_dmac = '08:00:00:00:FF:FF'

        ip_src_addr = '10.0.0.1'
        ip_dst_addr = '10.0.0.254'
        ig_port = 0

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFE, sport=0xFFFF) / Secret(opCode=SecretOpcode.DROPOFF.value, mailboxNum=1, message=0xdeadbeef)
        tu.send_packet(self, ig_port, pkt)
        tu.verify_no_other_packets(self)

        # PickUp
        in_smac = '08:00:00:00:02:22'
        in_dmac = '08:00:00:00:FF:FF'

        ip_src_addr = '10.0.0.2'
        ip_dst_addr = '10.0.0.254'
        ig_port = 1

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xEEEE) / Secret(opCode=SecretOpcode.PICKUP.value, mailboxNum=1, message=0)
        tu.send_packet(self, ig_port, pkt)
        tu.verify_no_other_packets(self)

class DropOffPickUpTest(DeadDropTest):
    def runTest(self):
        # DropOff
        in_smac = '08:00:00:00:01:11'
        in_dmac = '08:00:00:00:FF:FF'

        ip_src_addr = '10.0.0.1'
        ip_dst_addr = '10.0.0.254'
        ig_port = 0

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.DROPOFF.value, mailboxNum=2, message=0xdeadbeef)
        tu.send_packet(self, ig_port, pkt)

        exp_pkt = Ether(dst=in_smac, src=in_dmac) / IP(dst=ip_src_addr, src=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.SUCCESS.value, mailboxNum=2, message=0xdeadbeef)
        tu.verify_packets(self, exp_pkt, [ig_port])

        # PickUp
        in_smac = '08:00:00:00:02:22'
        in_dmac = '08:00:00:00:FF:FF'

        ip_src_addr = '10.0.0.2'
        ip_dst_addr = '10.0.0.254'
        ig_port = 1

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.PICKUP.value, mailboxNum=2, message=0x0)
        tu.send_packet(self, ig_port, pkt)

        exp_pkt = Ether(dst=in_smac, src=in_dmac) / IP(dst=ip_src_addr, src=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.SUCCESS.value, mailboxNum=2, message=0xdeadbeef)
        tu.verify_packets(self, exp_pkt, [ig_port])

class DropOffPickUpTwiceTest(DeadDropTest):
    def runTest(self):
        # DropOff
        in_smac = '08:00:00:00:01:11'
        in_dmac = '08:00:00:00:FF:FF'
        
        ip_src_addr = '10.0.0.1'
        ip_dst_addr = '10.0.0.254'
        ig_port = 0

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.DROPOFF.value, mailboxNum=4, message=0xdeadbeef)
        tu.send_packet(self, ig_port, pkt)

        exp_pkt = Ether(dst=in_smac, src=in_dmac) / IP(dst=ip_src_addr, src=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.SUCCESS.value, mailboxNum=4, message=0xdeadbeef)
        tu.verify_packets(self, exp_pkt, [ig_port])

        # PickUp
        in_smac = '08:00:00:00:02:22'
        in_dmac = '08:00:00:00:FF:FF'

        ip_src_addr = '10.0.0.2'
        ip_dst_addr = '10.0.0.254'
        ig_port = 1

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.PICKUP.value, mailboxNum=4, message=0x0)
        tu.send_packet(self, ig_port, pkt)

        exp_pkt = Ether(dst=in_smac, src=in_dmac) / IP(dst=ip_src_addr, src=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.SUCCESS.value, mailboxNum=4, message=0xdeadbeef)
        tu.verify_packets(self, exp_pkt, [ig_port])
        
        # Duplicate Pickup
        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.PICKUP.value, mailboxNum=4, message=0x0)
        tu.send_packet(self, ig_port, pkt)

        exp_pkt = Ether(dst=in_smac, src=in_dmac) / IP(dst=ip_src_addr, src=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.FAILURE.value, mailboxNum=4, message=0x0)
        tu.verify_packets(self, exp_pkt, [ig_port])

class DropOffMutatePickUpTest(DeadDropTest):
    def runTest(self):
        # DropOff
        in_smac = '08:00:00:00:01:11'
        in_dmac = '08:00:00:00:FF:FF'

        ip_src_addr = '10.0.0.1'
        ip_dst_addr = '10.0.0.254'
        ig_port = 0

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.DROPOFF.value, mailboxNum=8, message=0xdeadbeef)
        tu.send_packet(self, ig_port, pkt)

        exp_pkt = Ether(dst=in_smac, src=in_dmac) / IP(dst=ip_src_addr, src=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.SUCCESS.value, mailboxNum=8, message=0xdeadbeef)
        tu.verify_packets(self, exp_pkt, [ig_port])

        # Mutate
        current_path = os.path.abspath(os.path.dirname(__file__))
        assert os.path.basename(current_path) == 'ptf', \
            "Expected path to be ptf, got %s. \
                  Are you running run_ptf.sh from the exercise's root directory?" % current_path

        # got to one hierarchy up, trim off ptf
        current_path = os.path.dirname(current_path)
        print("Current path:", current_path)
        
        # go to util/secret_util
        util_path = os.path.join(current_path, 'secret_util')
        secret_util_path = os.path.join(util_path, 'secret_util')
        if not os.path.exists(secret_util_path):
            os.system(f"cd {util_path} && make && chmod +x secret_util")
        os.system(f"sudo {secret_util_path} write 8 bye")

        # PickUp
        in_smac = '08:00:00:00:02:22'
        in_dmac = '08:00:00:00:FF:FF'

        ip_src_addr = '10.0.0.2'
        ip_dst_addr = '10.0.0.254'
        ig_port = 1

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.PICKUP.value, mailboxNum=8, message=0x0)
        tu.send_packet(self, ig_port, pkt)

        exp_pkt = Ether(dst=in_smac, src=in_dmac) / IP(dst=ip_src_addr, src=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.FAILURE.value, mailboxNum=8, message=0x0)
        tu.verify_packets(self, exp_pkt, [ig_port])

class PickUpOnlyTest(DeadDropTest):
    def runTest(self):
        # PickUp
        in_smac = '08:00:00:00:02:22'
        in_dmac = '08:00:00:00:FF:FF'

        ip_src_addr = '10.0.0.2'
        ip_dst_addr = '10.0.0.254'
        ig_port = 1

        pkt = Ether(src=in_smac, dst=in_dmac) / IP(src=ip_src_addr, dst=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.PICKUP.value, mailboxNum=16, message=0x0)
        tu.send_packet(self, ig_port, pkt)

        exp_pkt = Ether(dst=in_smac, src=in_dmac) / IP(dst=ip_src_addr, src=ip_dst_addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.FAILURE.value, mailboxNum=16, message=0x0)
        tu.verify_packets(self, exp_pkt, [ig_port])
