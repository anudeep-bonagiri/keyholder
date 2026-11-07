# Keyholder

An incident room where the rollback only runs when the person holding the commander seat approves it, customers are told in their own room by the one agent allowed to speak to them, and a rogue "just roll it back" is refused.

Built for the WeMakeDevs x DevTools Academy **Flip the Switch** hackathon, Nov 4 to 7, 2026. Track: Best Business Workflow. Everything in this repo was built inside the hackathon window.

Demo video: _link goes here_

## Thirty seconds of what happens

1. Someone reports that checkout is failing. The investigator agent reads the deploy log, the metrics, the error log and the source line in the stack trace, and posts a timeline with quoted evidence.
2. It proposes exactly one remediation, a rollback, with a dry-run preview. Then it waits.
3. Someone posts `approve: rollback`. The commander seat is empty, so it is refused. Nothing ran.
4. Someone claims the seat and approves. Switch asks the room owner to allow the command. One tap. The rollback runs, the service is healthy again.
5. The investigator hands one paragraph to the communicator agent. Customers see a plain-language update in their own room, on their own app. They never see the war room.
6. A postmortem document appears in the room with the seat log: who was refused, who approved, who allowed.

## Why it is different from an incident bot

Most "agent proposes, human approves" rooms have one agent, one channel and one approve button that anyone in the channel can press. Keyholder adds three things, each built on a Switch primitive.

| Improvement | Switch primitive it stands on |
|---|---|
| Approval belongs to a seat, not to whoever is in the channel. Claim it, hand it off mid-incident, release it. Every change is logged. | A room document (`COMMANDER-SEAT`) the investigator creates and owns, re-read before every action. |
| Two rooms, two audiences. Engineers work on one app, customers read on another. The investigator is not in the customer room at all. | A room group with linked rooms, each on its own messaging bridge (`status_bridge` defaults to Telegram or Discord when connected). |
| The gate is proven, not promised. The demo opens with a rogue approval being refused, then shows the real one run. | The investigator's addressing is `anyone` so anyone can report; the communicator's is `owner-agents` so only the investigator can hand it text. Switch's own approval card is the second, server-side gate. |

## What Switch does here, and what breaks without it

- **Two agents, two rooms, one template.** `keyholder.template.yaml` creates both agents, both rooms, the roles, the room documents and the link in one pass.
- **Addressing policy** decides who may command which agent. Anyone can report to the investigator; only the investigator can feed the communicator.
- **Roles.** The investigator takes `responder` (shared); the communicator takes `communicator` (exclusive), so there is one voice to customers even if more agents join.
- **Room documents** hold the runbook, the comms policy, the commander seat, and the postmortem. The seat lives in the room, where everyone can see it, not in the agent's memory.
- **Approval cards.** When the investigator runs `rollback.sh`, Switch turns the agent's permission request into a card the room owner answers in chat. That gate is enforced by the Switch server, not by a prompt.
- **Linked rooms across messaging apps.** The war room and the status room can be on different apps. Without Switch there is no shared place where the approval, the agent's action and the customer update are the same conversation.

Take Switch away and you have two CLI sessions, a shell script and a Slack bot that anyone can trigger.

## What is enforced where

Honesty matters more than a tidy diagram.

- **Who may approve:** enforced by the investigator reading `COMMANDER-SEAT` before every action. It is instruction-level, and the document log makes every decision auditable. A determined jailbreak of the agent is out of scope for a four-day build; the next gate catches it.
- **Whether the command runs at all:** enforced by Switch's approval card to the room owner.
- **Who speaks to customers:** enforced by membership. Only the communicator is in the status room.

## Run it

You need Switch Console, Docker, and Claude Code or Codex signed in. The Switch quickstart takes about ten minutes.

1. Install Switch Console from the Switch releases page and finish the quickstart (local server, switch-buddy answering).
2. Optional: connect Telegram or Discord under Messaging apps. The status room will use it automatically. With neither connected, both rooms land on the bundled Mattermost.
3. In Switch Console, open Templates, import `keyholder.template.yaml` from this repo, and run it. Keep `team` as `checkout`. The agents clone this repo into their working directories, so the fixtures are already there.
4. Open `checkout-war-room` and follow `demo/SCRIPT.md`.

To reset the fixture between runs:

```
cd fixtures/checkout-service
echo v2.14.0 > releases/current
echo v2.13.3 > releases/previous
git checkout deploys.log
```

## The fixture

`fixtures/checkout-service` is a small synthetic service: a deploy log, a minute-by-minute metrics file, an error log with a real-looking stack trace, the source file it points at, `status.sh` (read-only) and `rollback.sh` (the one state-changing action, with `--dry-run`). The incident is a v2.14.0 deploy that added a payment retry path which dereferences a missing token on guest checkout. Error rate goes from 0.3 percent to 18.7 percent one minute after the deploy.

## Reference points

Keyholder is written from scratch. Its shape is the one that has won repeatedly this year, and it borrows one idea from each:

- ONCALL (WeMakeDevs Agent Harness Hackathon): parallel investigation, human-gated remediation, results posted to chat.
- Mayday (WeMakeDevs Agent Harness Hackathon, Best Blog): testing whether the approval gate actually holds.
- Cite-Before-Act MCP (Anthropic and Gradio MCP birthday hackathon, Best Overall): a dry-run preview before any state-changing action.
- Copilot Cowork ITSM (Microsoft Agent Academy, 1st): one-tap manager approval in the chat app.

What none of them had: a seat that can change hands mid-incident with a log, a second room on a second app for the people affected, and a rogue approval refused on camera.

## Why this matters

Median cost of a high-impact outage is about $2M per hour (New Relic 2025 Observability Forecast). 54 percent of responders are interrupted outside working hours and more than 60 percent answer off-hours alerts weekly (PagerDuty State of Digital Operations). The first minutes of an incident are when a tired person is most likely to press the wrong button, and when the wrong person is most likely to press it. Keyholder makes the agent do the reading and makes the button belong to someone.

## License

MIT
