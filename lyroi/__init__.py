from datetime import datetime
from importlib.metadata import version, PackageNotFoundError, metadata
import re
import sys
import signal

__package__ = "lyroi"
creation_date = datetime(2025, 11, 26)

try:
    __version__ = version(__package__)
except PackageNotFoundError:
    __version__ = "0.0.0"

meta = metadata(__package__)
email_list = meta.get("Author-email", "")
author_str = re.sub(r"<[^>]*>", "", email_list).strip()
now_date = datetime.now()
date_str = now_date.strftime("%Y") if creation_date.year == now_date.year else creation_date.strftime("%Y") + "-" + now_date.strftime("%Y")
__copyright__ = "Copyright (c) " + date_str + " " + author_str + ", www.hzdr.de"
__license__ = meta.get("License-Expression")

__legal__ = ("Notes:\n"
            "  This software is intended for research use only.\n"
            "  It is not a medical device and must not be used for clinical decisions.\n\n"
            f"{__package__} {__version__}\n"
            f"{__copyright__}\n"
            f"License: {__license__}; models are licensed separately")

def error_handler(exctype, value, traceback):
  print()
  print("Error:", value, file=sys.stderr)
  sys.exit(1)

def exit_handler(signal, frame):
  print()
  print("User abort (CTRL-C) received.")
  sys.exit(0)

signal.signal(signal.SIGINT, exit_handler)
sys.excepthook = error_handler