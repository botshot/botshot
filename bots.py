#!/usr/bin/env python
import argparse
import signal
import subprocess
import sys
import os
from django.core.management import execute_from_command_line
from shutil import copyfile
import time
import atexit

CONFIG_STR = """
import os

BOT_CONFIG = {
    "BOTS": {
        "{APP_NAME}/bots/default.yaml"
    },
    "REDIS_URL": os.environ.get('BOTSHOT_REDIS_URL', "redis://localhost:6379/"),
    'DEPLOY_URL': os.environ.get('BOTSHOT_DEPLOY_URL', 'http://localhost:8000/'),
    'MSG_LIMIT_SECONDS': 20,
}

CELERY_BROKER_URL = BOT_CONFIG.get('REDIS_URL').rstrip("/")+'/1'
CELERY_RESULT_BACKEND =  CELERY_BROKER_URL

"""

APPS_STR = """
    'botshot',
    'botshot.webgui',
"""

PYTHON_BINARY_PATH = sys.executable

BOT_APP_NAME = 'bot'

def install_skeleton(project_app_dir):
    if not os.path.isdir(project_app_dir):
        raise ValueError("{} is not a directory".format(project_app_dir))

    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'botshot/bootstrap'))

    print('Installing botshot files from {}'.format(src_dir))

    for root, dirs, files in os.walk(src_dir):

        print('Copying directory {}'.format(root))
        rel_dir = os.path.relpath(root, src_dir)

        for name in dirs:
            dest = os.path.join(project_app_dir, rel_dir, name)
            print("Create", dest)
            os.mkdir(dest, 0o755)

        for name in files:
            if not name.endswith('.tpl'):
                continue
            new_name = name.rsplit('.tpl', 1)[0]

            src = os.path.join(root, name)
            dest = os.path.join(project_app_dir, rel_dir, new_name)
            print("Copy", src, dest)
            copyfile(src, dest)

    print("Adding settings.py imports ...")
    with open(os.path.join(project_app_dir, "settings.py"), "r") as f:
        settings_content = f.read()
    # \n is converted by stdlib, stay calm
    settings_content = CONFIG_STR + "\n" + settings_content

    idx = settings_content.find("INSTALLED_APPS")
    idx = settings_content.find("\n", idx)
    settings_content = settings_content[:idx] + APPS_STR + settings_content[idx:]

    with open(os.path.join(project_app_dir, "settings.py"), "w") as f:
        f.write(settings_content)


def init_project(project_path):
    if not project_path:
        # TODO: Should be handled in the future by required argparse attribute
        raise AttributeError('Project path cannot be null.')

    print("Creating Botshot project in {} ...".format(project_path))

    try:
        os.makedirs(project_path, exist_ok=False)
    except FileExistsError:
        print("Error: Project directory already exists: {}".format(project_path))

    retval = subprocess.call(['django-admin', 'startproject', BOT_APP_NAME, project_path])
    # TOOD print output to stdout+stderr

    if retval != 0:
        print("Error: Can't create django project!")
        exit(1)

    print("Copying project files...")
    # install skeleton to django project module
    project_app_path = os.path.abspath(os.path.join(project_path, BOT_APP_NAME))
    install_skeleton(project_app_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", BOT_APP_NAME + ".settings")

    print("Initializing database ...")
    sys.path.append(project_path)
    execute_from_command_line(['_', 'migrate'])

    print("Everything looks OK!")
    print("You can start the server inside the directory with: botshot start")

PROCESSES = {}

def start_subprocess(name, args):
    if name in PROCESSES:
        raise AttributeError('Name {} already found in PROCESSES.'.format(name))
    PROCESSES[name] = subprocess.Popen(args)

def start():
    atexit.register(exit_and_close)

    start_subprocess('Redis Database', ["redis-server"])
    start_subprocess('Celery Worker', ["celery", "-A", BOT_APP_NAME, "worker"])
    start_subprocess('Django Webserver', [PYTHON_BINARY_PATH, "./manage.py", "runserver"])

    # Wait for first finished process (or for user's interruption)
    while True:
        try:
            for name, proc in PROCESSES.items():
                exit_code = proc.poll()
                if exit_code is not None:
                    print('{} exited.'.format(name))
                    sys.exit(1)
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(1)

def exit_and_close():
    print("Stopping...")
    for name, proc in PROCESSES.items():
        try:
            os.kill(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    # Newline to show that we are finished
    time.sleep(0.2)
    print('-'*80)
    print('Botshot stopped.')
    print('-'*80)
    exit(1)

def _yesno(query):
    reply = input(query)
    while True:
        reply = reply.strip()
        if reply in ["y", "Y"]:
            return True
        elif reply in ["n", "N"]:
            return False
        else:
            reply = input("Invalid input. Please reply either y or n.")


def main():

    if sys.version_info >= (3, 7):
        ok = _yesno("Warning: Python 3.7 is not supported yet due to Celery dependency. Do you want to continue? [y/n]")
        if not ok:
            exit(1)
    elif sys.version_info < (3, 5):
        print("Your Python version is not supported. Please update to Python 3.5 or 3.6.")
        exit(1)

    argp = argparse.ArgumentParser(description="Botshot framework configuration utility")
    argp.add_argument('command', nargs=1, type=str, help="One of: init, start, help")
    argp.add_argument('djangoapp', nargs='?', help="Name of your django app.")

    args = argp.parse_args()
    command = args.command[0]

    if command == 'init':
        init_project(args.djangoapp)
    elif command == 'start':
        start()
    elif command == 'help':
        argp.print_help()
        exit(0)
    else:
        print("Unknown command {}".format(command))
        argp.print_usage()
        exit(1)


if __name__ == "__main__":
    main()
