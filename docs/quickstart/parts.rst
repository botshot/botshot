###################
Parts of a chatbot
###################

| Anyway, what does a good chatbot consist of?

| Well, for one, it needs to be able to **send and receive messages**, or it wouldn't be a chatbot, right?
| Then it needs to **understand messages** and their meaning (partially at least).
| It should also **keep track of conversation** and remember the **conversation history**. In other words, it shouldn't lose the thread in the middle of a conversation.
| Finally, it should be able to **generate messages** that answer the users' input.
|
| Let's now go over the main components that Botshot provides.

---------------------
Messaging endpoints
---------------------

Botshot supports popular messaging platforms such as *Facebook*, *Telegram* or *Alexa*.
The messages are converted to a universal format, so you don't need to worry about compatibility.

For each of these platforms, there is a corresponding chat interface.
To enable support for a messaging platform, just enable the associated interface in the config.
Read more at `Messaging endpoints`_.

.. note:: Botshot is fully extensible. If you need to support another messaging API, just implement your own chat interface.

-------------------------------------
Natural language understanding (NLU)
-------------------------------------

| Natural language understanding is the process of analyzing text and extracting machine-interpretable information.
| You don't have to be an expert to make a chatbot. Today, there are many available services that do the job for you.
| Botshot provides easy integration with the most popular tools, such as Facebook's `Wit.ai`_, Microsoft's `Luis.AI`_, or the offline `Rasa NLU`_.
| Or you can use our own Botshot NLU module.

| When a message is received, the chatbot should:

1. Analyze what the user wants, aka **Intent detection**
    | Classify the message into a *category*.
    | Input:  ``{"text": "Hi there!"}``
    | Output: ``{"intent": "greeting", "confidence": 0.9854, "source": "botshot_nlu"}``
2. Find out details about the query, aka **Entity extraction**
    | Extract *entities* such as *dates*, *places* and *names* from text.
    | Input:  ``{"text": "Are there any interesting events today?"}``
    | Output: ``{"query": "events", "date": "2018-01-01"}``

| You won't need to use a NLU service to get started, but you should really use one to keep your future users happy.
| Read more at `Natural language understanding`_.

.. note:: You can also use your own machine learning models. See `Entity extractors`_ for more details.

.. _Wit.ai: https://wit.ai
.. _Luis.AI: https://luis.ai
.. _Rasa NLU: https://github.com/RasaHQ/rasa_nlu


------------------------------------------
Dialog Management & Context
------------------------------------------

| The Dialog manager is a system responsible for tracking the user's progress in conversation.
| You can picture the conversation as a state machine, with each state representing a specific point in the conversation (like *greeting*).
| The user can move between these states by sending messages, tapping buttons and so on.
| Dialog manager also stores conversation context. That is, if you're building a chatbot that does more than say "hello", you will probably also want to remember what the user has said before.


------------------------------------------
Actions
------------------------------------------

Each state of the conversation has an attached action that returns a response.
The most common way of generating responses is using Python code.
You can define a function that Botshot will call when a message is received.
In this function, you can call your business logic, call any required APIs and generate a response.

**Alright, enough chit chat. Let's get coding!**
