import logging

class log:

    def __init__(self, conf):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.ch = logging.StreamHandler()
        self.ch.setFormatter(formatter)
        self._setConf(conf)

    def getLoggerHandle(self, name, loglevel=None):
        if not loglevel:
            loglevel = self.conf[1]
        handle = logging.getLogger(name)
        handle.setLevel(loglevel)
        handle.addHandler(self.ch)
        return handle

    def _setConf(self, logconf):
        self.conf = logconf

