class cfg:
    
    #logstuf
    LOGNAME = "cfg"
    
    #section info
    MAIN = "main"
    LOGGING = "logging"
    #hook section info
    HOOKTYPE = "type"
    HOOKHOOK = "hook"
    HOOKDIR = "dir"
    
    import log
    
    def __init__(self, file):
        import ConfigParser
        self.cfparser = ConfigParser.SafeConfigParser(allow_no_value=True)
        with open(file, 'r') as f:
            self.cfparser.readfp(f)

    def getLoggerCfg(self):
        returndata = None
        if not self.cfparser.has_section(cfg.LOGGING):
            print "no logging info found, exiting"
            returndata = False
        else:
            confdata = dict(logfile=self.cfparser.get(cfg.LOGGING, "logfile"),
                            loglevel=self.cfparser.get(cfg.LOGGING,
                                                       "loglevel"))
            returndata = confdata
        return returndata

    def addLogging(self, logger):
        self.loghandle = logger.getLoggerHandle(cfg.LOGNAME)

    def getHookList(self):
        hooksections = self.cfparser.sections()
        hooks = []
        for hook in hooksections:
            if "hook/" in hook:
                self.loghandle.debug("Found section: %s", hook)
                f = lambda option: self.cfparser.get(hook, option) if self.cfparser.has_option(hook, option) else None
                settings = (f(cfg.HOOKTYPE), f(cfg.HOOKHOOK), f(cfg.HOOKDIR), hook)
                hooks.append(settings)
        self.loghandle.info("Got %s from hooks in config", hooks)
        return hooks

    @staticmethod
    def getHookType(type):
        import hook
        return {
            'python': hook.pyhookhandler,
            'exec': hook.exechookhandler,
            }.get(type, hook.exechookhandler)
