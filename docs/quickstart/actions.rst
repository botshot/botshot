############
Actions
############

| If you read the previous page, you should already suspect what actions are.
| To recap, each state has an action that triggers under some conditions. This action can be a hardcoded message or a python function returning some text.

-----------------
Hardcoded actions
-----------------

| You can simply define a message to be sent directly from the YAML flow.
| We encourage you to try making a flow just with these and testing it in the web chat interface before moving on to Python code.

.. code-block:: yaml

    action:
      text: "How are you?"        # sends a text message
      replies:                    # sends quick replies below the message
      - "I'm fine!"
      - "Don't even ask"
      next: "next.root:"          # moves to a different state


-------------------------
Coding actions in Python
-------------------------

You can call a custom function anywhere where you would use a hardcoded action. This function can be imported relatively or absolutely.

.. code-block:: yaml

    # absolute import
    action: chatbot.bots.default.conditions.bar
    action: actions.foo  # relative import

The function takes one parameter - an instance of ``DialogManager`` and optionally returns name of the next state (equivalent to ``next`` in YAML).
