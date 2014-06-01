from lib.hook import pyhook

class Hook(pyhook):
 
    def handle(self, dn, reqmod, reqresult):
        self.loghandle.info("received: %s", dn)