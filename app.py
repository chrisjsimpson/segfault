from flask import Flask, render_template, request
from uuid import uuid4
import git
import os
import re

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
        # Create directory for site
        uuid = str(uuid4())
        os.mkdir("./sites/" + uuid)
        savePath = f"./sites/{uuid}/"
        git.Repo.clone_from(remote, savePath, branch="main")
        subdomain = make_subdomain(remote)
        # Write wsgi file
        with open(savePath + "/site.wsgi", "w") as fp:
            fp.write("from app import app as application")
        # Write vassal file
        with open(savePath + subdomain + "-vassal.ini", "w") as fp:
            fp.write(
                vassal_template.format(
                    hostname=make_subdomain(remote) + ".segfault.app"
                )
            )

    except Exception as e:
        print(e)
        return "Error", 500
    return "OK"
