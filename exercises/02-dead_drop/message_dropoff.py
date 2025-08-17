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
    parser = argparse.ArgumentParser(description='Send a message to a mailbox.')
    parser.add_argument('--message', type=str, required=True, help='Message to send')
    parser.add_argument('--mbox', type=int, required=True, help='Mailbox number to send the message to')
    args = parser.parse_args()

    mbox = args.mbox
    message = int.from_bytes(bytes(args.message,'UTF-8'), byteorder='big')
    if mbox < 0 or mbox > 65535:
        print("Mailbox number must be between 0 and 65535")
        sys.exit(1)
    if message > 0xFFFFFFFF:
        print("Message too long, must be 4 bytes or less")
        sys.exit(1)

    addr = socket.gethostbyname("10.0.0.254")
    iface = get_if()
    bind_layers(UDP, Secret, sport=0xFFFF, dport=0xFFFF)

    print("sending on interface %s to %s" % (iface, str(addr)))
    pkt =  Ether(src=get_if_hwaddr(iface), dst="08:00:00:00:FF:FF")
    pkt = pkt / IP(dst=addr) / UDP(dport=0xFFFF, sport=0xFFFF, chksum=0) / Secret(opCode=SecretOpcode.DROPOFF.value, mailboxNum=mbox, message=message)
    
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
            print(">> Message successfully dropped off to mailbox %d!" % mbox)
        elif res_p[Secret].opCode == SecretOpcode.FAILURE.value:
            print(">> Failed to drop off message to mailbox %d!" % mbox)
        else:
            print(">> Unexpected response received.")

if __name__ == '__main__':
    main()
