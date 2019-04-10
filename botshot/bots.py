#!/usr/bin/env python
import argparse
import signal
import subprocess
import sys
import os
from django.core.management import execute_from_command_line
from shutil import copyfile, rmtree, move
import time
import atexit
import tempfile

APPS_STR = """
    'botshot.apps.BotshotConfig',
    'botshot.webchat',

"""

PYTHON_BINARY_PATH = sys.executable

DEFAULT_BOT_APP_NAME = 'bot'

def install_skeleton(project_app_dir):
    if not os.path.isdir(project_app_dir):
        raise ValueError("{} is not a directory".format(project_app_dir))

    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bootstrap'))

    print('Installing botshot files from {}'.format(src_dir))

    for root, dirs, files in os.walk(src_dir):
        rel_dir = os.path.relpath(root, src_dir)

        for name in dirs:
            dest = os.path.join(project_app_dir, rel_dir, name)
            os.mkdir(dest, 0o755)

        for name in files:
            if not name.endswith('.tpl'):
                continue
            new_name = name.rsplit('.tpl', 1)[0]

            src = os.path.join(root, name)
            dest = os.path.join(project_app_dir, rel_dir, new_name)
            copyfile(src, dest)

    with open(os.path.join(project_app_dir, "settings.py"), "r") as f:
        settings_content = f.read()

    with open(os.path.join(src_dir, "botshot_settings.py"), "r") as f:
        botshot_settings = f.read()

    settings_content = settings_content + "\n" + botshot_settings

    idx = settings_content.find("INSTALLED_APPS")
    idx = settings_content.find("\n", idx)
    settings_content = settings_content[:idx] + APPS_STR + settings_content[idx:]

    with open(os.path.join(project_app_dir, "settings.py"), "w") as f:
        f.write(settings_content)

def fail(message):
    eprint(message)
    exit(1)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def init_project(args):
    project_path = args.name

    if not project_path:
        raise AttributeError('Project path cannot be null.')

    print("Creating Botshot project in {} ...".format(project_path))

    if os.path.exists(project_path):
        fail("Error: Project directory already exists: {}".format(project_path))

    # Create project in temporary directory to avoid problems with half-initialized projects
    tmp_path = tempfile.mkdtemp()
    try:
        retval = subprocess.call(['django-admin', 'startproject', DEFAULT_BOT_APP_NAME, tmp_path])

        if retval != 0:
            fail("Error: Can't create django project!")

        print("Copying project files...")
        # install skeleton to django project module
        project_app_path = os.path.abspath(os.path.join(tmp_path, DEFAULT_BOT_APP_NAME))
        install_skeleton(project_app_path)


        print("Initializing database ...")
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", DEFAULT_BOT_APP_NAME + ".settings")
        sys.path.append(tmp_path)
        execute_from_command_line(['_', 'migrate'])

    except Exception as e:
        # Remove temp directory if initialization fails
        rmtree(tmp_path)
        raise e

    # Move final directory to target path (note: rename can't be used, this may be on another filesystem)
    move(tmp_path, project_path)

    print("New project initialized in: {}".format(project_path))
    print("You can start the server inside the directory with: bots start")


PROCESSES = {}

def start_subprocess(name, args):
    if name in PROCESSES:
        raise AttributeError('Name {} already found in PROCESSES.'.format(name))
    PROCESSES[name] = subprocess.Popen(args)

def start(args):
    app_name = args.app or DEFAULT_BOT_APP_NAME

    if not os.path.exists("./manage.py"):
        fail("Not a Botshot project. Run from a project's root folder.")

    atexit.register(exit_and_close)

    # start_subprocess('Redis Database', ["redis-server"])
    start_subprocess('Celery Worker', ["celery", "-A", app_name, "worker", "-l", "info", "--concurrency", "1"])
    start_subprocess('Celery Beat', ["celery", "-A", app_name, "beat", "-l", "info"])

    # Give some time to Redis and Celery to start
    time.sleep(0.5)
    # Run django development server. Don't reload on file changes until celery worker reload is implemented.
    start_subprocess('Django Webserver', [PYTHON_BINARY_PATH, "./manage.py", "runserver", "-v", "0", "--noreload"])

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
        proc.terminate()
    # Newline to show that we are finished
    time.sleep(1.0)
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

    parser = argparse.ArgumentParser(description="Botshot framework configuration utility")
    subparsers = parser.add_subparsers(help='Choose one of given commands')

    parser_init = subparsers.add_parser('init', help='Create new Botshot project')
    parser_init.add_argument('name', type=str, help='Project name or path')
    parser_init.set_defaults(func=init_project)

    parser_start = subparsers.add_parser('start', help='Run Botshot server in development mode')
    parser_start.add_argument('app', default=DEFAULT_BOT_APP_NAME, nargs='?', help='Name of botshot app')
    parser_start.set_defaults(func=start)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_usage()
        exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
