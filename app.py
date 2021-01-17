from flask import Flask, render_template, request
import git
import os
import re
import subprocess
import shutil
from pathlib import Path

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


def make_subdomain(repo):
    """Make subdomain string from repo address

    e.g. https://github.co.uk/files-community/Files.git
    Becomes: files-community-files
    """
    match = re.match(r"^.*\.(com|co.uk|org)/(.*)\.git", repo).group(2)
    match = match.replace("/", "-").lower()
    return match


vassal_template = """
[uwsgi]
strict = true
# %d absolute path of the directory containing the configuration file
# See https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html#magic-variables # noqa
chdir = %d

wsgi-file = %d/site.wsgi
virtualenv = %d/venv
reload-on-exception

processes = 1
threads = 2
master = true
vacuum = true
subscribe-to = /tmp/sock2:{hostname}

socket = /tmp/sockets/%n.sock
"""


@app.route("/", methods=["POST"])
def go():
    try:
        remote = request.form.get("repo", None)
        subdomain = make_subdomain(remote)
        # Remove old repo if present
        shutil.rmtree(f"/root/sites/{subdomain}", ignore_errors=True)
        # Create directory for site
        os.mkdir("/root/sites/" + subdomain)
        savePath = f"/root/sites/{subdomain}/"
        git.Repo.clone_from(remote, savePath, branch="main")
        webaddress = f"https://{subdomain}.segfault.app"
        # Write wsgi file
        with open(savePath + "/site.wsgi", "w") as fp:
            fp.write("from app import app as application")
        # Create virtualenv & install app requirements to it
        print("Creating virtualenv")
        subprocess.call(
            f"export LC_ALL=C.UTF-8; export LANG=C.UTF-8; /root/.local/bin/virtualenv -p python3 {savePath}venv",  # noqa
            cwd=savePath,
            shell=True,
        )
        # Activate virtualenv and install requirements
        subprocess.call(
            f"export LC_ALL=C.UTF-8; export LANG=C.UTF-8; . {savePath}venv/bin/activate;pip install -r {savePath}requirements.txt",  # noqa
            cwd=savePath,
            shell=True,
        )
        # Write vassal file last because app can only boot once requirements are installed # noqa
        with open(savePath + subdomain + "-vassal.ini", "w") as fp:
            fp.write(
                vassal_template.format(
                    hostname=make_subdomain(remote) + ".segfault.app"
                )
            )

    except Exception as e:
        print(e)
        return "Error", 500

    # Force a reload of the app
    path = Path(f"{savePath}" + "site.wsgi")
    path.touch(exist_ok=True)

    return render_template("complete.html", webaddress=webaddress)
