# past for Hermes: contributor guide

A Hermes `MemoryProvider`, installed as a pip package through the `hermes_agent.memory_providers`
entry point. The provider is `past_hermes/__init__.py`; `past_hermes/cli.py` adds `hermes pastdotdev setup` and `hermes pastdotdev status` (Hermes lists them while `pastdotdev` is the active provider, and `hermes memory setup` runs the same setup). Standard library only. Setup writes the key to the shared `~/.past/config.json`, created `600`.

## How it fits together

```
Hermes turn
  prefetch(message)       POST /api/v1/recall, rendered as the "=== past · recalled from memory ===" block
  past_recall tool        POST /api/v1/recall, as JSON
  sync_turn(user, reply)  appended to ~/.past/hermes/sessions/<session>.json, nothing sent
  session end, compaction, switch, shutdown
                          POST /api/v1/ingest/batch: every sitting whose content changed
  initialize              sends sessions a crash left behind
```

## The rules this code keeps

They are the Claude Code connector's (`CLAUDE.md` in github.com/pastdotdev/claude-code-plugin), applied to Hermes:

1. **Never break the session.** Every hook catches its own failures; a failed send is kept in
   `~/.past/hermes/state.json` as `lastError`.
2. **Only prose travels.** `sync_turn` gives the person's message and Hermes' reply; tool calls,
   results and the recall block Hermes injected are not sent.
3. **Send at boundaries, never every turn.** A session that grew is a new revision, priced on its
   whole content, so turns are kept on disk and sent when the session ends, compacts or switches.
4. **The hash gates the send.** Each sitting's content hash is kept; an unchanged sitting is not sent.
5. **Sittings.** A session is cut where it was silent for `sittingMinutes` (30, at least 5), pinned
   per session at its first send. The first sitting's id is `hermes:<session>`, the next ones
   `hermes:<session>:<n>`; each is timed at its first turn.
6. **Redact the query and the content alike.** Same patterns as the other connectors.
7. **`~/.past` is private.** Files are created `600` in a `700` folder; the key is written only by
   `hermes pastdotdev setup`, into the shared config, and otherwise read from the environment.

## Contracts

`POST /api/v1/recall` (needs `identity`), `POST /api/v1/ingest/batch` (`id` for replacement,
`timestamp`, `label`, `metadata`, optional `audience`), the Hermes `MemoryProvider` interface
(`agent.memory_provider`). Verified manually against a real Hermes, like the other connectors.
