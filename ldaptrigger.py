#!/usr/bin/env python
'''
Documentation, License etc.

@package ldaptrigger
'''
import ldaptrigger.conf as config
import ldaptrigger.log as log
import ldaptrigger.udsserver as udsserver
import ldaptrigger.hook as hook

import os
import subprocess
import SocketServer
import traceback
import sys
from multiprocessing import Process, Queue, Event
import signal

loghandle = None
registeredhooks = []


def signalhandler(signum=None, frame=None):
    loghandle.info("caught signal: %s", signum)
    #shutdownServer()
    shutdownProcesses()
    sys.exit(0)


def registerhook(hookconf):
    """Start and register a hook

    :param hookconf: A dict with the config of the hook to register
    """
    rtn = False
    hookcfg = dict(hookconf)
    hookclass = config.getHookType(hookcfg['hooktype'])
    hookqueue = Queue()
    hookname = hookcfg[config.HOOKNAME]
    hooklevel = hookcfg[config.LOGLEVEL]
    hookevent = Event()
    hookprocess = hookclass(hookconf,
                            logobject.getLoggerHandle(hookname, hooklevel),
                            hookqueue,
                            hookevent
                            )
    hookprocess.start()
    if hookevent.wait(2.0):
        registeredhooks.append((hookname, hookcfg, hookprocess, hookqueue))
        rtn = True
    else:
        loghandle.critical("Failed to start hook process {}".format(hookname))
        rtn = False
    return rtn


def callback(request):
    requesthook, dn, mod, result = request
    item = (dn, mod, result)
    loghandle.debug("checking hooks for matching type")
    for hookname, hookcfg, hookprocess, hookqueue in registeredhooks:
        loghandle.debug("trying to match \"%s\" with \"%s\"", requesthook, hookcfg[config.HOOKHOOK])
        if hookcfg[config.HOOKHOOK] == requesthook and dn.lower().endswith(hookcfg[config.HOOKBASEDN]):
            loghandle.debug("dispatching item to queue")
            hookqueue.put(item)


def shutdownProcesses():
    for hookname, hook, hookprocess, hookqueue in registeredhooks:
        hookprocess.shutdown()
        loghandle.info("shutting down %s", hookname)
        hookqueue.close()


def shutdownServer():
    serverprocess.terminate()


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
        if not registerhook(conf):
            break
    else:
        socketconf = config.getSectionCfg("socket")
        server = udsserver.udsserver(socketconf,
                                     lambda *args, **keys: udsserver.udshandler(logobject, callback, *args, **keys), logobject)
        serverprocess = Process(target=server.processStart)
        serverprocess.start()
        serverprocess.join()
    loghandle.info("Exiting")
