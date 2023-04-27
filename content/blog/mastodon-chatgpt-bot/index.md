---
title: Automating Mastodon Posts with OpenAI's ChatGPT
description: Building Mastofact, a silly ChatGPT-powered Mastodon bot that toots a random fact every hour, using Python and the Mastodon.py library.
date: 2023-03-05T05:24:54.000Z
slug: mastodon-chatgpt-bot
tags: [mastodon, chatgpt, bot]
toc: true
math: false
comments: true
---

{{< note variant="info" >}}
In this post we're going to build a silly ChatGPT-powered Mastodon bot that toots a random fact every hour, using Python and the [Mastodon.py library](https://mastodonpy.readthedocs.io/en/stable/). You can find the full source code on [GitHub](https://github.com/n3d1117/mastofact). It's currently running at [@mastofact](https://mastodon.social/@mastofact)!
{{< /note >}}

## Introduction
[Mastodon](https://joinmastodon.org) is a decentralized social media platform that allows users to communicate and share content with others in a community-based manner. OpenAI's GPT-3 is a powerful language model that can generate human-like responses to prompts. In this blog post, we'll explore how to combine the two to automatically post interesting facts on Mastodon.

{{< img src="mastofact.png" caption="Mastofact icon (courtesy of DALL·E)" w="150" >}}

## Prerequisites
- Python 3.10+ and [Pipenv](https://pipenv.readthedocs.io/en/latest/) installed
- A Mastodon access token (create one under `Development` > `Your applications` > `New application` > `Your access token`)
- An [OpenAI](https://openai.com) API token

## Dependencies

We start by creating a new Python project with the following Pipfile:

```toml
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
"Mastodon.py" = "1.8.0"
openai = "==0.27.0"
python-dotenv = "*"

[dev-packages]

[requires]
python_version = "3.10"
```

We install the dependencies with `pipenv install`. We'll use the [Mastodon.py](https://mastodonpy.readthedocs.io/en/stable/) library to interact with the Mastodon API, and the [OpenAI](https://github.com/openai/openai-python) library to interact with the OpenAI API.

We'll also use [python-dotenv](https://pypi.org/project/python-dotenv/) to load environment variables from a `.env` file. We create the file and add the following variables:

```bash
MASTODON_INSTANCE="YOUR_MASTODON_INSTANCE" # e.g. https://mastodon.social/
MASTODON_BOT_TOKEN="YOUR_MASTODON_BOT_TOKEN"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
POST_INTERVAL_SECONDS=3600 # 1h
```

## Code
We start by reading the environment variables from the `.env` file created before, using the `load_dotenv()` function from the `python-dotenv` library. This makes it easy to set configuration values in a separate file without hardcoding them in the script.

```python
from dotenv import load_dotenv

load_dotenv()# [tl! focus]
```

First, we import the Mastodon library, and setup the Mastodon instance with the access token:

```python
import os
from mastodon import Mastodon

# Setup Mastodon
mastodon = Mastodon(# [tl! focus:start] 
    access_token=os.environ['MASTODON_BOT_TOKEN'],
    api_base_url=os.environ['MASTODON_INSTANCE']
)# [tl! focus:end] 
```

Then we import the OpenAI library, and setup the OpenAI instance with the API key. We provide an initial prompt for our ChatGPT model and instruct it to reply with a random interesting fact:

```python
import openai

# Setup OpenAI [tl! focus:start] 
openai.api_key = os.environ['OPENAI_API_KEY']
prompt = "Tell me a random fact, be it fun, lesser-known or just interesting. Before answering, always " \
            "check your previous answers to make sure you haven't answered with the same fact before, " \
            "even in different form."
history = [{
    "role": "system",
    "content": "You are a helpful assistant. When asked about a random fun, lesser-known or interesting fact, "
                "you only reply with the fact and nothing else."
}]# [tl! focus:end] 
```

Finally, we create a loop that will run forever, and post a new fact every hour:

```python
import time

while True:# [tl! focus:start] 
    try:
        history.append({"role": "user", "content": prompt})

        # Only keep the last 10 messages to avoid excessive token usage
        if len(history) > 10:
            history = history[-10:]

        # Generate a random fact
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=history,
            temperature=1.3,
        )

        # Post the fact on Mastodon
        mastodon.status_post(status=response.choices[0]['message']['content'])

    except Exception as e:
        logging.error(e)

    # Wait for the specified interval before posting again
    time.sleep(float(os.environ.get('POST_INTERVAL_SECONDS', 3600)))# [tl! focus:end] 
```

The while loop runs indefinitely, posting a new status to Mastodon every `POST_INTERVAL_SECONDS` seconds. This value defaults to 3600 seconds (1 hour) if it is not set.

The loop appends the current prompt to the history list and removes any elements that are more than 10 items back in the list, to limit the token usage for the OpenAI API. It then calls the `openai.ChatCompletion.create()` method to generate a random fact. 

The `temperature` argument is a number between 0 and 2, which defaults to 1. Higher values will make the output more random, while lower values will make it more focused and deterministic. Here we set it to 1.3 to get more interesting facts.

## Conclusion
In this blog post, we explored how to combine Mastodon and OpenAI's ChatGPT to automatically post interesting facts on Mastodon.

{{< img src="demo.png" caption="Output demo (source: [@mastofact](https://mastodon.social/@mastofact))" w="500" >}}

I hope you enjoyed it! You can find the full source code on [GitHub](https://github.com/n3d1117/mastofact). It's currently running at [@mastofact](https://mastodon.social/@mastofact)!