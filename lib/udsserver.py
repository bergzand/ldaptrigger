import SocketServer
import StringIO
import ldif
    
class udshandler(SocketServer.BaseRequestHandler):

    import log

    name = "nethandler"

    def __init__(self, logger, callback, *args, **keys):
        self.callback = callback
        self.loghandle = logger.getLoggerHandle(udshandler.name)
        SocketServer.BaseRequestHandler.__init__(self, *args, **keys)

    def _parsemessage(self, datagram):
        payload = ''.join(datagram.splitlines(True)[3:])
        ldifdata = ldif.LDIFRecordList(StringIO.StringIO(payload))
        ldifdata.parse()
        ldifdn, ldifattr = ldifdata.all_records[0]
        self.loghandle.debug("ldif data dn = %s,attrs= %s", ldifdn, ldifattr)
        reqdn = ldifattr['reqDN'][0]
        reqtype = ldifattr['reqType'][0]
        if reqtype != "delete":
            reqmod = ldifattr['reqMod']
        else:
            reqmod = None
        reqresult = ldifattr['reqResult'][0]
        req = (reqtype, reqdn, reqmod, reqresult)
        self.callback(req)
        self.loghandle.debug("ldif parsed data: type= %s, dn = %s, mod = %s", reqtype, reqdn, reqmod)
        

    def handle(self):
        endmarker = '\n\n'
        self.loghandle.debug("connection received")
        total_data = []
        data =''
        #receive complete ldap message
        while True:
            data = self.request.recv(1024)
            self.loghandle.debug("received : %s", data)
            if data.endswith(endmarker):
                self.loghandle.debug('complete message received')
                total_data.append(data)
                break
            total_data.append(data)
            if ''.join(total_data).endswith(endmarker):
                self.loghandle.debug('complete message received')
                break
        datagram = ''.join(total_data)
        self.loghandle.debug('total data: %s', ''.join(total_data))
        if datagram.split('\n', 1)[0] != "UNBIND":
            self.request.sendall("RESULT\ncode: 0\n")
        self._parsemessage(datagram)

class udsserver(SocketServer.UnixStreamServer):
    import log
    name = "netsrv"
    LOGNAME = "socketserver"

    def __init__(self, server_address, RequestHandlerClass, logger):
        self.loghandle = logger.getLoggerHandle(udsserver.name)
        self.loghandle.info("initializing socket server")
        SocketServer.UnixStreamServer.__init__(self, server_address, RequestHandlerClass)
        return