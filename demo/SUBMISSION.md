# Paste-ready submission text

Form: https://www.wemakedevs.org/hackathons/switch/submit (WeMakeDevs sign-in)

**Project name:** Keyholder

**One line:** An incident room on Switch where the rollback only runs when the person holding the commander seat approves it, customers are told in their own room by the one agent allowed to speak to them, and a rogue "just roll it back" is refused.

**Track:** Best Business Workflow

**Repo:** https://github.com/anudeep-bonagiri/keyholder

**Demo video:** (paste link)

**Description (longer field):**
Keyholder is a Switch room template that stands up two agents and two linked rooms in one pass. The investigator sits in the engineering war room: on an incident report it reads the deploy log, metrics, error log and the source line in the stack trace, posts a timeline with quoted evidence, and proposes exactly one remediation with a dry-run preview. It never acts on that proposal unless the approval comes from whoever holds the commander seat, a room document it owns and re-reads before every action. The seat can be claimed, handed off mid-incident and released, and every change is logged. Switch's own approval card to the room owner is the second, server-side gate. The communicator agent is the only agent in the customer status room, which can live on a different messaging app, and it posts only text the investigator has marked approved, rewritten in plain language. The demo opens with a rogue approval being refused, then shows the real one run, the customer update land in the other room, and the postmortem document with the seat log.

**Which agents you connected:** Claude Code (both agents; the template also accepts Codex or OpenCode).

**How the channel is set up:** One room group: `checkout-war-room` (private, investigator + communicator, roles responder and communicator, documents RUNBOOK, COMMS-POLICY, COMMANDER-SEAT, postmortem) linked to `checkout-status` (public, communicator only, on Telegram or Discord when connected, else the bundled Mattermost).

**How to run it:** Install Switch Console, finish the quickstart, import `keyholder.template.yaml` from the repo on the Templates page, run it with team `checkout`, open the war room and follow `demo/SCRIPT.md`.

**What would stop working without Switch:** the seat document everyone can see, addressing that lets anyone report but only the investigator feed the communicator, the approval card the server enforces, and two rooms on two apps sharing one conversation.

---

# #HowISwitch post (X)

Built Keyholder for #FlipTheSwitch: an incident room on @switch_ai_ where the rollback only runs when the person holding the commander seat approves it. Customers get their own room on their own app. The demo opens with a rogue "approve: rollback" being refused. #HowISwitch @devtoolsacademy @WeMakeDevs

https://github.com/anudeep-bonagiri/keyholder

# LinkedIn version

I spent the Flip the Switch hackathon (WeMakeDevs x DevTools Academy, powered by Switch AI) on one question: when an AI agent can roll back production, who is allowed to say yes?

Keyholder is a Switch room template. The investigator agent reads the logs and metrics, posts a timeline with quoted evidence, and proposes one remediation with a dry-run preview. It will not run it unless the approval comes from whoever holds the commander seat, a room document it owns and re-reads before every action. The seat can be handed off mid-incident, and every change is logged. Switch's approval card to the room owner is the second gate. A separate communicator agent is the only thing that ever speaks to customers, in their own room, on their own app.

The demo opens with a rogue approval being refused. Then the real one runs.

Repo: https://github.com/anudeep-bonagiri/keyholder
#HowISwitch
