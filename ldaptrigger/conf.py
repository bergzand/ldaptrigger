import ConfigParser

class cfg:
    
    #logstuf
    LOGNAME = "cfg"
    
    #section info
    MAIN = "main"
    LOGGING = "logging"
    SOCKET = "socket"
    #hook section info
    HOOKTYPE = "hooktype"
    HOOKNAME = "hookname"
    HOOKHOOK = "hook"
    HOOKDIR = "hookdir"
    HOOKBASEDN = "basedn"
    LOGLEVEL = "loglevel"
    
    DEFAULTS = {'loglevel': 'WARNING',
                'hooktype': 'python',
                'basedn': '',
                }

    def __init__(self, file):

        self.cfparser = ConfigParser.SafeConfigParser(cfg.DEFAULTS, allow_no_value=True)
        with open(file, 'r') as f:
            self.cfparser.readfp(f)

    def getLoggerCfg(self, section):
        returndata = None
        if not self.cfparser.has_section(section):
            returndata = False
        else:
            confdata = (self.cfparser.get(section, "logfile"),
                        self.cfparser.get(section, "loglevel"))
            returndata = confdata
        return returndata

    def getHookList(self):
        hooksections = self.cfparser.sections()
        hooks = []
        for hook in hooksections:
            if "hook/" in hook:
                self.loghandle.debug("Found section: %s", hook)
                hookconf = self.getSectionCfg(hook)
                hookconf.append((cfg.HOOKNAME, hook))
                hooks.append(hookconf)
        self.loghandle.info("Got %s from hooks in config", hooks)
        return hooks

    def getSectionCfg(self,section):
        return self.cfparser.items(section)

    @staticmethod
    def getHookType(type):
        import hook
        return {
            'python': hook.pyhookhandler,
            'exec': hook.exechookhandler,
            }.get(type, hook.exechookhandler)

    def addLogging(self, logger):
        self.loghandle = logger.getLoggerHandle(cfg.LOGNAME)

class cfsettings:
    def __init__(self):
        pass

    def getLogConf(self):
        pass
