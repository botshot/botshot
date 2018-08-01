###################
Parts of a chatbot
###################

| So anyway, what does a good chatbot consist of?

| Well, multiple things. For one, it needs to be able to **send and receive messages**, or it wouldn't be a chatbot, right?
| It also needs to **understand messages** and know their meaning (partially at least).
| It should also **keep track of conversation** and remember the **conversation history**. In other words, it shouldn't lose the thread in the middle of a conversation.
| Finally, it should be able to **generate messages** that answer the users' input.
|
| Let's go over these things, really quickly.

---------------------
Messaging endpoints
---------------------

Botshot supports popular messaging platforms such as *Facebook messenger* and *Telegram*.
For each of these platforms, there is an endpoint that converts the messages to a universal format,
so you don't need to worry about compatibility.

To enable support for messaging platforms, just add the associated API token to ``BOT_CONFIG``.
Read more at `Messaging endpoints`_.

.. note:: Botshot is fully extensible. If you need to support your private messaging API, just implement the endpoint and it will work.

-------------------------------------
Natural language understanding (NLU)
-------------------------------------

| Natural language understanding is the process of analyzing text and extracting machine-interpretable information.
| NLU is actually a topic in AI, but you don't have to be an expert to make a chatbot. Today, there are many available services that do the job for you.
| Botshot provides easy integration with the most popular tools, such as Facebook's `Wit.ai`_, Microsoft's `Luis.AI`_, or the offline `Rasa NLU`_.
| We also have our own NLU module, designed specifically for use with Botshot. Contact us if you're interested.
| Although you don't have to, you should really use NLU. The above tools are very easy to use.

NLU tools are useful for these purposes:

1. **Intent detection** aka "What does the user want?"
    | Classify the message into a *category*.
    | Input:  ``{"text": "Hi there!"}``
    | Output: ``{"intent": "greeting", "confidence": 0.9854, "source": "botshot_nlu"}``
2. **Entity extraction** aka "How does the user want it?"
    | Extract *entities* such as *dates*, *places* and *names* from text.
    | Input:  ``{"text": "Are there any interesting events today?"}``
    | Output: ``{"query": "events", "date": "2018-01-01"}``

To enable support for NLU platforms, just add the associated API token to ``BOT_CONFIG``.
Read more at `Natural language understanding`_.

.. note:: You can use your own machine learning models for NLU if you wish. See `Entity extractors`_ for more details.

.. _Wit.ai: https://wit.ai
.. _Luis.AI: https://luis.ai
.. _Rasa NLU: https://github.com/RasaHQ/rasa_nlu


------------------------------------------
Dialogue Management & Conversation Context
------------------------------------------

| If you're building a chatbot that does more than say "hello", you will need a way to keep track of the conversation
and remember what the user has said before.
| Botshot has a Dialogue Manager that does exactly this. You can picture the conversation as a state machine
with states like *greeting* and transitions that fire when a message is received.
| There is also a Context Manager that you can query about past conversations and NLU entities.

.. note:: We would be really happy if we could just train a neural network instead.
           However, there are still many problems that need to be solved before production use.


**Alright, enough chit chat. Let's get coding!**
