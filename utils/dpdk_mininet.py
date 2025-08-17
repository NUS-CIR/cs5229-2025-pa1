#! /usr/bin/env python3
# Copyright 2013-present Barefoot Networks, Inc.
# Copyright 2025-present National University of Singapore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Adapted by Xin Zhe Khooi (khooixz@comp.nus.edu.sg) from scripts found in
# the P4 Tutorial

import os
import tempfile
from sys import exit
from time import sleep

from mininet.log import debug, error, info
from mininet.moduledeps import pathCheck
from mininet.node import Host, Switch

SWITCH_START_TIMEOUT = 10 # seconds

class DpdkHost(Host):
    def config(self, **params):
        r = super(Host, self).config(**params)

        self.defaultIntf().rename("eth0")

        for off in ["rx", "tx", "sg"]:
            cmd = "/sbin/ethtool --offload eth0 %s off" % off
            self.cmd(cmd)

        # disable IPv6
        self.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        self.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        self.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

        return r

    def describe(self):
        print("**********")
        print(self.name)
        print("default interface: %s\t%s\t%s" %(
            self.defaultIntf().name,
            self.defaultIntf().IP(),
            self.defaultIntf().MAC()
        ))
        print("**********")

class DpdkSwitch(Switch):
    """DPDK switch"""
    def __init__(self, name, **kwargs):
        Switch.__init__(self, name, **kwargs)

        self.dpdk_exe = kwargs.get('dpdk_exe', None)
        self.log_file = kwargs.get('log_file', None)
        self.pcap_dir = kwargs.get('pcap_dir', None)
        self.params = kwargs.get('params', {})

    @classmethod
    def setup(cls):
        pass

    def check_switch_started(self, pid):
        """While the process is running (pid exists), we check if the Thrift
        server has been started. If the Thrift server is ready, we assume that
        the switch was started successfully. This is only reliable if the Thrift
        server is started at the end of the init process"""
        while True:
            if not os.path.exists(os.path.join("/proc", str(pid))):
                return False
            sleep(0.5)

    def start(self, controllers):
        "Start up a new DPDK switch"
        info("Starting DPDK switch {}.\n".format(self.name))

        self.tap_interfaces = []
        self.intf_tap_pairs = []
        self.bridges = []
        i = 0
        for port, intf in list(self.intfs.items()):
            if not intf.IP():
                tap_if_name = f"tap{i}"
                bridge_name = f"br{i}"
                self.tap_interfaces.append(tap_if_name)
                self.intf_tap_pairs.append((intf.name, tap_if_name))
                self.bridges.append(bridge_name)
                i = i + 1
        debug("tap interfaces: ", self.tap_interfaces, "\n")
        debug("intf-tap pairs: ", self.intf_tap_pairs, "\n")

        vdev_list = []
        for tap_if_name in self.tap_interfaces:
            vdev_list.append(f"--vdev=net_{tap_if_name},iface={tap_if_name}")
        debug("dpdk vdev list: ", vdev_list, "\n")

        command = f"sudo ./build/{self.dpdk_exe} --proc-type=auto --no-pci {' '.join(vdev_list)} -l 0-1 -n2 > {self.log_file} 2>&1"
        debug("command: ", command, "\n")

        with tempfile.NamedTemporaryFile() as f:
            self.cmd(f"{command} & echo $! >> {f.name}" )
            self.dpdk_pid = int(f.read())
        debug("DPDK switch {} PID is {}.\n".format(self.name, self.dpdk_pid))

        # TODO: check DPDK status

        # setup the tap interfaces and bridges
        for i, (intf_name, tap_if_name) in enumerate(self.intf_tap_pairs):
            current_bridge = self.bridges[i]
            self.cmd(f'sudo ovs-vsctl add-br {current_bridge}')
            self.cmd(f'sudo ovs-vsctl add-port {current_bridge} {intf_name}')
            self.cmd(f'sudo ovs-vsctl add-port {current_bridge} {tap_if_name}')
            self.cmd(f"sudo ovs-ofctl add-flow {current_bridge} \"in_port=2,actions=output:1\"")
            self.cmd(f"sudo ovs-ofctl add-flow {current_bridge} \"in_port=1,actions=output:2\"")
        
        # collect pcap files keep their pid and stop later
        if self.pcap_dir:
            if not os.path.exists(self.pcap_dir):
                os.makedirs(self.pcap_dir)
            for intf, tap_if_name in self.intf_tap_pairs:
                pcap_file = os.path.join(self.pcap_dir, f"{intf}.pcap")
                self.cmd(f"sudo tcpdump -i {tap_if_name} -w {pcap_file} &")


    def stop(self):
        "Terminate P4 switch."
        info("Stopping DPDK switch {}.\n".format(self.name))
        # stop dpdk switch
        self.cmd(f'sudo kill -9 {self.dpdk_pid}')
        # stop pcap capture
        if self.pcap_dir:
            for tap_if_name in self.tap_interfaces:
                self.cmd(f'sudo pkill -f "tcpdump -i {tap_if_name}"')
        # remove bridges
        for bridge in self.bridges:
            self.cmd(f'sudo ovs-vsctl --if-exists del-br {bridge}')
        self.cmd('wait')
        self.deleteIntfs()

    def attach(self, intf):
        "Connect a data port"
        assert(0)

    def detach(self, intf):
        "Disconnect a data port"
        assert(0)

    def describe(self):
        print("**********")
        print(self.name)
        print("default interface: %s\t%s\t%s" %(
            self.defaultIntf().name,
            self.defaultIntf().IP(),
            self.defaultIntf().MAC()
        ))
        print("**********")
