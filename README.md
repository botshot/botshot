
# Botshot chatbot framework

![PyPI](https://img.shields.io/pypi/v/botshot.svg)
![PyPI - Status](https://img.shields.io/pypi/status/botshot.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/botshot.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/botshot/botshot.svg)
![Read the Docs](https://img.shields.io/readthedocs/botshot.svg)
![GitHub](https://img.shields.io/github/license/botshot/botshot.svg)

<!-- ![PyPI - Django Version](https://img.shields.io/pypi/djversions/botshot.svg) -->
<p>
<img src="https://raw.githubusercontent.com/botshot/botshot/devel/docs/images/botshot.png" height="100"/>
</p>


#### Botshot is a Python/Django framework for building stateful chatbots and conversational interfaces.

With Botshot, you can build complex chatbots that remember past conversations.

Botshot can:
- __Receive messages__ from __Messenger__, __Telegram__ or __Amazon Alexa__ (more platforms coming soon)
- __Understand__ these messages using your favorite **NLU** service
  - e.g. "Show me the best concert" -> *intent:* recommend, *query:* concert
- __Keep track of the history__ of the conversation *(context)*
- __Move between different states__ of the conversation based on the context
- __Send messages__ and media back to the user
<!-- - It's __language independent__ -->
<!-- - It has a __web chat GUI__ for easy testing -->

## Getting started

Just install the package and run our `bots` init script.
```bash
pip3 install botshot
bots init my_bot && cd my_bot
bots start
```

That's it! Now open http://localhost:8000/chat and chat with your bot.

You may also want to add some actual content, so check the docs ;-)

## Docs

It's quite easy to get started!

Find out how to make your own bot in the **[Docs](https://botshot.readthedocs.io)**.

Questions? [Join us on Slack!](https://botshot-slackin.herokuapp.com/)

## Authors
- David Příhoda - [prihoda](https://github.com/prihoda)
- Matúš Žilinec - [mzilinec](https://github.com/mzilinec)
- Jakub Drdák   - [drdakjak](https://github.com/drdakjak)


## License
This project is dual licensed. You may only use Botshot for open-source projects under the AGPL license.  If you'd like to use Botshot for commercial projects, please contact us for a commercial license.
