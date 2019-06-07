
# Botshot Chatbot Framework

![CodeFactor](https://www.codefactor.io/repository/github/botshot/botshot/badge?style=flat-square)
![PyPI](https://img.shields.io/pypi/v/botshot.svg)
![PyPI - Status](https://img.shields.io/pypi/status/botshot.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/botshot.svg)
![Read the Docs](https://img.shields.io/readthedocs/botshot.svg)
![GitHub](https://img.shields.io/github/license/botshot/botshot.svg)


<!--![GitHub last commit](https://img.shields.io/github/last-commit/botshot/botshot.svg)-->
<!-- ![PyPI - Django Version](https://img.shields.io/pypi/djversions/botshot.svg) -->
<p>
<img src="https://raw.githubusercontent.com/botshot/botshot/devel/docs/images/botshot.png" height="100"/>
</p>


#### Botshot is a Python/Django framework for building stateful chatbots and conversational interfaces.

With Botshot, you can build complex chatbots that remember past conversations.

Botshot can:
- __Receive messages__ from __Messenger__, __Telegram__ or __Amazon Alexa__ (more platforms coming soon)
- __Understand__ and parse messages using a **NLU** service
  - e.g. "Show me the best concert" -> *intent:* recommend, *query:* concert
- __Manage the dialogue__ and move between the conversation's states
- __Keep track of the context__ and history of the conversation
- __Send messages__ and media back to the user
- __Connect__ to 3rd party APIs and analytics
<!-- - It's __language independent__ -->
<!-- - It has a __web chat GUI__ for easy testing -->

## Getting started

Just install the package and run the `bots` script. You will also need the Redis database.
```bash
sudo apt install redis-server
pip3 install botshot
bots init my_bot && cd my_bot
bots start
```

That's it! Now open http://127.0.0.1:8000/chat and chat with your bot.

You may also want to add some actual content, so check the docs ;-)

## Docs

Find out how to make your own chatbot in the **[Docs](https://botshot.readthedocs.io)**.

Questions? [Join us on Slack!](https://botshot-slackin.herokuapp.com/)

## Authors
- Matúš Žilinec - [mzilinec](https://github.com/mzilinec)
- David Příhoda - [prihoda](https://github.com/prihoda)
- Jakub Drdák   - [drdakjak](https://github.com/drdakjak)


## License
This project is dual licensed. You may only use Botshot for open-source projects under the AGPL license.  If you'd like to use Botshot for commercial projects, please contact us for a commercial license.
