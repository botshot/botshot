# Botshot chatbot framework

![PyPI](https://img.shields.io/pypi/v/botshot.svg)
![PyPI - Status](https://img.shields.io/pypi/status/botshot.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/botshot.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/the-bots/botshot.svg)
![Read the Docs](https://img.shields.io/readthedocs/botshot.svg)
![GitHub](https://img.shields.io/github/license/the-bots/botshot.svg)

<!-- ![PyPI - Django Version](https://img.shields.io/pypi/djversions/botshot.svg) -->

<p align="center">
<img src="https://raw.githubusercontent.com/botshot/botshot/devel/docs/images/botshot.png" height="200"/>
</p>

#### Botshot is a Python/Django framework for building stateful chatbots.

With Botshot, you can build complex chatbots that remember past conversations.

Botshot can:
- __Receive messages__ from __Messenger__ and __Telegram__ (Actions on Google coming soon)
- __Extract entities__ from these messages using your favorite **NLU** service
  - e.g. "Show me the best concert" -> *intent:* recommend, *query:* concert
- __Keep track of the history__ of all entities in the *context*
- __Move between different states__ of the conversation based on intent and other entities
- __Send messages__ and media back to the user
<!-- - It's __language independent__ -->
<!-- - It has a __web chat GUI__ for easy testing -->

## Getting started

Just install the package and run our `bots` init script.
```bash
pip3 install botshot
bots init my-bot
cd my-bot && bots start my-bot
```

That's all! A development chat server should now be running at http://localhost:8000.


You may also want to configure NLU, chat integrations and analytics, see the documentation for details.

## Docs

It's quite easy to get started!

Find out how to make your own bot in the **[Docs](https://botshot.readthedocs.io)**.


## Authors
- David Příhoda - [prihoda](https://github.com/prihoda)
- Matúš Žilinec - [mzilinec](https://github.com/mzilinec)
- Jakub Drdák   - [drdakjak](https://github.com/drdakjak)


Made @ [Datalab](https://datalab.fit.cvut.cz) [FIT CTU](https://fit.cvut.cz/en) in Prague.
