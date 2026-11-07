---
title: Who is allowed to say yes? Building Keyholder, a seat-gated incident room on Switch
published: false
tags: hackathon, howiswitch, switch, ai
---

I spent the Flip the Switch hackathon on one question: when an AI agent can roll back production from a chat room, who is allowed to say yes, and can you prove the wrong person cannot?

This post is the build log for Keyholder, a Switch room template that answers that question. If you have never used Switch, the second half is the part I wish I had read first.

Repo: https://github.com/anudeep-bonagiri/keyholder. Walkthrough: https://keyholder-demo.vercel.app.

## The problem with incident bots

Every incident bot works the same way. An agent reads the logs, proposes a rollback, and someone presses approve. The weak point is the word *someone*. In a channel at 3 AM it means whoever is awake, and nothing checks that the approval gate actually holds. I wanted three things an incident bot usually does not have:

1. The approval belongs to a named seat, not to the channel, and the seat can change hands mid-incident with a log.
2. Customers are told what is happening in their own room, on their own app, by one agent that cannot say anything unapproved.
3. The gate is proven, not promised. The demo opens with a rogue approval being refused.

## What Switch gave me for free

Switch connects coding agents such as Claude Code or Codex to Slack, Teams, Discord, Telegram and Mattermost, and gives them rooms to work in with people. Five of its primitives carried the whole design.

**Templates.** One YAML document creates agents, rooms, the links between rooms, roles, documents and a kickoff message, and the server validates the entire document before creating anything. This is the single most important feature for a hackathon, because it means a judge can reproduce your room by importing one file.

**Addressing policy.** Each agent declares who may command it: `owner`, `owner-agents`, or `anyone`. My investigator is `anyone`, so any teammate can report an incident. My communicator is `owner-agents`, so only the investigator can feed it text. One line each.

**Room documents.** Documents live in the room where every member can read them. I put the runbook and the comms policy there, and the investigator creates a `COMMANDER-SEAT` document at kickoff that records who holds the seat and logs every change.

**Approval cards.** When a Claude Code agent asks permission to run a command, Switch turns that prompt into a card in the chat with Allow once, Allow for this session, and Decline. Only the room owner can answer. This is the server-enforced half of my gate.

**Linked rooms on different messaging apps.** The engineering war room and the customer status room are one conversation for the agents and two audiences for people. The status room takes Telegram or Discord when connected, so customers never sit in the engineering app.

## How the gate works

The investigator reads the deploy log, the metrics, the error log and the source line in the stack trace, posts a minute-by-minute timeline with the evidence quoted, and proposes exactly one remediation with a dry-run preview. Then it waits.

It runs the rollback only after a message that says exactly `approve: rollback` from the person named as holder in `COMMANDER-SEAT`, and it re-reads the document before acting. If the seat is empty or someone else approves, it refuses in one line and the proposal stays open. When it does run the command, Switch's approval card appears for the room owner. Two gates, in series.

After the rollback it verifies with a read-only status script, hands one paragraph marked `APPROVED FOR CUSTOMERS` to the communicator, and writes a postmortem document with the seat log: who was refused, who approved, who allowed.

## What I learned about Switch, and what I would tell a first-time user

- **Roles are hats for agents, not for people.** I assumed a role with an exclusive lease could be held by a human. It cannot. I built the human seat as a room document instead, which is auditable but enforced by the agent reading it. If you need a server-enforced human gate today, the approval card to the room owner is it.
- **Start from a shipped template.** `examples/agent-templates/support-desk.template.yaml` in the Switch repo already shows two agents across two linked rooms. I copied its shape, not its text.
- **Mention your agents in the kickoff.** Agents only start working when a message addresses them. A room with no kickoff is a room where nothing happens.
- **Local agents answer only while Switch Console is open.** Keep it open during your demo.
- **Colima users:** there is no `/var/run/docker.sock`. Launch the Console from a terminal with `DOCKER_HOST=unix://$HOME/.colima/default/docker.sock` and Homebrew's `docker` on `PATH`.
- **Keep the state-changing surface to one script.** My fixture has exactly one command that changes anything, `rollback.sh`, with a `--dry-run` flag. That makes the approval card mean something specific.

## What I would want Switch to add

People-side roles with leases, approval cards that can be gated by a named person or role instead of the owner, and native scheduled triggers. With those three, the whole Keyholder gate could move from instructions into the server.

## Try it

Install Switch Console, finish the ten-minute quickstart, import `keyholder.template.yaml` from the repo on the Templates page, and follow `demo/SCRIPT.md`. The first `approve: rollback` should be refused. If it is not, the gate is broken and I want to hear about it.
