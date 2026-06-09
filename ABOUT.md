# ABOUT.md

## Why this role
I only want to work at a place that respects AI-native engineering. The AI model will ALWAYS have
more information than I will, and it (especially the new models of today) will code better than me.
It however always has the problem of being a lazy blind genius, and I've spent thousands of hours
coding with agents, I know how to make them sing, it's extremely fun for me to work with them.

## How you work with AI tools
Claude Opus 4.8, Claude Code, GPT 5.5, Codex.

My AI workflow involves giving the agent as much context as possible and then asking it to ground
me in truths. I ask the agent, "what do you see?", "what is the purpose of this repository?",
"what do you see between the lines and files that I do not see?", "perform a critical review
of the codebase and return to me with your findings."

I use Max thinking mode 99%+ of the time. I'm asked about cost and usage limits, and I respond with
my own opinion that anything below Max for really any level of work will yield you a less thorough
result that leaves other more novel solutions that may have been uncovered with a higher level of
thinking on the table. For example, on High mode, the agent will implement a well-done solution. On
Max mode, the agent may determine that the entire approach is wrong, and a refactor to this cleaner
architecture or data model will require less code and be more reusable.

TLDR: I ask a lot of questions, keep the prompts as focused and minimally polluted as possible, and
always challenge the agent to find a higher level than where we stand. I use these tools to make me
smarter, not just complete tasks for me.

## Your last project (mermaid-cli)
- **One ambiguity** you faced and how you resolved it:
When I made mermaid, I had a very limited understanding of LLMs and agentic systems. I wanted to
make an open source version of Claude Code, but I didn't understand backends for LLMs at all. Claude
basically gave me an entire course on Ollama and Groq and other LLM API providers. I used Claude as
a tutor so that I can better steer Claude. Claude and I live in this self-reinforcing loop, we make
each other smarter.
- **One tradeoff** you made and why:
I really wanted to introduce a plan mode during development but the scope creep at that point was
getting too high, so I completely scrapped it and decided to laser focus on just getting the core
loop working with Claude.
- **One mistake** you made and what you changed:
Huge one. I got cocky when they released GPT-5.5 and decided that I want to make a frontend native
web app for mermaid. I then confused the agent by saying I want both the CLI and the frontend to
exist, and the frontend will simply be a CLI manager window where you can observe work at a higher
level. It was such a terrible idea on my part. Implementation was a nightmare and I was never
consistent with what I wanted. It became more and more of a headache to try to keep working through it so I totally scrapped that idea and went back to just focusing on the CLI, in a position where
I wasn't sure what to do with it next.
- **One review comment** that made you change your mind:
I wanted to have every single API provider supported from every major LLM server. Anthropic, OpenAI,
Ollama, vLLM, Groq, Cerebras, etc., but that was such a nightmare to orchestrate at that time that
Claude recommended we first just stick with Ollama and build the infrastructure around that first.
We only expand once we prove that Mermaid can work with Ollama as our deep backend.

## Anything you'd improve about THIS challenge or our CLAUDE.md
CLAUDE.md is really well written. Nothing to say about it. It's short and focused and has the
least amount of implementation details in it as possible. This allows the agent to find novel
solutions without being constrained to whatever the prompt declares is the standard. It also
saves precious time from the agent having to search for files and makes the standard pattern clear
for new sessions.

The challenge is well written. I would be really interested in an expanded part of the challenge
where we attempt to construct a machine learning model that can find edges better than any human 
written algorithm can.