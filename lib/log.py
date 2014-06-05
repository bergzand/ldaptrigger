class log:
    import logging as logging
    
    def __init__(self, conf):
        formatter = log.logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.ch = log.logging.StreamHandler()
        self.ch.setFormatter(formatter)
        self._setConf(conf)

    def getLoggerHandle(self, name, loglevel=None):
        if not loglevel:
            loglevel = self.conf[1]
        handle = self.logging.getLogger(name)
        handle.setLevel(loglevel)
        handle.addHandler(self.ch)
        return handle

    def _setConf(self, logconf):
        self.conf = logconf
