###################
Quick Start
###################

Botshot is a framework for building chatbots in Python. It enables developers to build reliable and smart bots.
Its main advantages are that it defines a concrete structure of the conversation and keeps track of the conversation history.


---------------------------
Dependencies
---------------------------

Botshot runs on top of the Django_ web framework. It is built with scalability in mind, and Celery_ is used for message processing.
For persistence of conversation context, we use Redis_. You don't need to know any of these tools, but it's a plus.


.. seealso::
    If you have never worked in Python, don't worry. It is a very intuitive and easy to learn language.
    Check out the official `beginners guide`_.
.. _beginners guide: https://wiki.python.org/moin/BeginnersGuide

.. _Django: https://djangoproject.com/
.. _Celery: https://celeryproject.org/
.. _Redis:  https://redis.io/
