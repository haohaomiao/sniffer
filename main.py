import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QFile,Qt
from PySide6.QtWidgets import QTableWidgetItem as QTItem
from PySide6.QtWidgets import QListWidgetItem as QLItem
from PySide6.QtWidgets import QTreeWidgetItem as QRItem
from PySide6.QtGui import QPixmap
from mainwindow_ui import Ui_MainWindow
from utils import NetworkSniffer
from scapy.all import IP
from scapy.all import Padding
from scapy.all import Raw
from scapy.utils import hexdump
import logging
import time

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='[%(asctime)s] [%(module)s:%(lineno)d] %(levelname)s %(message)s',)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.sniffer = NetworkSniffer()
        # self.sniffer
        self.sniffer.new_pkg_sig.connect(self.update_table)
        self.ui.pushButton.clicked.connect(self.start)
        self.ui.tableWidget.cellPressed.connect(self.update_content)
        self.ui.treeWidget.itemPressed.connect(self.update_layer_content)
        self.ui.actionabout.triggered.connect(self.surprise)
        name_list = [interface.name for interface in self.sniffer.interface]
        self.ui.comboBox.addItems(name_list)

    def surprise(self):
        pic = QPixmap("./avatar.jpg").scaled(self.ui.label.size(), aspectMode=Qt.KeepAspectRatio)
        self.ui.label.setPixmap(pic)
        self.ui.namelabel.setText("hhm")
        self.ui.namelabel.setStyleSheet('color:white')

    def start(self):
        idx = self.ui.comboBox.currentIndex()
        face = self.sniffer.interface[idx]
        logging.debug(f"face: {face.name}")
        bpf_filter = self.ui.lineEdit.text()
        logging.debug(f"filter: {bpf_filter}")
        self.show_table()
        self.sniffer.start_sniffing(face, bpf_filter)



    def show_table(self):
        
        # 假设有一个 3 列的表格
        self.ui.tableWidget.setColumnCount(7)
        horizontal_headers = ["No.", "Time", "Source","Destination","Protocol","Lenth","Info"]
        self.ui.tableWidget.setHorizontalHeaderLabels(horizontal_headers)
        self.ui.tableWidget.horizontalHeader().setStretchLastSection(True)


    def update_table(self):
        packet = self.sniffer.queue.get(False)
        if not packet:
            return

        if self.ui.tableWidget.rowCount() >= 1024:
            self.ui.tableWidget.removeRow(0)

        row = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row)

        self.sniffer.counter += 1
        self.ui.tableWidget.setItem(row, 0, QTItem(str(self.sniffer.counter)))

        total_time = time.time() - self.sniffer.start_time
        self.ui.tableWidget.setItem(row, 1, QTItem(f"{total_time:2f}"))

        if IP in packet:
            src = packet[IP].src
            dst = packet[IP].dst
        else:
            src = packet.src
            dst = packet.dst

        self.ui.tableWidget.setItem(row, 2, QTItem(src))

        self.ui.tableWidget.setItem(row, 3, QTItem(dst))

        layer = None
        for var in self.sniffer.get_packet_layers(packet):
            if not isinstance(var, (Padding, Raw)):
                layer = var

        protocol = layer.name
        self.ui.tableWidget.setItem(row, 4, QTItem(str(protocol)))

        length = f"{len(packet)}"
        self.ui.tableWidget.setItem(row, 5, QTItem(length))

        info = str(packet.summary())
        item = QTItem(info)
        item.packet = packet
        self.ui.tableWidget.setItem(row, 6, item)

    def update_layer_content(self, item, column):
        if not hasattr(item, 'layer'):
            return
        layer = item.layer
        self.ui.textBrowser.setText(hexdump(layer, dump=True))

    def update_content(self, x, y):
        logging.debug("%s, %s clicked", x, y)
        item = self.ui.tableWidget.item(x, 6)
        if not hasattr(item, 'packet'):
            return
        logging.debug(item)
        logging.debug(item.text())
        packet = item.packet
        self.ui.textBrowser.setText(hexdump(packet, dump=True))

        self.ui.treeWidget.clear()
        for layer in self.sniffer.get_packet_layers(packet):
            item = QRItem(self.ui.treeWidget)
            item.layer = layer
            item.setText(0, layer.name)

            for name, value in layer.fields.items():
                child = QRItem(item)
                child.setText(0, f"{name}: {value}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())