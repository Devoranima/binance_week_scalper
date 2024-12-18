import logging
import os


grey = "\x1b[38;20m"
yellow = "\x1b[33;20m"
red = "\x1b[31;20m"
bold_red = "\x1b[31;1m"
reset = "\x1b[0m"

dbg_fmt  = "DBG: %(module)s: %(lineno)d: %(msg)s"
info_fmt = "%(asctime)s - %(msg)s"
warning_fmt = "%(asctime)s - %(name)s - %(msg)s"
err_fmt  = "%(asctime)s - %(name)s - %(levelname)s - %(msg)s (%(filename)s:%(lineno)d)"

class adaptiveFormatter(logging.Formatter):
    
    def __init__(self, fmt=None, datefmt=None, style='%', validate=True, *,
                 defaults=None):
        #if (fmt != None):
        #    fmt = fmt
        #else:
        #    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
            
        if datefmt == None:
            datefmt = "%Y-%m-%d %H:%M"

        self.FORMATS = {
            logging.DEBUG: grey + dbg_fmt + reset,
            logging.INFO: grey + info_fmt + reset,
            logging.WARNING: yellow + warning_fmt + reset,
            logging.ERROR: red + err_fmt + reset,
            logging.CRITICAL: bold_red + err_fmt + reset
        }
        
        self.params = dict(
            style = style,
            datefmt = datefmt,
            validate = validate,
            defaults = defaults
        )

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, **self.params)
        return formatter.format(record)


LOG_FOLDER = os.path.join(os.getcwd(), "logs")

def getLogPath (name: str):
    return os.path.join(LOG_FOLDER, name)

