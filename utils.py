from scapy import all as sca
from PySide6.QtCore import QObject, Signal
import sys
import logging
import time
from queue import Queue

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='[%(asctime)s] [%(module)s:%(lineno)d] %(levelname)s %(message)s',)

class NetworkSniffer(QObject):
    new_pkg_sig = Signal(None)
    new_face_sig = Signal(list)
    def __init__(self):
        super(NetworkSniffer, self).__init__()
        self.interface = []
        self.sniffer = None
        self.queue = Queue()
        self.start_time = 0
        self.counter = 0
        self.init_interface()


    def init_interface(self):
        for interface in sca.get_working_ifaces():
            # face.name face.ip face.
            logging.debug(f"{interface.name},{interface.mac},{interface.ip}")
            self.interface.append(interface)

    def send_new_pkg_sig(self,packet):
        if not self.sniffer:
            logging.warning("sniffer = None!!!")
        self.queue.put(packet)
        logging.debug(packet.summary())
        self.new_pkg_sig.emit()

    def get_packet_layers(self, packet):
        counter = 0
        while True:
            layer = packet.getlayer(counter)
            if layer is None:
                break
            yield layer
            counter += 1    

    

    def start_sniffing(self, face, bpf_filter):
        """face: 进行抓包的网卡，"""
        self.start_time = time.time()
        self.counter = 0
        logging.debug("time and counter reset")
        self.sniffer = sca.AsyncSniffer(iface=face,prn=self.send_new_pkg_sig,filter=bpf_filter) 
        self.sniffer.start()
        logging.debug(self.sniffer)
