###################
Quick Start
###################

Botshot is a framework for building chatbots in Python. It enables developers to build reliable and smart bots.
Botshot defines a concrete structure of the conversation and keeps track of the conversation history.


---------------------------
Dependencies
---------------------------

Botshot runs on top of the Django_ web framework. It is built with scalability in mind, and Celery_ is used for message processing.
For persistence of conversation context, we use Redis_. You don't need to understand the internal workings of these components.


.. seealso::
    Python is a very intuitive programming language.
    If you have never worked in Python, check out the official `beginners guide`_.
.. _beginners guide: https://wiki.python.org/moin/BeginnersGuide

.. _Django: https://djangoproject.com/
.. _Celery: https://celeryproject.org/
.. _Redis:  https://redis.io/
