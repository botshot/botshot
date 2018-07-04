#!/usr/bin/env python3
import argparse
import signal
import subprocess
import sys
import urllib.request
import zipfile

import os


def yesno():
    while True:
        response = input()
        if response.lower() in ['y', 'yes']:
            break
        elif response.lower() in ['n', 'no']:
            exit(-1)


def download_and_unzip(name, weburl):
    bots_file = None

    try:
        print("Downloading {} ...".format(name))
        # TODO use a release instead of the master branch!
        bots_file, headers = urllib.request.urlretrieve(weburl, "{}.zip".format(name))
    except Exception as e:
        print("Error downloading botshot: {}".format(e), file=sys.stderr)
        exit(1)

    try:
        print("Unpacking {} ...".format(name))
        zip = zipfile.ZipFile(bots_file, 'r')
        dirname = zip.namelist()[0]  # botshot-master
        for file in zip.infolist():
            if file.filename == dirname:
                continue
            file.filename = file.filename.split(dirname, 1)[1]
            zip.extract(file, '.')
        zip.close()
    except Exception as e:
        print("Error unpacking: {}".format(e), file=sys.stderr)
        exit(1)
    finally:
        os.remove(bots_file)


def install_skeleton(to):
    import botshot.bootstrap
    botshot.bootstrap.install_skeleton(to)


def bots_init(bot_name=None, do_clone=False):
    if not hasattr(sys, 'real_prefix'):
        print("Warning: We recommend using a virtual environment, do you want to continue? [y/n]")
        yesno()

    if not bot_name:
        bot_name = input("How do you want to call your chatbot?\n")

    if ('/' in bot_name) or ('\0' in bot_name) or ('\\' in bot_name):
        print("Error: Directory name contains invalid characters", file=sys.stderr)
        exit(1)
    elif not bot_name:
        print("Error: Directory name is empty", file=sys.stderr)
        exit(1)

    if os.path.exists(bot_name):
        if os.path.isdir(bot_name):
            print("Warning: Directory {} exists, do you want to continue? [y/n]".format(bot_name))
            yesno()
        else:
            print("Error: File {} already exists".format(bot_name), file=sys.stderr)
            exit(1)

    print("Creating a botshot project in {} ...".format(bot_name))

    if do_clone:
        # ensure django is installed
        retval = subprocess.call(['pip3', 'install', 'django'])
        if retval != 0:
            print("Error in pip install", file=sys.stderr)
            exit(1)

    retval = subprocess.call(['django-admin', 'startproject', bot_name])
    if retval != 0:
        print("Error: Can't create a django project!")
        exit(1)

    os.chdir(bot_name)

    if do_clone:

        download_and_unzip('botshot', "https://github.com/prihoda/botshot/archive/master.zip")

        print("Installing requirements ...")
        # unfortunately, pip > 10 doesn't support main() anymore
        retval = subprocess.call(['pip3', 'install', '-r', 'requirements.txt'])
        if retval != 0:
            print("Error in pip install", file=sys.stderr)
            exit(1)

    print("Creating skeleton project ...")
    # download_and_unzip('skeleton project', "https://github.com/mzilinec/golem-example-chatbot/archive/master.zip")
    # install skeleton to django project module
    install_skeleton(os.path.abspath(os.path.join(os.getcwd(), bot_name)))

    print("Running django migrate ...")
    retval = subprocess.call(['python3', './manage.py', 'migrate'])
    if retval != 0:
        print("Error in manage.py migrate", file=sys.stderr)
        exit(1)

    print("Everything looks OK!")
    print("You can start the server inside the directory with: bots start [django-app]")


def bots_start(djangoapp):
    # TODO handle errors

    print("Starting Redis database ...")
    redis = subprocess.Popen(["redis-server"])

    print("Starting Celery ...")
    django = subprocess.Popen(["celery", "-A", djangoapp, "worker"])

    print("Starting Django ...")
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


def main():
    argp = argparse.ArgumentParser(description="botshot framework configuration utility")
    argp.add_argument('command', nargs=1, type=str, help="One of : init, start, help")
    argp.add_argument('djangoapp', nargs='?', help="Name of your django app.")
    argp.add_argument("--clone", action="store_true",
                      help="Downloads botshot from master instead of using PyPI. Only for development, don't use!")

    args = argp.parse_args()
    command = args.command[0]

    if command == 'init':
        do_clone = args.clone
        bots_init(args.djangoapp, do_clone)
    elif command == 'start':
        if args.djangoapp is None:
            argp.error("Django app name must be specified.")
        djangoapp = args.djangoapp
        bots_start(djangoapp)
    elif command == 'help':
        argp.print_help()
        exit(0)
    else:
        print("Unknown command {}".format(command))
        argp.print_usage()
        exit(1)


if __name__ == "__main__":
    main()
