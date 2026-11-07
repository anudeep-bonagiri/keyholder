# Demo script (about two minutes)

Record the Switch Console or Mattermost window. Keep the Console open the
whole time; local agents only answer while it is open.

Room: checkout-war-room (and checkout-status in a second window or phone).

1. Post:
   @checkout-investigator checkout is failing for customers, 500s on
   /checkout/confirm since about 17:22 UTC. Investigate.
   Wait for: timeline, the v2.14.0 deploy, AttributeError at
   payment_retry.py:17, the dry-run preview, "Seat holder: (empty)".

2. The rogue message. Post:
   approve: rollback
   Expect: refused in one line, seat is empty, proposal stays open.
   (Nothing ran. Say that out loud on the recording.)

3. Post:
   commander: claim
   Expect: "Seat holder: <you>" and a dated line in COMMANDER-SEAT.

4. Optional handoff, if you have a second user in the room:
   commander: handoff @bob
   then from your account:  approve: rollback   -> refused, bob holds it.
   From bob:                approve: rollback   -> proceeds.
   Skip this step if you are alone; the empty-seat refusal in step 2
   already proves the gate.

5. Post (as the seat holder):
   approve: rollback
   Expect: the investigator says it has requested the command, a Switch
   approval card appears for the room owner. Tap Allow once.
   Expect: "rolled checkout-service back from v2.14.0 to v2.13.3" and
   status HEALTHY, error rate 0.3%.

6. Switch to checkout-status. Expect one plain-language update from
   checkout-comms, under 60 words, no versions or internal names.

7. Back in the war room: open the INCIDENT-... document. Show the seat
   log with the refused approval and the approval that ran.

Reset between takes:
   cd fixtures/checkout-service && echo v2.14.0 > releases/current && echo v2.13.3 > releases/previous && git checkout deploys.log
