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
import Queue
import multiprocessing

loghandle = None
registeredhooks = []


def registerhook(hookconf):
    hookcfg = dict(hookconf)
    hookclass = config.getHookType(hookcfg['hooktype'])
    hookqueue = Queue.Queue()
    hookname = hookcfg[config.HOOKNAME]
    hooklevel = hookcfg[config.LOGLEVEL]
    hookthread = hookclass(hookconf,
                           logobject.getLoggerHandle(hookname, hooklevel),
                           hookqueue)
    registeredhooks.append((hook, hookthread, hookqueue))


def callback(request):
    requesthook, dn, mod, result = request
    item = (dn, mod, result)
    loghandle.debug("checking hooks for matching type")
    for hook, hookthread, hookqueue in registeredhooks:
        loghandle.debug("trying to match \"%s\" with \"%s\"", requesthook, hook)
        if hook == requesthook:
            loghandle.debug("dispatching item to queue")
            hookqueue.put(item)

#main function
if __name__ == '__main__':
    #load config
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
    serverprocess = multiprocessing.Process(target=server.processStart)
    serverprocess.daemon=True
    serverprocess.start()
    serverprocess.join()