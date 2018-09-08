#######################
Conversation testing
#######################

.. note:: TODO

.. code-block:: python

    BOTS_CONFIG['TEST_MODULE'] = 'my.tests'

my_tests/foo.py:

.. code-block:: python

    from botshot.core.responses import *
    from botshot.core.tests import *

    actions = []

    actions.append(UserTextMessage("Hello").produces_entity("intent","greeting"))

    actions.append(StateChange("greeting.root"))
    actions.append(BotMessage(TextMessage).with_text("Hey there! ;)"))
    actions.append(StateChange("greeting.intro"))

    actions.append(UserTextMessage ...
