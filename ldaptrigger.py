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

#main function
if __name__ == '__main__':
    #load config
    config = config.cfg('ldaptrigger.conf')
    #set up logging
    logding = log.log("blaat")
    logding.setConf(config.getLoggerCfg())
    #get loghandle
    loghandle = logding.getLoggerHandle("main")
    #add logging to the config functions
    config.addLogging(logding)
    #get list of hooks
    hooklist = config.getHookList()
    #register each hook in array
    for type, hook, dir, name in hooklist:
        registerhook(type, hook, dir, name)
    socketconf = config.getSocketInfo()
    server = udsserver.udsserver(socketconf,
                                 lambda *args, **keys: 
                                     udsserver.udshandler(logding, callback, *args, **keys)
                                 , logding)
    try:
        server.serve_forever()
    except:
        traceback.print_tb()
        traceback.print_exception()
    finally:
        server.shutdown()
