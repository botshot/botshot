# Botshot chatbot framework

![PyPI](https://img.shields.io/pypi/v/botshot.svg)
![PyPI - Status](https://img.shields.io/pypi/status/botshot.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/botshot.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/the-bots/botshot.svg)
![Read the Docs](https://img.shields.io/readthedocs/botshot.svg)
![GitHub](https://img.shields.io/github/license/the-bots/botshot.svg)

<!-- ![PyPI - Django Version](https://img.shields.io/pypi/djversions/botshot.svg) -->

<p align="center">
<img src="https://www.praguevisitor.eu/wp-content/uploads/2018/03/Golem.jpg" width="300"/>
</p>

#### Botshot is a python framework for building chatbots for Messenger, Telegram and other platforms.

It differs from other bot frameworks by giving a concrete structure to the conversation.

What it can do:
- __Receive messages__ from __Messenger__ and __Telegram__ (Actions on Google coming soon)
- __Extract entities__ from these messages, for example using [Wit.ai](http://wit.ai)
  - e.g. "Show me the best concert" -> *intent:* recommend, *query:* concert
- __Keep track of the history__ of all entity values in the *context*
- __Move between different states__ of the conversation based on intent and other entities
- Call your functions for each state and __send messages__ and media back to the user
- It supports any language supported by Wit (English is recommended)
- It has a __web chat GUI__ for easy testing

## Getting started

Just install the package and run our `golm` init script that will take care of initial configuration.
```bash
pip3 install botshot
bots init my-bot
cd my-bot && bots start my-bot
```

That's all! A development chat server should now be running at http://localhost:8000.


You may also want to configure NLU, chat integrations and analytics, see the documentation for details.

## Docs

It's very easy to get started!

Find out how to make your own bot on the **[Wiki](https://github.com/the-bots/botshot/wiki)**.


## Authors
- David Příhoda - [prihoda](https://github.com/prihoda)
- Matúš Žilinec - [mzilinec](https://github.com/mzilinec)
- Jakub Drdák   - [drdakjak](https://github.com/drdakjak)


Made @ [Datalab](https://datalab.fit.cvut.cz) [FIT CTU](https://fit.cvut.cz/en) in Prague.
