import os


def install_skeleton(dest_dir):
    if not os.path.isdir(dest_dir):
        raise ValueError("{} is not a directory".format(dest_dir))

    src_dir = os.path.dirname(__file__)
    app_name = os.path.basename(os.path.normpath(dest_dir))

    for root, dirs, files in os.walk(src_dir):

        rel_dir = os.path.relpath(root, src_dir)

        for name in dirs:
            dest = os.path.join(dest_dir, rel_dir, name)
            print("Create", dest)
            os.mkdir(dest, 0o755)

        for name in files:
            if not name.endswith('-tpl'):
                continue
            new_name = name.rsplit('-tpl', 1)[0]

            src = os.path.join(src_dir, rel_dir, name)
            dest = os.path.join(dest_dir, rel_dir, new_name)
            print("Copy", src, dest)

            with open(src, 'r') as f:
                file_content = f.read().replace("{APP_NAME}", app_name)
            with open(dest, 'w') as f:
                f.write(file_content)

    print("Adding settings.py imports ...")
    with open(os.path.join(dest_dir, "settings.py"), "r") as f:
        settings_content = f.read()
    # \n is converted by stdlib, keep calm
    settings_content = "from .bot_settings import *\n" + settings_content
    apps_str = "\n    'botshot.apps.BotshotConfig',"  # \n    'webgui',"  # FIXME botshot-webgui
    idx = settings_content.find("INSTALLED_APPS")
    idx = settings_content.find("\n", idx)
    settings_content = settings_content[:idx] + apps_str + settings_content[idx:]
    with open(os.path.join(dest_dir, "settings.py"), "w") as f:
        f.write(settings_content)
