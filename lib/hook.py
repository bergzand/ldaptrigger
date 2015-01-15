import os
import pwd
import grp
import sys
import importlib
import Queue
import multiprocessing
import subprocess
import traceback


class hookhandler(multiprocessing.Process):
    #initialize hookhandler and start thread
    def __init__(self, hookconf, loghandle, queue, event):
        self.hookconf = dict(hookconf)
        self.hookdir = self.hookconf['hookdir']
        self.queue = queue
        self.loghandle = loghandle
        self.successevent = event
        self.hooks = self.gethooks()
        self.loghandle.debug("starting thread")
        multiprocessing.Process.__init__(self)
        self.exit = multiprocessing.Event()
   
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
        else:
            running_uid = cur_user
        if group:
            try:
                running_gid = grp.getgrnam(group).gr_gid
            except KeyError as e:
                self.loghandle.critical(e)
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

    def run(self):
        """function to thread with, should listen on the queue
        """
        self.inithooks()
        user = self.hookconf.get('user', None)
        group = self.hookconf.get('group', None)
        if not self._dropToUser(user, group):
            self.exit.set()
        else:
            self.successevent.set()
        while not self.exit.is_set():
            try:
                item = self.queue.get(timeout=0.3)
            except Queue.Empty:
                continue
            #self.loghandle.debug("queue item: %s", item)
            reqdn, reqmod, reqresult = item
            self.handle(reqdn, reqmod, reqresult)
        self.loghandle.critical("caught exitsignal, exiting")

    def shutdown(self):
        self.exit.set()


class exechookhandler(hookhandler):
    
    def _getfiles(self):
        self.loghandle.info("getting al hooks from %s", self.hookdir)
        for root, dirs, files in os.walk(self.hookdir):
            for file in files:
                hook = os.path.join(root, file)
                if os.access(hook, os.X_OK):
                    self.loghandle.debug("found executable %s", file)
                    yield hook

    def handle(self, dn, reqmod, reqresult):
        for exechook in self.exechooks:
            p = subprocess.Popen([exechook, str(dn), str(reqmod), str(reqresult)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if stdout:
                for line in stdout.splitlines():
                    self.loghandle.info(line.strip())
            if stderr:
                 for errors in stderr.splitlines():
                    self.loghandle.error(errors)
            #self.loghandle.info("got output: %s", output)

    def gethooks(self):
        exechooks = []
        for hook in self._getfiles():
            exechooks.append(hook)
        self.exechooks = exechooks

    def inithooks(self):
        pass


class pyhookhandler(hookhandler):
    #get all python modules in a dir
    def _getfiles(self):
        self.loghandle.info("getting al pyhooks from %s", self.hookdir)
        #build a list of file in the hookdir
        for root, dir, files in os.walk(self.hookdir):
            for file in files:
                self.loghandle.debug("found file: %s", self.hookdir)
                if file.endswith(".py"):
                    file = file.split('.')[0]
                    self.loghandle.debug("%s is a hook", os.path.join(root,file))
                    yield file
                else:
                    self.loghandle.debug("%s is not a correct hook",os.path.join(root,file))

    #execute all python modules found by gethooks
    def handle(self, dn, reqmod, reqresult):
        self.loghandle.info("executing hooks")
        for pyhook in self.hooks:
            self.loghandle.debug("Executing %s", pyhook)
            result = pyhook.handle(dn, reqmod, reqresult)
            self.loghandle.debug("Result: %s", result)

    def inithooks(self):
        self.loghandle.info("initializing hooks")
        for pyhook in self.hooks:
            self.loghandle.debug("initializing: %s", pyhook)
            pyhook.inithook(loghandle=self.loghandle)
            

    
    #initialize the hooks
    def gethooks(self):
        #building path
        sys.path.append(os.path.join(os.getcwd(), self.hookdir))
        pyhooks = []
        hookgen = self._getfiles()
        for hook in hookgen:
            self.loghandle.debug("importing hook %s", hook)  
            pyhook = importlib.import_module(hook)
            pyhooks.append(pyhook.Hook())
        return pyhooks


class pyhook:
    def __init__(self):
        print "init pyhook now"
        pass

    def inithook(self, loghandle):
        self.loghandle = loghandle
        self.loghandle.debug("initializing hook now")
   
    def handle(self, dn, reqmod, reqresult):
        return True
