import os

workers = 2
port = int(os.environ.get("PORT", 8060))
bind = "0.0.0.0:%s" % port
logger_class = "snekbox.GunicornLogger"
access_logformat = "%(m)s %(U)s%(q)s %(s)s %(b)s %(L)ss"
access_logfile = "-"
