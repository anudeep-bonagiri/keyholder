# Keyholder

An incident room on Switch where the rollback runs only when the person holding the commander seat approves it, customers are told in their own room by the one agent allowed to speak to them, and a rogue "just roll it back" is refused.

- **Demo video (2:00):** _link_
- **Interactive walkthrough:** _link_
- **The template:** [`keyholder.template.yaml`](keyholder.template.yaml)

Built for the WeMakeDevs x DevTools Academy **Flip the Switch** hackathon, Nov 4 to 7, 2026. Track: Best Business Workflow. Every file here was written inside the hackathon window.

## The problem

Incident bots are everywhere now. An agent reads the logs, proposes a rollback, and someone presses approve. The weak point is the word *someone*: it is whoever happens to be in the channel at 3 AM, and nothing checks that the gate actually holds. Keyholder makes the approval belong to a named seat, proves the gate on camera, and keeps customers out of the war room.

## What happens, in two minutes

1. An engineer reports that checkout is failing. Anyone in the war room can report.
2. The investigator agent reads the deploy log, the metrics, the error log and the source line in the stack trace, then posts a minute-by-minute timeline with the evidence quoted.
3. It proposes exactly one remediation, a rollback, and shows the dry-run preview. Then it waits.
4. Someone posts `approve: rollback`. Nobody holds the commander seat, so it is refused in one line. Nothing ran.
5. The on-call engineer claims the seat and approves. Switch asks the room owner to allow the command. One tap. The rollback runs and the service is healthy again.
6. The communicator agent posts a plain-language update in the customer status room, on a different messaging app. A postmortem document appears in the war room with the seat log: who was refused, who approved, who allowed.

## Why Switch, and what breaks without it

| Switch primitive | What it does in Keyholder | Without it |
|---|---|---|
| **Template** | One YAML file creates both agents, both rooms, the link, the roles, the documents and the kickoff. The server validates the whole document before creating anything. | Manual setup that no judge could reproduce. |
| **Addressing policy** | The investigator is addressable by `anyone`, so any teammate can report. The communicator is `owner-agents`, so only the investigator can hand it text. | Anyone in the channel can drive the customer-facing agent. |
| **Room documents** | The commander seat, the runbook, the comms policy and the postmortem live in the room where everyone can read them. The investigator re-reads the seat before every action and logs every change. | The seat lives in one agent's memory, invisible and unauditable. |
| **Approval cards** | When the investigator runs `rollback.sh`, Switch turns Claude Code's permission request into a card the room owner answers in chat. Enforced by the Switch server. | The agent's own judgment is the only gate. |
| **Linked rooms on two bridges** | The war room runs on Mattermost or Slack. The status room takes Telegram or Discord when connected. One conversation for the agents, two audiences for people. | Customers sit in the engineering channel, or a human copies updates by hand. |
| **Roles** | The communicator role is exclusive. There is one voice to customers even if more agents join the room. | Two agents post conflicting updates. |

Take Switch away and you have two CLI sessions, a shell script and a Slack bot that anyone can trigger.

## Reproduce it in ten minutes

You need Switch Console, Docker, and Claude Code signed in. Codex or OpenCode also work; the template picks the first one installed.

1. Install Switch Console from the [Switch releases page](https://github.com/sandbox-quantum/switch/releases/latest) and finish the [quickstart](https://docs.switchagents.ai/switch-rooms/getting-started) until switch-buddy answers.
2. Optional: under Messaging apps, connect Telegram or Discord. The status room will use it automatically. With neither connected, both rooms land on the bundled Mattermost and the linked-room mechanics are identical.
3. Clone this repo. In Switch Console open Templates, import `keyholder.template.yaml`, and run it with team `checkout`. The agents clone this repo into their working directories, so the fixture is already in place.
4. Open `checkout-war-room`. You should see the investigator confirm that `COMMANDER-SEAT` exists with an empty holder, and the communicator confirm it will post only approved text.
5. Follow [`demo/SCRIPT.md`](demo/SCRIPT.md) line by line. Checkpoints: the dry-run preview appears; the first `approve: rollback` is refused; after `commander: claim` the second one triggers an approval card; after Allow once, `status.sh` reports HEALTHY; the status room receives one update; an `INCIDENT-...` document appears.

Reset the fixture between runs:

```
cd fixtures/checkout-service
echo v2.14.0 > releases/current
echo v2.13.3 > releases/previous
git checkout deploys.log
```

Colima instead of Docker Desktop: there is no `/var/run/docker.sock`. Launch the Console from a terminal with `DOCKER_HOST=unix://$HOME/.colima/default/docker.sock` and Homebrew's `docker` on `PATH`, or symlink the socket.

## What is enforced where

Honesty matters more than a tidy diagram.

- **Who may approve.** The investigator reads `COMMANDER-SEAT` before every action and accepts `approve: rollback` only from the named holder. This is instruction-level, and the document log makes every decision auditable. A determined jailbreak of the agent is out of scope for a four-day build; the next gate catches it.
- **Whether the command runs at all.** Switch's approval card to the room owner. Server-enforced.
- **Who speaks to customers.** Room membership. Only the communicator is in the status room; the investigator is not.

## Design choices

- **Approval belongs to a seat, not a channel.** Claim it, hand it off mid-incident, release it. The room always knows who is accountable right now, and the log says who was.
- **Proof over promise.** The demo opens with a rogue approval being refused. A gate you have not watched fail is a gate you are trusting.
- **Two rooms, two audiences.** Engineers need the stack trace. Customers need three calm lines. Putting them in different rooms on different apps is a Switch primitive, not a workaround.
- **One remediation, previewed.** The investigator never offers a menu. It shows the dry run of the one thing it wants to do, so the approver decides on evidence.

## The fixture

`fixtures/checkout-service` is a small synthetic service: a deploy log, a minute-by-minute metrics file, an error log with a stack trace, the source file it points at, `status.sh` (read-only) and `rollback.sh` (the one state-changing action, with `--dry-run`). The incident is a v2.14.0 deploy that added a payment retry path which dereferences a missing token on guest checkout. Error rate goes from 0.3 percent to 18.7 percent one minute after the deploy. No real customer data anywhere.

## Lineage

Keyholder is written from scratch. Its shape is the one that has won repeatedly this year, and it takes one idea from each:

- **ONCALL** (WeMakeDevs Agent Harness Hackathon): investigate first, remediate only behind a human gate, report into chat.
- **Mayday** (WeMakeDevs Agent Harness Hackathon, Best Blog): test whether the approval gate actually holds.
- **Cite-Before-Act MCP** (Anthropic and Gradio MCP birthday hackathon, Best Overall): a dry-run preview before any state-changing action.
- **Copilot Cowork ITSM** (Microsoft Agent Academy, 1st): one-tap approval inside the chat app.

What none of them had: a seat that changes hands mid-incident with a log, a second room on a second app for the people affected, and a rogue approval refused on camera.

## Why it matters

| Number | Source |
|---|---|
| Median cost of a high-impact outage: about $2M per hour | New Relic, 2025 Observability Forecast |
| 54 percent of responders interrupted outside working hours; more than 60 percent answer off-hours alerts weekly | PagerDuty, State of Digital Operations |
| Elite teams recover from a failed deploy in under an hour; low performers take a week to a month | DORA, Accelerate State of DevOps 2024 |

The first minutes of an incident are when a tired person is most likely to press the wrong button, and when the wrong person is most likely to press it. Keyholder makes the agent do the reading and makes the button belong to someone.

## Repository map

```
keyholder.template.yaml   the whole room group: agents, rooms, link, roles, documents, kickoffs
fixtures/checkout-service the synthetic service the investigator works on
demo/SCRIPT.md            the two-minute run, line by line, with reset steps
demo/SUBMISSION.md        the hackathon form answers and the #HowISwitch posts
demo/video/               renderer, narration script and build script for the walkthrough video
site/                     the interactive walkthrough deployed on Vercel
```

## License

MIT
