---
title: "Converts GPT-4-style prompts to Claude3 prompts"
category: prompt-engineering
tags:
  - prompt-conversion
  - gpt4
  - template
source: "https://twitter.com/mattshumer_/status/1765441669820780582"
author: null
model: null
has_image: false
added: "2026-03-05"
---

# Converts GPT-4-style prompts to Claude3 prompts

from:

```
To prompt Claude 3 well, use XML tags in your prompts. They help the model better understand what you're asking it to do.

Here's an example, from Anthropic's docs:
<example_prompt>
Your task is to analyze the following report:
<report>
[Full text of Matterport SEC filing 10-K 2023, not pasted here for brevity]
</report>

Summarize this annual report in a concise and clear manner, and identify key market trends and takeaways. Output your findings as a short memo I can send to my team. The goal of the memo is to ensure my team stays up to date on how financial institutions are faring and qualitatively forecast and identify whether there are any operating and revenue risks to be expected in the coming quarter. Make sure to include all relevant details in your summary and analysis.
</example_prompt>

Note that they include <report> and </report> tags. It's a small adjustment, but it makes a big difference.

Now, I'm going to give you a <prompt_to_convert>. Take this <prompt_to_convert> and adjust it to be ideal for Claude.

Here's the prompt:

<prompt_to_convert>
{PLACE_YOUR_PROMPT_HERE}
</prompt_to_convert>

Increase clarity, and use XML tags wherever possible.
```
