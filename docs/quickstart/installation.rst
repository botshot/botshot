###################
Installation
###################

| The easiest way to get started is using our ``bots`` command line tool.

.. note::  We strongly recommend using a virtual environment to avoid package conflicts.
            ``virtualenv -p python3 bot_env/ && source bot_env/bin/activate``

| First, install Botshot and dependencies from PyPI.
| ``pip3 install botshot``
|
| Now go ahead and run:
| ``bots init my_bot``
| This will bootstrap a chatbot with default configuration under ``my_bot/``.

----------------------
Running the chatbot
----------------------

| First, cd to the chatbot directory you just created.
| ``cd my_bot``
| You can now run the chatbot with
| ``bots start my_bot``.
|
| The web chat interface should now be running at http://localhost:8000/ .
| Go ahead and say something to your chatbot!

+++++++++++++++++++++++++++
Running from IDE (optional)
+++++++++++++++++++++++++++
In case you're using an IDE such as PyCharm for development, it might be more convenient to run the chatbot
from within it, to make use of the debugger.

You will need to manually start these three components:

- Django server
                Under **Edit configurations > Add configuration > Django server**
- Celery tasks
                | Under **Edit configurations > Add configuration > Python**
                | **Script path:** path to celery - bot_env/bin/celery
                | **Working directory:** chatbot root
- Redis database
                | You can either run ``redis-server`` from the terminal or with an init script, as you would any other database.
                | If you're on Ubuntu and have installed redis with ``apt install redis``, it should already be running.
                | You can connect to your database using ``redis-cli``.