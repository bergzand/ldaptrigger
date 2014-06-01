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
import threading

loghandle = None
socket_location = "ldaptrigger.sock"
registeredhooks = []


def registerhook(type, hook, dir, name):
    hookclass = config.getHookType(type)
    hookqueue = Queue.Queue()
    hookthread = hookclass(dir, logding.getLoggerHandle(name), hookqueue)
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

if __name__ == '__main__':
    #load config
    config = config.cfg('ldaptrigger.conf')
    #set up logging
    logding = log.log("blaat")
    logding.setConf(config.getLoggerCfg())
    loghandle = logding.getLoggerHandle("main")
    config.addLogging(logding)

    hooklist = config.getHookList()
    for type, hook, dir, name in hooklist:
        registerhook(type, hook, dir, name)
    loghandle.info("setting up socket")
    try:
        os.unlink(socket_location)
        loghandle.debug("removed old socket")
    except:
        pass
    server = udsserver.udsserver(socket_location, 
                                 lambda *args, **keys: 
                                     udsserver.udshandler(logding, callback, *args, **keys)
                                 , logding)
    loghandle.debug("socket ready at %s", socket_location)
    try:
        server.serve_forever()
    except:
        traceback.print_tb()
        traceback.print_exception()
    finally:
        server.shutdown()
