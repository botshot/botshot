#!/usr/bin/env python3
import argparse
import signal
import subprocess
import sys
import os

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

def process_template(text, app_name):
    return text.replace("{APP_NAME}", app_name)


def install_skeleton(dest_dir):
    if not os.path.isdir(dest_dir):
        raise ValueError("{} is not a directory".format(dest_dir))

    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'botshot/bootstrap'))

    print('Installing botshot files from {}'.format(src_dir))

    app_name = os.path.basename(os.path.normpath(dest_dir))

    for root, dirs, files in os.walk(src_dir):

        print('Copying directory {}'.format(root))
        rel_dir = os.path.relpath(root, src_dir)

        for name in dirs:
            dest = os.path.join(dest_dir, rel_dir, name)
            print("Create", dest)
            os.mkdir(dest, 0o755)

        for name in files:
            if not name.endswith('.tpl'):
                continue
            new_name = name.rsplit('.tpl', 1)[0]

            src = os.path.join(root, name)
            dest = os.path.join(dest_dir, rel_dir, new_name)
            print("Copy", src, dest)

            with open(src, 'r') as f:
                file_content = process_template(f.read(), app_name)
            with open(dest, 'w') as f:
                f.write(file_content)

    print("Adding settings.py imports ...")
    with open(os.path.join(dest_dir, "settings.py"), "r") as f:
        settings_content = f.read()
    # \n is converted by stdlib, stay calm
    settings_content = process_template(CONFIG_STR, app_name) + "\n" + settings_content

    idx = settings_content.find("INSTALLED_APPS")
    idx = settings_content.find("\n", idx)
    settings_content = settings_content[:idx] + APPS_STR + settings_content[idx:]

    with open(os.path.join(dest_dir, "settings.py"), "w") as f:
        f.write(settings_content)


def init_project(bot_name=None):
    import botshot.bootstrap

    if not bot_name:
        bot_name = input("How do you want to call your chatbot?\n")

    print("Creating Botshot project in {} ...".format(bot_name))

    retval = subprocess.call(['django-admin', 'startproject', bot_name])
    # TOOD print output to stdout+stderr

    if retval != 0:
        print("Error: Can't create django project!")
        exit(1)

    print("Creating skeleton project ...")
    # install skeleton to django project module
    project_path = os.path.abspath(os.path.join(os.getcwd(), bot_name, bot_name))
    install_skeleton(project_path)

    print("Running django migrate ...")
    # TODO: which python version should we call? can we call this programmatically?
    #retval = subprocess.call(['python3', './manage.py', 'migrate'])
    #if retval != 0:
    #    print("Error in manage.py migrate", file=sys.stderr)
    #    exit(1)

    print("Everything looks OK!")
    print("You can start the server inside the directory with: botshot start [django-app]")


def start(djangoapp):
    # TODO handle errors

    print("Starting Redis database ...")
    redis = subprocess.Popen(["redis-server"])

    print("Starting Celery ...")
    django = subprocess.Popen(["celery", "-A", djangoapp, "worker"])

    print("Starting Django ...")
    # TODO: which python should we call? can we call this programmatically?
    celery = subprocess.Popen(["python3", "./manage.py", "runserver"])

    while True:
        try:
            c = sys.stdin.read(1)
        except KeyboardInterrupt:
            break

    print("Stopping ...")
    os.kill(celery.pid, signal.SIGTERM)
    os.kill(django.pid, signal.SIGTERM)
    os.kill(redis.pid, signal.SIGTERM)
    # Newline to show that we are finished
    print('')


def main():
    argp = argparse.ArgumentParser(description="Botshot framework configuration utility")
    argp.add_argument('command', nargs=1, type=str, help="One of: init, start, help")
    argp.add_argument('djangoapp', nargs='?', help="Name of your django app.")

    args = argp.parse_args()
    command = args.command[0]

    if command == 'init':
        init_project(args.djangoapp)
    elif command == 'start':
        if args.djangoapp is None:
            argp.error("Django app name must be specified.")
        djangoapp = args.djangoapp
        start(djangoapp)
    elif command == 'help':
        argp.print_help()
        exit(0)
    else:
        print("Unknown command {}".format(command))
        argp.print_usage()
        exit(1)


if __name__ == "__main__":
    main()