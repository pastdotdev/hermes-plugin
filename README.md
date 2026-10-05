# past.dev memory for Hermes Agent

Gives your [Hermes](https://github.com/NousResearch/hermes-agent) agent a long-term memory in
[past.dev](https://past.dev): before each message, what past remembers about it is added as
background, and your conversations are kept in past, cut into sittings where they went quiet.
The agent can also search its memory with the `past_recall` tool.

## Install

```bash
pip install "git+https://github.com/pastdotdev/hermes-plugin"   # in the same environment as Hermes
hermes config set memory.provider past
hermes past setup                  # your project key from the past.dev console, and who you are
```

`hermes memory setup` offers past too and runs the same steps. `hermes past status` shows the
connection and the last sessions sent. The environment works as well: `PAST_API_KEY`,
`PAST_IDENTITY`.

If you already use past's Claude Code or Codex plugin, there is nothing to set: this plugin reads
the same `~/.past/config.json`. `PAST_API_URL` points it at a self-hosted past.

## What it sends

- **Recall:** the message you send, with obvious secrets (keys, tokens, `PASSWORD=...`) removed,
  as the query. Nothing is recalled until an identity is set.
- **Memory:** what you and Hermes said in each session, without tool calls or their results, with
  the same redaction. A session is kept on this machine (`~/.past/hermes/`) while it runs and sent
  when it ends, is compacted or switched; one that a crash left behind is sent at the next start.
- Cron runs, subagents and memory flushes are never sent.
- **Messaging gateway (Telegram, Slack, Discord...):** off by default. past recalls as one
  identity, so on a gateway that several people use, one person's memories would reach another.
  If the gateway serves only you, set `"gateway": true` in `~/.past/config.json`.

`"recall": false` or `"ingest": false` in `~/.past/config.json` turns either off.

MIT licensed.
