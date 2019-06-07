############
Actions
############

| If you read the previous page, you should already suspect what actions are.
| To recap, each state has an action that triggers under some conditions. This action can be a hardcoded message or a python function returning some text.

========================
Hardcoded actions
========================

| You can simply define a message to be sent directly from the YAML flow.
| In the example below, each time the user visits the "root" state, the bot sends the message "How are you?" and moves to the state "root" of the flow "next".

.. code-block:: yaml

    greeting:
        states:
        - name: "root"
          action:
            text: "How are you?"        # sends a text message
            replies:                    # sends quick replies below the message
            - "I'm fine!"
            - "Don't even ask"
          next: "next.root:"          # moves to a different state


========================
Coding actions in Python
========================

You can also define the action as a regular Python function.
In this function, you can implement business logic and send messages from the bot.

.. code-block:: yaml

    greeting:
        states:
        - name: "root"
        # relative import ...
          action: actions.foo
        # ... or absolute import
          action: chatbot.bots.default.conditions.bar

| The function should take one parameter - ``dialog``. This object can be used to send messages and query conversation context and user profile.
| To move to another state, the function can optionally return the new state's name (equivalent to ``next`` in YAML).

.. code-block:: python

    import random
    from custom.logic import get_all_jokes

    from botshot.core.dialog import Dialog
    from botshot.core.responses import *

    def show_joke(dialog: Dialog):
        jokes = get_all_jokes()
        joke = random.choice(jokes)
        dialog.send(joke)  # sends a string message
        return "next.root:"

| You can send messages by calling ``dialog.send()``. This method takes one argument - the message!
| The argument can be a string, a standard template from ``botshot.core.responses``, or a list of messages.
| See `Message Templates`_.
|
| The context of the conversation is stored in ``dialog.context``. See `Context`_ for more information.

.. note:: The function will be run asynchronously. While waiting for the function to return, a typing indicator will be displayed. (three dots in messenger)


--------------------------------------
Sending more messages at once
--------------------------------------

.. code-block:: python

    messages = []
    for i in range(3):
        messages.append("Message #{}".format(i))
    dialog.send(messages)

.. TODO picture

.. warning:: Avoid calling dialog.send() in a loop. In bad network conditions, the messages might be sent in wrong order.

--------------------------------------
Sending delayed messages
--------------------------------------

You can schedule messages to be sent at a time in the future, or when the user is inactive for a period of time.
Read more in `Scheduling messages`_.

.. code-block:: python

    payload = {"_state": "default.schedule", "schedule_id": "123"}

    # Regular scheduled message - use a datetime or number of seconds
    dialog.schedule(payload, at=None, seconds=None)

    # Executed only if the user remains inactive
    dialog.inactive(payload, seconds=None)

.. TODO explain payloads

-------------------
Message templates
-------------------

This section contains a list of all message templates that can be sent using ``dialog.send()``.
The templates are universal, but they will render slightly different on each messaging service.

+++++++++++++++++
Text message
+++++++++++++++++

| A basic message with text. Can contain buttons or quick replies.

``TextMessage(text, buttons=[], replies=[])``

Buttons are shown below the message. They can be used to provide additional related actions.

- ``LinkButton(title, url)`` - Opens a web page upon being clicked.
- ``PayloadButton(title, payload)`` - Sends a special `postback message`_ with programmer-defined payload on click.
- ``PhoneButton(title, phone_number)`` - Facebook only. Calls a number when clicked.
- ``ShareButton()`` - Facebook only. Opens the "Share" window.

Quick replies are used to suggest a user's response. They contain text that is sent back to the chatbot when clicked. They can also contain payload.

- ``QuickReply(title)`` - Used to suggest what the user can say. Sends "title" as a message.
- ``LocationQuickReply()`` - Facebook only. Opens the "Send location" window.

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


.. TODO show result on all platforms

.. note:: Different platforms have different message limitations. For example, quick replies in Facebook Messenger can have a maximum of 20 characters.

+++++++++++++++++++++
Media message
+++++++++++++++++++++

MediaMessage can be used to send an image with optional buttons. The image should be located on a publicly available URL.

Example:

.. code-block:: python

    from botshot.core.responses import MediaMessage

    message = MediaMessage(url="http://placehold.it/300x300", buttons=[LinkButton("Open", "http://example.com"))

renders as:

.. TODO show result on all platforms

.. +++++++++++++++++++++
.. Image message
.. +++++++++++++++++++++

.. TODO

.. +++++++++++++++++++++
.. Audio message
.. +++++++++++++++++++++

.. TODO

.. +++++++++++++++++++++
.. Video message
.. +++++++++++++++++++++

.. TODO

+++++++++++++++++++++
Card template
+++++++++++++++++++++

The card template displays a card with a title, subtitle, an image and buttons.
It can be used to present structured information about an item or product.

.. code-block:: python

    msg = CardTemplate(
        title="A card",
        subtitle="Hello world!",
        image_url="http://placehold.it/300x300",
        item_url="http://example.com"
    )
    msg.add_button(button)

.. TODO show result on all platforms

+++++++++++++++++++++
Carousel template
+++++++++++++++++++++

The carousel template is a horizontal list of cards.

.. code-block:: python

    msg = CarouselTemplate()
    msg.add_element(
        CardTemplate(
            title="Card 1",
            subtitle="Hello world!",
            image_url="http://placehold.it/300x300"
        )
    )

+++++++++++++++++++++
List template
+++++++++++++++++++++

The list template is a vertical list of cards.
