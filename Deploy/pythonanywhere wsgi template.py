# PythonAnywhere WSGI config template for anllms.
#
# This file is NOT run as part of this repo. PythonAnywhere generates its
# own WSGI config file per web app (Web tab -> "WSGI configuration file"
# link), and you paste the contents below into THAT file, editing the two
# placeholders first. This template just keeps a version-controlled record
# of what that file should contain.
#
# DO NOT commit your real API key anywhere in this repo. The API key line
# below only ever lives in the PythonAnywhere-hosted copy of this file,
# which is not part of git and is not pushed back to GitHub.

import sys
import os

# 1. Replace with the path where you cloned the repo on PythonAnywhere,
#    e.g. '/home/yourusername/anllms' (the folder containing pyproject.toml).
project_home = "/home/YOUR_PYTHONANYWHERE_USERNAME/anllms"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 2. Replace with your real Anthropic API key. This file lives only on
#    PythonAnywhere's server, never in git, so this is safe here.
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-REPLACE-WITH-YOUR-REAL-KEY"

# Optional: turn on chat transcript logging the same way ANLLMS_CHAT_LOG=1
# does in Codespaces. Comment out to disable.
os.environ["ANLLMS_CHAT_LOG"] = "1"

from chat.server import app as application  # noqa: E402
