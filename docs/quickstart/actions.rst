############
Actions
############

| If you read the previous page, you should already suspect what actions are.
| To recap, each state has an action that triggers under some conditions. This action can be a hardcoded message or a python function returning some text.

========================
Hardcoded actions
========================

| You can simply define a message to be sent directly from the YAML flow.
| We encourage you to try making a flow just with these and testing it in the web chat interface before moving on to Python code.

.. code-block:: yaml

    action:
      text: "How are you?"        # sends a text message
      replies:                    # sends quick replies below the message
      - "I'm fine!"
      - "Don't even ask"
      next: "next.root:"          # moves to a different state


========================
Coding actions in Python
========================

You can call a custom function anywhere where you would use a hardcoded action. This function can be imported relatively or absolutely.

.. code-block:: yaml

    # absolute import
    action: chatbot.bots.default.conditions.bar
    action: actions.foo  # relative import

The function takes one parameter - an instance of ``DialogManager`` and optionally returns name of the next state (equivalent to ``next`` in YAML).
This function should look at the conversation context (NLU entities), fetch any data it needs from external APIs and send messages to the user.

.. code-block:: python

    import random
    from custom.logic import get_all_jokes

    from botshot.core.dialog_manager import DialogManager
    from botshot.core.responses import *

    def show_joke(dialog: DialogManager):
        jokes = get_all_jokes()
        joke = random.choice(jokes)
        dialog.send(joke)  # sends a string message
        return "next.root:"

.. note:: While waiting for the function to return, a typing indicator is displayed. (three dots in messenger)

-------------------
Message templates
-------------------

| You can send messages by calling ``dialog.send()``. This method requires one argument - the message!
|
|
| The message should either be a string, one of the templates from ``golem.core.responses``, or a list of these.
| Here is a list of all the templates you can use:

+++++++++++++++++
Text message
+++++++++++++++++

| A basic message with text. Can optionally have buttons or quick replies.

| The officially supported button types are:

- ``LinkButton(title, url)`` Redirects to a webpage upon being clicked.
- ``PayloadButton(title, payload)`` Sends a special `postback message`_ on click.
- ``PhoneButton(title, phone_number)`` Facebook only. Calls a number when clicked.
- ``ShareButton()`` Facebook only. Opens the "Share" window.

| The supported quick reply types are:

- ``QuickReply(title)`` Used to suggest what the user can say. Sends "title" as a message.
- ``LocationQuickReply()`` Facebook only. Opens the "Send location" window.

.. code-block:: python

    msg = "Botshot is the best!"
    dialog.send(msg)

    msg = TextMessage("I'm a message with buttons!")
    msg.add_button(LinkButton("I'm a button", "https://example.com"))
    msg.add_button(PayloadButton("Next page", payload={"_state": "next.root:"}))
    msg.add_button(ShareButton())
    # or ...
    msg.with_buttons(button_list)
    dialog.send(msg)

    msg = TextMessage("I'm a message with quick replies!")
    # or ...
    msg.add_reply(LocationQuickReply())
    msg.add_reply(QuickReply("Lorem ipsum ..."))
    msg.add_reply("dolor sit amet ...")
    # or ...
    msg.with_replies(reply_list)


TODO picture, result on more platforms?

.. note:: Different platforms have different message limitations. For example, quick replies in Facebook Messenger can have a maximum of 20 characters.

+++++++++++++++++++++
Image message
+++++++++++++++++++++

TODO

+++++++++++++++++++++
Audio message
+++++++++++++++++++++

TODO

+++++++++++++++++++++
Video message
+++++++++++++++++++++

TODO

+++++++++++++++++++++
Carousel template
+++++++++++++++++++++

TODO

+++++++++++++++++++++
List template
+++++++++++++++++++++

TODO

++++++++++++++++++++++++++++++
Sending more messages at once
++++++++++++++++++++++++++++++

.. code-block:: python

    messages = []
    for i in range(3):
        messages.append("Message #{}".format(i))
    dialog.send(messages)

TODO picture

.. warning:: Avoid calling dialog.send() in a loop. In bad network conditions, the messages might be sent in wrong order.

-------------------
Scheduling messages
-------------------

You can schedule a message to be sent in the future.
You can optionally send it only if the user doesn't say anything first.

.. code-block:: python

    payload = {"_state": "default.schedule", "schedule_id": "123"}

    # Regular scheduled message - use a datetime or number of seconds
    dialog.schedule(payload, at=None, seconds=None)

    # Runs only if the user remains inactive
    dialog.inactive(payload, seconds=None)
