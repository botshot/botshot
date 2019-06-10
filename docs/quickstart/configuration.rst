###################
Configuration
###################

If you used the ``bots`` init tool, you don't need to configure anything at the moment.

----------------------
Project structure
----------------------
As Botshot runs on top of Django, its projects use the familiar Django structure.

It might look similar to this:

::

    my_bot/  # the root directory
        bot/  # your chatbot (django) app
            chatbots/            # actual chatbot logic (read on)
            botshot_settings.py  # chatbot-specific settings
            settings.py          # web server settings
        manage.py  # script that starts web server

----------------------
Settings
----------------------

| In ``botshot_settings.py``, you will find a python dict ``BOT_CONFIG``.
| Most configuration values, such as for NLU and messaging endpoints, belong here.
|
| ``settings.py`` contains configuration of the web server.
| Notably, you can:
|
| - link SQL databases under ``DATABASES``,
| - permit listening on URLs under ``ALLOWED_URLS``.
| For more information, see `django settings`_.

.. _django settings: https://docs.djangoproject.com/en/2.0/topics/settings/

----------------------
Environment variables
----------------------
If you plan to develop a larger chatbot, you shouldn't hardcode configuration values. You can provide them
as environment variables instead. This can be done with a so-called env file.

You can create a file, for example ``.env``, and put your config values in it like in a shell script:

.. code-block:: bash

    DEBUG=false
    FB_PAGE_TOKEN=foo
    NLU_TOKEN=bar
    ROOT_PASSWORD=12345

Then, to make it load automatically, you can for example:

- (virtualenv) add this line to `env/bin/activate`: ``export $(grep -v '^#' .env | xargs)``
- (PyCharm) use the EnvFile plugin, add the file in run configuration


+++++++++++++++++++++++++++++++++++++++++++++
BOT_CONFIG reference
+++++++++++++++++++++++++++++++++++++++++++++

- WEBCHAT_WELCOME_MESSAGE
