import logging

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# The background is set with 40 plus the number of the color, and the foreground with 30

# These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


COLORS = {
    'WARNING': YELLOW,
    'INFO': GREEN,
    'DEBUG': WHITE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, datefmt=None, use_color=True):
        super().__init__(msg, datefmt)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return super().format(record)


# TODO: read setting to set log level
def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    file_formatter = ColoredFormatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
    file_handlder = logging.FileHandler('/tmp/infnote_chain.log')
    file_handlder.setLevel(logging.DEBUG)
    file_handlder.setFormatter(file_formatter)

    stream_formatter = ColoredFormatter('[%(asctime)s,%(msecs)03d][%(levelname)s] %(message)s', '%H:%M:%S')
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(stream_formatter)

    logger.addHandler(file_handlder)
    logger.addHandler(stream_handler)

    return logger


default_logger = get_logger('infnote_chain')
