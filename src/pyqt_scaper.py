'''
Created on Feb 21, 2018

@author: pjdrm
'''
import sys
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QUrl
from PyQt4.QtWebKit import QWebPage
import bs4 as bs

class Client(QWebPage):
    
    def __init__(self, url):
        self.app = QApplication(sys.argv)
        QWebPage.__init__(self)
        self.loadFinished.connect(self.on_page_load)
        self.mainFrame().load(QUrl(url))
        self.app.exec_()
        
    def on_page_load(self):
        self.app.quit()
        
url = "http://map.pogotuga.club/"
client_response = Client(url)
source = client_response.mainFrame().toHtml()
with open("map_scapre.html", "w+") as f:
    f.write(source)
soup = bs.BeautifulSoup(source, 'lxml')
