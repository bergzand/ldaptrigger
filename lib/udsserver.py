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
        self.loghandle.debug("ldif parsed data: type= %s, dn = %s, mod = %s",
                             reqtype, reqdn, reqmod)

    def handle(self):
        endmarker = '\n\n'
        self.loghandle.debug("connection received")
        total_data = []
        data =''
        #receive complete ldap message
        while True:
            data = self.request.recv(1024)
            if not data:
                return
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

class udsserver(SocketServer.ThreadingUnixStreamServer):
    import log

    name = "netsrv"
    LOGNAME = "socketserver"

    def __init__(self, socketconf, RequestHandlerClass, logger):
        import pwd
        import grp
        import os

        self.loghandle = logger.getLoggerHandle(udsserver.name)
        self.loghandle.info("initializing socket server at %s",
                            socketconf['file'])
        try:
            os.unlink(socketconf['file'])
            self.loghandle.debug("removed old socket")
        except:
            pass
        #initializing real socketserver init
        SocketServer.ThreadingUnixStreamServer.__init__(self, 
                                                        socketconf['file'],
                                                        RequestHandlerClass)
        #setting correct permissions and stuff for the socket file
        if "mode" in socketconf:
            self.loghandle.debug("setting mode to %s", socketconf['mode'])
            os.chmod(socketconf['file'], int(socketconf['mode'], 8))
        uid = gid = -1
        if "user" in socketconf:
            uid = pwd.getpwnam(socketconf['user']).pw_uid
        if "group" in socketconf:
            gid = grp.getgrnam(socketconf['group']).gr_gid
        self.loghandle.debug("setting owner to %s:%s", uid, gid)
        os.chown(socketconf['file'], uid, gid)
        self.loghandle.debug(" Done setting up socket server at %s",
                             socketconf['file'])
        return
