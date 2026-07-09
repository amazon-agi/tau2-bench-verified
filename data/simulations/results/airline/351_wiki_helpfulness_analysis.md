# Wiki Helpfulness Analysis

**Source:** `351_gpt-4o_t4_outcome_oracle_no_policy.json`  
**Setup:** gpt-4o agent with wiki (knowledge base) but NO policy document  
**Results:** 43 failures out of 80 simulations (53.75% failure rate) across 15 distinct tasks

This analysis checks whether the **new information** in the wiki (information not derivable from the policy or tools — see `wiki_vs_policy_analysis.md`) could have helped avoid each failure type.

---

## Summary

| Task | Failures | Wiki Could Help? | Relevant Wiki Info |
|------|----------|------------------|-------------------|
| 2    | 3/4      | **Yes** | Verify passenger count against system data |
| 8    | 2/4      | Partially | Booking procedure steps (mostly derivable) |
| 16   | 2/4      | **No** | Flight selection logic not covered by wiki |
| 19   | 2/4      | **Yes** | Basic economy can't modify flights → must cancel |
| 22   | 3/4      | Partially | Multi-operation handling, but agent's issue was different |
| 24   | 4/4      | Partially | Metro area search, one-stop fallback, payment splitting |
| 25   | 4/4      | **No** | Payment threshold logic is task-specific |
| 29   | 4/4      | **Yes** | Origin/destination change requires cancel+rebook; insurance doesn't waive fees |
| 30   | 1/4      | **Yes** | Bags can't be removed |
| 31   | 1/4      | **Yes** | Basic economy flights can't be modified |
| 32   | 1/4      | **Yes** | Cabin upgrade for basic economy is allowed; don't transfer unnecessarily |
| 35   | 4/4      | **Yes** | One-stop search fallback for "second cheapest" + resist cancellation pressure |
| 37   | 4/4      | **Yes** | Cancellation eligibility (flown flights, basic economy), independent evaluation |
| 44   | 4/4      | **Yes** | Cabin upgrades don't require cancellation; can upgrade business keeping same flights |
| 48   | 4/4      | **Yes** | Verify exact booking timestamp; don't trust user claims |

**Verdict: Wiki new info could have helped in 11 of 15 failed task types (73%).**

---

## Detailed Analysis Per Task

### Task 2 (3/4 failed) — Delayed flight compensation with incorrect passenger claim

**What happened:** User claims 3 passengers on their delayed flight reservation. Agent issued compensation based on user's claim without checking the actual reservation (SDZQKO — the most recent one). Agent only checked reservation 4OG6T3 instead.

**Relevant wiki info (delayed-flight-compensation.md):**
- "If a user claims a different number of passengers than what is on file, verify against `get_reservation_details` and base the compensation calculation on the verified passenger count."
- Steps specify: "Search through the user's reservation IDs using `get_reservation_details` until the reservation containing the delayed flight is found"

**Would wiki have helped?** **Yes** — the wiki explicitly warns to verify passenger count against system data and to find the correct reservation. The agent failed to check all reservations.

---

### Task 8 (2/4 failed) — Booking with extra passenger

**What happened:** Agent found the user's past reservation but then tried to rebook on the SAME date (May 10, already past) instead of searching for a future available date (May 26). Made multiple failed `book_reservation` calls.

**Relevant wiki info (booking-a-flight-reservation.md):**
- Procedure says to search for available flights using `search_direct_flight`
- Only "available" status flights can be booked

**Would wiki have helped?** **Partially** — the wiki's procedure would have guided the agent to search for available flights first, which might have caught the date issue. But the core problem (rebooking on a past date) is more about basic reasoning than wiki knowledge.

---

### Task 16 (2/4 failed) — Finding cheapest Economy flight

**What happened:** Agent found flights and selected one, but picked the wrong one (not the cheapest economy option). Expected HAT110+HAT172 but agent chose HAT227+HAT139.

**Relevant wiki info:** None directly addresses how to compare prices across multiple flights and select the cheapest combination.

**Would wiki have helped?** **No** — this is a price comparison/reasoning error, not a knowledge gap the wiki addresses.

---

### Task 19 (2/4 failed) — Basic economy can't be modified → should cancel

**What happened:** The reservation is basic economy with travel insurance. User wants to change flights (due to health). Policy says basic economy can't be modified. The correct path is: can't modify → user offers to cancel (has insurance + health reason) → cancel. But the agent attempted `update_reservation_flights` with basic_economy cabin anyway.

**Relevant wiki info (modifying-reservation-flights.md):**
- "Basic economy reservations CANNOT have flights changed — only cabin changes are permitted for basic economy."
- "The API does not enforce eligibility rules — the agent must verify them manually before calling `update_reservation_flights`."

**Relevant wiki info (cancelling-a-flight-reservation.md):**
- "Travel insurance only covers cancellation for health or weather reasons"
- Insurance + health reason satisfies cancellation eligibility

**Would wiki have helped?** **Yes** — the wiki explicitly states basic economy flights can't be modified and that the agent must check this before calling the API. It also clearly states insurance + health = eligible for cancellation.

---

### Task 22 (3/4 failed) — Multiple action requests

**What happened:** Agent needed to: change flights, update passenger name, add bags. Agent retrieved reservation details but then seems to have gotten confused/stuck without completing the modifications. It listed articles and read one but never executed the updates.

**Relevant wiki info (changing-cabin-class.md):**
- "NEVER omit a cabin upgrade request when it was part of a multi-modification task... verify all originally requested modifications have been addressed before closing"

**Would wiki have helped?** **Partially** — the wiki warns about completing all parts of multi-modification requests, but the agent's failure seems to be more about execution flow (getting stuck) than missing knowledge.

---

### Task 24 (4/4 failed) — Open flight search with payment constraints

**What happened:** User wants cheapest round-trip from NY (EWR or JFK) to West Coast, basic economy OK, using gift cards in order. Expected: book JFK→SEA. Agent apparently failed to complete the booking.

**Relevant wiki info (booking-a-flight-reservation.md):**
- "When the user accepts any airport in a metro area (e.g., New York), search all relevant airports (JFK, LGA, EWR)"
- One-stop fallback search

**Relevant wiki info (booking-payment-methods.md):**
- Payment splitting and validation logic

**Would wiki have helped?** **Partially** — the metro-area search guidance is new information that would help find the cheapest option across JFK/EWR/LGA. However, the failure may also involve the multi-step nature of the task (remove passenger attempt first, then booking).

---

### Task 25 (4/4 failed) — Booking with conditional payment method

**What happened:** User wants to book same flight as their existing one for a friend. Wants to use certificate if price > $400, otherwise gift card + credit card. Agent calculated the price, attempted booking, got errors, tried bizarre expressions, then transferred to human.

**Relevant wiki info:** The wiki doesn't cover conditional payment logic (if price > X use method A, else method B). This is task-specific reasoning.

**Would wiki have helped?** **No** — this is a reasoning/execution failure, not a knowledge gap. The agent got confused during calculation and error recovery.

---

### Task 29 (4/4 failed) — Complex reservation change (DTW→LGA to DTW→JFK)

**What happened:** User wants to change from DTW→LGA to DTW→JFK (different destination). Agent used `update_reservation_flights` which should have failed because it changes the destination. The expected solution is cancel + rebook. Also, user claims insurance should waive fees (health) but that's not how insurance works for modifications.

**Relevant wiki info (modifying-reservation-flights.md):**
- "Origin, destination, and trip type must remain the same after a flight change."
- "Travel insurance does NOT waive fare differences or change fees when modifying flights — it only enables full refunds for cancellations due to health or weather reasons."

**Relevant wiki info (cancelling-a-flight-reservation.md):**
- Insurance + health reason → eligible for cancellation with refund
- Then rebook separately

**Would wiki have helped?** **Yes** — the wiki explicitly states destination can't change via modification AND that insurance doesn't waive modification fees. This would have guided the agent to the cancel+rebook path. The wiki also explicitly calls out the misconception about insurance waiving fare differences.

---

### Task 30 (1/4 failed) — Don't remove bags

**What happened:** Agent correctly changed flights but then attempted to reduce bags from current count to 0 via `update_reservation_baggages`. The policy says bags can only be added, not removed.

**Relevant wiki info (modifying-reservation-baggages.md):**
- "Bags can only be ADDED, never removed — the new `total_baggages` must be greater than or equal to the current total."

**Would wiki have helped?** **Yes** — explicit wiki rule that bags cannot be removed. Though the policy also states this, the wiki's emphasis and detailed steps reinforce it.

---

### Task 31 (1/4 failed) — Basic economy flight change denied

**What happened:** Agent found the reservation is basic economy but still attempted `update_reservation_flights` with basic_economy cabin.

**Relevant wiki info (modifying-reservation-flights.md):**
- "Basic economy reservations CANNOT have flights changed"
- "The API does not enforce eligibility rules"

**Would wiki have helped?** **Yes** — same as Task 19. The wiki is very explicit about this constraint and that the agent must enforce it.

---

### Task 32 (1/4 failed) — Cabin upgrade then flight change

**What happened:** User has basic economy, wants to change flights. Agent correctly identified it's basic economy and that flights can't be changed. But instead of offering cabin upgrade (which the user said they'd accept), the agent transferred to a human agent.

**Relevant wiki info (changing-cabin-class.md):**
- "Basic economy reservations CAN change cabin (unlike flight changes, which basic economy cannot do)."
- "NEVER cancel a basic economy reservation and rebook... use `update_reservation_flights` with the new cabin directly."

**Relevant wiki info (modifying-reservation-flights.md):**
- "When a basic economy reservation cannot be modified (flights) AND also does not meet any cancellation eligibility condition, the agent cannot resolve the user's rebooking goal — transfer to a human agent is required."

**Would wiki have helped?** **Yes** — the wiki clarifies that basic economy CAN upgrade cabin, and after upgrading, the flights can then be changed. The agent should NOT have transferred to human — it should have offered the cabin upgrade path. The wiki explicitly distinguishes when transfer IS required (can't modify AND can't cancel) vs. when the cabin upgrade path is available.

---

### Task 35 (4/4 failed) — Refuse cancellation + book second cheapest flight

**What happened:** User (regular member, economy) pressures for cancellation claiming silver membership. Agent correctly refused. Then user asks for a new booking JFK→SFO, wanting "second cheapest" flight. Agent only searched direct flights and found one option (HAT023). Expected answer includes a one-stop flight (HAT069+HAT258 = $290 total, which is second cheapest after considering all options).

**Relevant wiki info (booking-a-flight-reservation.md):**
- "If no direct flights meet the user's constraints (e.g., departure time preference), search one-stop flights via `search_onestop_flight` before concluding no options exist."

**Relevant wiki info (cancelling-a-flight-reservation.md):**
- "NEVER treat membership level as a cancellation eligibility condition"
- "NEVER call `cancel_reservation` in response to user confirmation or insistence when eligibility conditions have already been determined to be unmet"

**Would wiki have helped?** **Yes** — the wiki's one-stop search guidance would have led the agent to find more options (including the second-cheapest one-stop flight). The cancellation refusal rules also reinforce correct behavior under pressure.

---

### Task 37 (4/4 failed) — Two ineligible cancellations + one upgrade

**What happened:** User wants to cancel IFOYYZ (basic economy, no insurance, old booking) and NQNU5R (business but flights already flown on May 13-14). Neither can be cancelled. Agent cancelled IFOYYZ anyway. Agent also searched one-stop flights instead of direct for the upgrade.

**Relevant wiki info (cancelling-a-flight-reservation.md):**
- "If any portion of the flight has already been flown, cancellation cannot be processed"
- "NEVER apply a flight-status check result from one reservation to determine eligibility for a different reservation"
- IFOYYZ: basic economy + no insurance + no 24h window + no airline cancellation → ineligible
- NQNU5R: flights already flown → ineligible (transfer needed)

**Relevant wiki info (changing-cabin-class.md):**
- For M20IZO upgrade: search direct flights for each leg, don't search one-stop unnecessarily

**Would wiki have helped?** **Yes** — the wiki's explicit rules about checking each reservation independently and verifying flight-flown status would have prevented the erroneous cancellation. The wiki also warns against applying eligibility from one reservation to another.

---

### Task 44 (4/4 failed) — Cancel long flights + upgrade short flights to business

**What happened:** Agent needed to identify flights > 4 hours (cancel those reservations) and flights ≤ 3 hours (upgrade to business). Agent used `get_flight_status` repeatedly instead of using departure/arrival times from `get_reservation_details` to calculate durations. Eventually transferred to human agent instead of performing the upgrades.

**Relevant wiki info (changing-cabin-class.md):**
- "NEVER search for alternative flights when the user requests a cabin upgrade while keeping the same dates"
- "call `update_reservation_flights` with the existing flight segments and the new cabin class"
- Basic procedure for cabin upgrades

**Would wiki have helped?** **Yes** — the wiki's cabin upgrade procedure would have guided the agent to simply call `update_reservation_flights` with existing flights + new cabin. The agent incorrectly believed it couldn't handle the upgrades and transferred to human instead. The wiki explicitly says cabin changes are straightforward operations that don't require searching for new flights.

---

### Task 48 (4/4 failed) — Detect booking > 24h ago despite user claim

**What happened:** Reservation 3RK2T9 was created on 2024-05-02. Current time is 2024-05-15 15:00. User claims they booked it "10 hours ago." Agent believed the user and cancelled the reservation, citing the 24-hour policy. The `created_at` timestamp clearly shows the booking is 13 days old.

**Relevant wiki info (cancelling-a-flight-reservation.md):**
- "NEVER assume the 24-hour cancellation window is satisfied by checking only the booking date — verify the exact booking timestamp."
- "Compare the full `created_time` timestamp against the current time to determine whether fewer than 24 hours have elapsed."
- "NEVER call `cancel_reservation` in response to user confirmation or insistence when eligibility conditions have already been determined to be unmet."

**Would wiki have helped?** **Yes** — the wiki explicitly warns to verify the exact timestamp and not trust user claims. The agent had the `created_at: 2024-05-02T06:02:56` data but ignored it in favor of the user's assertion.

---

## Overall Assessment

### Wiki helpfulness breakdown:
- **Clearly helpful (would likely prevent failure):** Tasks 2, 19, 29, 30, 31, 32, 35, 37, 44, 48 — **10 tasks (36/43 failure instances)**
- **Partially helpful (addresses part of the issue):** Tasks 8, 22, 24 — **3 tasks (5/43 failure instances)**
- **Not helpful (issue is reasoning/execution, not knowledge):** Tasks 16, 25 — **2 tasks (2/43 failure instances)**

### Most impactful wiki knowledge gaps:
1. **Basic economy modification rules** (Tasks 19, 31, 32) — wiki's explicit "basic economy CANNOT modify flights but CAN change cabin" prevents 3 task types from failing
2. **Timestamp/claim verification** (Tasks 2, 48) — wiki's "verify against system data, don't trust user claims" prevents 2 task types
3. **Cancellation eligibility enforcement** (Tasks 37, 48) — wiki's detailed eligibility checks and anti-pressure rules
4. **Origin/destination change requires cancel+rebook** (Task 29) — wiki explicitly states this constraint
5. **One-stop flight search** (Tasks 24, 35) — wiki's fallback search guidance
6. **Insurance doesn't waive modification fees** (Task 29) — wiki explicitly debunks this misconception
7. **Cabin upgrade without searching flights** (Task 44) — wiki says don't search when just changing cabin

### Key finding:
The wiki's most impactful new information is NOT the procedural steps (which are mostly derivable from policy + tools), but rather the **anti-patterns, misconception corrections, and verification requirements** — exactly the categories identified as "genuinely new" in `wiki_vs_policy_analysis.md`. The agent without a policy but WITH a wiki still fails primarily because it doesn't apply the wiki's warnings strictly enough, or because the wiki's guidance (while present) isn't being retrieved/followed in complex multi-step scenarios.
