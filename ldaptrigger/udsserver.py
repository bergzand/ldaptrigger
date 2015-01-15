import SocketServer
import StringIO
import ldif

import pwd
import grp
import os
import multiprocessing
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
        #self.loghandle.debug("ldif data dn = %s,attrs= %s", ldifdn, ldifattr)
        reqdn = ldifattr['reqDN'][0]
        reqtype = ldifattr['reqType'][0]
        if reqtype != "delete":
            reqmod = ldifattr['reqMod']
        else:
            reqmod = None
        reqresult = ldifattr['reqResult'][0]
        req = (reqtype, reqdn, reqmod, reqresult)
        self.callback(req)
        #self.loghandle.debug("ldif parsed data: type= %s, dn = %s, mod = %s",
        #                     reqtype, reqdn, reqmod)

    def handle(self):
        endmarker = '\n\n'
        total_data = []
        data =''
        unbind = False
        #receive complete ldap message
        while not unbind:
            while True:
                data = self.request.recv(1024)
                if not data:
                    return
                if data.endswith(endmarker):
                    total_data.append(data)
                    break
                total_data.append(data)
                if ''.join(total_data).endswith(endmarker):
                    break
            datagram = ''.join(total_data)
            msgtype = datagram.split('\n', 1)[0]
            self.loghandle.debug('complete message received of type {0}'.format(msgtype))
            if msgtype == "PING":
                self.request.sendall("RESULT\ncode: 0\n")
            elif msgtype != "UNBIND":
                self.request.sendall("RESULT\ncode: 0\n")
                self._parsemessage(datagram)
                unbind = True
            else:
                unbind = True


class udsserver(SocketServer.ThreadingUnixStreamServer):

    name = "netsrv"
    LOGNAME = "socketserver"

    def __init__(self, socketconf, RequestHandlerClass, logger):

        self.socketconf = dict(socketconf)
        self.loghandle = logger.getLoggerHandle(udsserver.name)
        self.loghandle.info("initializing socket server at %s",
                            self.socketconf['file'])
        try:
            os.unlink(self.socketconf['file'])
            self.loghandle.debug("removed old socket")
        except:
            pass
        #initializing real socketserver init
        SocketServer.ThreadingUnixStreamServer.__init__(self, 
                                                        self.socketconf['file'],
                                                        RequestHandlerClass)
        #setting correct permissions and stuff for the socket file
        if "mode" in self.socketconf:
            self.loghandle.debug("setting mode to %s", self.socketconf['mode'])
            os.chmod(self.socketconf['file'], int(self.socketconf['mode'], 8))
        uid = gid = -1
        if "socketuser" in self.socketconf:
            uid = pwd.getpwnam(self.socketconf['socketuser']).pw_uid
        if "socketgroup" in self.socketconf:
            gid = grp.getgrnam(self.socketconf['socketgroup']).gr_gid
        self.loghandle.debug("setting owner to %s:%s", uid, gid)
        os.chown(self.socketconf['file'], uid, gid)
        self.loghandle.debug(" Done setting up socket server at %s",
                             self.socketconf['file'])

    def processStart(self):
        if self._dropToUser(self.socketconf['user'], self.socketconf['group']):
            
            self.serve_forever()
        else:
            return None

    def _dropToUser(self, user, group):
        rtn = False
        cur_user = os.getuid()
        cur_group = os.getgid()
        print user
        if user:
            try:
                running_uid = pwd.getpwnam(user).pw_uid
            except KeyError as e:
                self.loghandle.critical(e)
                return False
        else:
            running_uid = cur_user
        if group:
            try:
                running_gid = grp.getgrnam(group).gr_gid
            except KeyError as e:
                self.loghandle.critical(e)
                return False
        else:
            running_gid = cur_group
        # Remove group privileges
        # Ensure a very conservative umask
        old_umask = os.umask(077)
        if os.getuid() != 0:
            if cur_user != running_uid:
                self.loghandle.critical('Not running as root, unable to drop to configged user')
                
            elif cur_group != running_gid:
                self.loghandle.critical('Not running as root, unable to drop to configged group')
            else:
                rtn=True
        else:
            os.setgroups([])
            os.setgid(running_gid)
            os.setuid(running_uid)
            self.loghandle.info('Dropped to %s:%s', user, group)
            rtn = True
        return rtn
