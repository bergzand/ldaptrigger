class log:
    import logging as logging
    
    def __init__(self, conf):
        formatter = log.logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.ch = log.logging.StreamHandler()
        self.ch.setFormatter(formatter)

    def getLoggerHandle(self, name):
        handle = self.logging.getLogger(name)
        handle.setLevel(self.conf['loglevel'])
        handle.addHandler(self.ch)
        return handle

    def setConf(self,logconf):
        self.conf = logconf