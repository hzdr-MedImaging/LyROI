from datetime import datetime
from importlib.metadata import version, PackageNotFoundError, metadata
import re

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