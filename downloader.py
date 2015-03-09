import StringIO
import struct

import httplib, urlparse, urllib2
import requests

from threading import Thread
from Queue import Queue

from utils import get_image_info 

class DownloadWorker(object):
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0'}

    IDLE = 0
    DOWNLOADING = 1

    image_size = 0
    downloaded_size = 0

    segment_size = 8 * 1024 # 8K
    
    def __init__(self):
        self.status = self.IDLE 

    def __create_request(self, uri):
        # check the uri
        scheme, host, path, params, query, fragment = urlparse.urlparse(uri)
        if scheme != "http":
            raise ValueError("only supports HTTP requests")
        if not path:
            path = "/"
        if params:
            path = path + ";" + params
        if query:
            path = path + "?" + query

        # make a http HEAD request
        request = httplib.HTTP(host)
        request.putrequest("HEAD", path)
        request.putheader("Host", host)
        request.endheaders()

        return request

    def start(self, url, target_path):
        self.status = self.DOWNLOADING

        worker_thread = Thread(target=self.__start, args=[url, target_path])
        worker_thread.daemon = True
        worker_thread.start()

    def __start(self, url, target_path):
        # Get the image size before download
        req = self.__create_request(url)
        status, reason, headers = req.getreply()
        req.close()

        self.image_size = headers.get("content-length")
        self.downloaded_size = 0

        # Start Download
        stream = urllib2.urlopen(url)

        download_time = int(self.image_size) / self.segment_size
        last_size = int(self.image_size) % self.segment_size 

        with open(target_path, "wb") as target:
            for index in range(0, download_time):
                target.write(stream.read(self.segment_size))
                self.downloaded_size = self.downloaded_size + self.segment_size 

            target.write(stream.read(last_size))

        self.status = self.IDLE

if __name__ == "__main__":
    import time
    worker = DownloadWorker()
    worker.start("http://lknovel.lightnovel.cn/illustration/image/20120810/20120810172427_41881.jpg", "test.jpg")
    while worker.status == worker.DOWNLOADING:
        print worker.downloaded_size, worker.image_size
        time.sleep(1)
