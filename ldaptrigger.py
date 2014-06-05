#!/usr/bin/env python
'''
Documentation, License etc.

@package ldaptrigger
'''
import lib.conf as config
import lib.log as log
import lib.udsserver as udsserver
import lib.hook as hook

import os
import subprocess
import SocketServer
import traceback
import sys
from multiprocessing import Process, Queue
import signal

loghandle = None
registeredhooks = []


def signalhandler(signum=None, frame=None):
    loghandle.info("caught signal: %s", signum)
    #shutdownServer()
    shutdownProcesses()
    sys.exit(0)

def registerhook(hookconf):
    hookcfg = dict(hookconf)
    hookclass = config.getHookType(hookcfg['hooktype'])
    hookqueue = Queue()
    hookname = hookcfg[config.HOOKNAME]
    hooklevel = hookcfg[config.LOGLEVEL]
    hookprocess = hookclass(hookconf,
                           logobject.getLoggerHandle(hookname, hooklevel),
                           hookqueue)
    hookprocess.start()
    registeredhooks.append((hookname, hook, hookprocess, hookqueue))


def callback(request):
    requesthook, dn, mod, result = request
    item = (dn, mod, result)
    loghandle.debug("checking hooks for matching type")
    for hookname, hook, hookprocess, hookqueue in registeredhooks:
        loghandle.debug("trying to match \"%s\" with \"%s\"", requesthook, hookname)
        if hook == requesthook:
            loghandle.debug("dispatching item to queue")
            hookqueue.put(item)


def shutdownProcesses():
    for hookname, hook, hookprocess, hookqueue in registeredhooks:
        hookprocess.shutdown()
        loghandle.info("shutting down %s", hookname)
        hookqueue.close()


def shutdownServer():
    serverprocess.terminate()


#main function
if __name__ == '__main__':
    #load config
    signal.signal(15, signalhandler)
    config = config.cfg('ldaptrigger.conf')
    #set up logging
    logobject = log.log(config.getLoggerCfg("main"))
    #get loghandle
    loghandle = logobject.getLoggerHandle("main")
    #add logging to the config functions
    config.addLogging(logobject)
    #get list of hooks
    loghandle.debug("Buidling hooklist")
    hooklist = config.getHookList()
    #register each hook in array
    for conf in hooklist:
        registerhook(conf)
    socketconf = config.getSectionCfg("socket")
    server = udsserver.udsserver(socketconf,
                                 lambda *args, **keys: 
                                     udsserver.udshandler(logobject, callback, *args, **keys)
                                 , logobject)
    serverprocess = Process(target=server.processStart)
    serverprocess.daemon=True
    serverprocess.start()
    serverprocess.join()
