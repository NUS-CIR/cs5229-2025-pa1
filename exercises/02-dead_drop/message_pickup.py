#!/usr/bin/env python3
import sys
import socket
import argparse
from enum import Enum

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

def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

def main():
    parser = argparse.ArgumentParser(description='Pickup a message from a mailbox.')
    parser.add_argument('--mbox', type=int, required=True, help='Mailbox number to pickup the message from')
    args = parser.parse_args()

    mailboxNum = args.mbox
    if mailboxNum < 0 or mailboxNum > 65535:
        print("Mailbox number must be between 0 and 65535")
        sys.exit(1)

    addr = socket.gethostbyname("10.0.0.254")
    iface = get_if()
    bind_layers(UDP, Secret, sport=0xFFFF, dport=0xFFFF)

    print("sending on interface %s to %s" % (iface, str(addr)))
    pkt =  Ether(src=get_if_hwaddr(iface), dst="08:00:00:00:FF:FF")
    pkt = pkt / IP(dst=addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.PICKUP.value, mailboxNum=mailboxNum, message=0)
    print("========== Sent packet:")
    pkt.show2()
    print("==========")
    res_p = srp1(pkt, iface=iface, verbose=False, timeout=2)
    if not res_p:
        print("Timeout! No message received.")
    else:
        print("========== Received packet:")
        res_p.show()
        print("==========")
        if res_p[Secret].opCode == SecretOpcode.SUCCESS.value:
            print(">> Message successfully picked up from mailbox %d!" % mailboxNum)
            message = res_p[Secret].message
            if message != 0:
                print("Message content: %s" % message.to_bytes(4, byteorder='big').decode('UTF-8'))
        elif res_p[Secret].opCode == SecretOpcode.FAILURE.value:
            print(">> Failed to pickup message from mailbox %d!" % mailboxNum)
        else:
            print(">> Unexpected response received.")


if __name__ == '__main__':
    main()
