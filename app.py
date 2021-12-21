from flask import Flask, render_template, request
import git
import os
import re
import subprocess
import shutil
from pathlib import Path
from dotenv import load_dotenv

# load settings from environment or from .env
load_dotenv(verbose=True)

PERSISTENT_DATA_MOUNT_POINT = os.getenv("PERSISTENT_DATA_MOUNT_POINT")
PAAS_WEB_ADDRESS = os.getenv("PAAS_WEB_ADDRESS")

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
# Tell uwsgi where the wsgi app is
wsgi-file = %d/app.wsgi

# Set the current working direcotry for the app
chdir = %d
"""


@app.route("/", methods=["POST"])
def go():
    try:
        remote = request.form.get("repo", None)
        subdomain = make_subdomain(remote)
        breakpoint()
        # Remove old repo if present
        shutil.rmtree(
            f"{PERSISTENT_DATA_MOUNT_POINT}/{subdomain}", ignore_errors=True
        )  # noqa
        # Create directory for site
        os.mkdir(f"{PERSISTENT_DATA_MOUNT_POINT}/" + subdomain)
        savePath = f"{PERSISTENT_DATA_MOUNT_POINT}/{subdomain}/"
        git.Repo.clone_from(remote, savePath, branch="main")
        webaddress = f"https://{subdomain}.{PAAS_WEB_ADDRESS}"
        # Write wsgi file
        with open(savePath + "/app.wsgi", "w") as fp:
            fp.write("from app import app as application")
        # Create virtualenv & install app requirements to it
        print("Creating virtualenv")
        subprocess.call(
            f"python3 -m venv {savePath}venv",  # noqa
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
                    hostname=make_subdomain(remote) + ".{PAAS_WEB_ADDRESS}"
                )
            )

    except Exception as e:
        print(e)
        return "Error", 500

    # Force a reload of the app
    path = Path(f"{savePath}" + "app.wsgi")
    path.touch(exist_ok=True)

    return render_template("complete.html", webaddress=webaddress)
