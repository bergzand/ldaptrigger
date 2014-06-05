import os
import pwd
import grp
import sys
import importlib
import Queue
import multiprocessing
import subprocess

class hookhandler:
    #initialize hookhandler and start thread
    def __init__(self, hookconf, loghandle, queue):
        self.hookconf = dict(hookconf)
        self.hookdir = self.hookconf['hookdir']
        self.queue = queue
        self.loghandle = loghandle
        self.hooks = self.gethooks()
        self.loghandle.debug("starting thread")
        p = multiprocessing.Process(target=self.run)
        p.daemon = True
        p.start()

    def _dropToUser(self, user, group):
        if os.getuid() != 0:
            self.loghandle.info('Not running as root, unable to drop to configged user')
            # We're not root so, like, whatever dude
            return
        # Get the uid/gid from the name
        running_uid = pwd.getpwnam(user).pw_uid
        running_gid = grp.getgrnam(group).gr_gid
        # Remove group privileges
        os.setgroups([])
        # Try setting the new uid/gid
        self.loghandle.info('Dropping to %s:%s', user, group)
        os.setgid(running_gid)
        os.setuid(running_uid)
        # Ensure a very conservative umask
        old_umask = os.umask(077)

    def inithooks(self):
        pass

    #function to thread with, should listen on the queue
    def run(self):
        self.inithooks()
        self._dropToUser(self.hookconf['user'], self.hookconf['group'])
        while True:
            item = self.queue.get()
            self.loghandle.debug("queue item: %s", item)
            reqdn, reqmod, reqresult = item
            self.handle(reqdn, reqmod, reqresult)
            self.queue.task_done()


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
            pyhook.handle(dn, reqmod, reqresult)

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
        print "__init__ pyhook now"
        pass

    def inithook(self, loghandle):
        self.loghandle = loghandle
        self.loghandle.debug("initializing hook now")
   
    def handle(self, dn, reqmod, reqresult):
        pass
