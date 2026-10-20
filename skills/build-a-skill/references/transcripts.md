# Finding the start in the transcript

The skill is built from the conversation, so the first job is to find where the story began:
the prompt that produced the first almost-right output. The first correction is not the start;
the task before it is.

## Read the conversation you have

Read backwards from the latest message. The start is the last user message before the first
output that the user later corrected. Mark the prompt, the output, and each correction after it.

## When the context was summarized or the start is older

Agents keep the full session on disk. Open it with the tools you have (read the file, search it
for a phrase from the task) and never paste it whole into the conversation.

| Agent | Where the transcript lives | How to find the right one |
|---|---|---|
| Codex | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | One JSON object per line; the first line names the `cwd`. Pick the newest file whose `cwd` is this repository. User turns have `"role": "user"`. |
| Claude Code | `~/.claude/projects/<cwd with every slash replaced by a dash>/*.jsonl` | One JSON object per line; `message.role` is `user` or `assistant`. The newest file is the current session. |
| Another agent | Ask the user where it keeps sessions, or ask them to paste the first prompt | |

Timestamps in these files are UTC. Use the first prompt's time to find the commit that was
checked out then: `git log -1 --before="<time>" --format=%H`, or the commit the transcript shows
in a tool call around that time.

## When you cannot tell

Do not guess. Quote the message you believe started it and ask one question: "Is this the prompt
where it started, or was it earlier?" If the user names a message, use that. If they cannot
remember, ask for the task in their words and treat the earliest matching output as the start.
