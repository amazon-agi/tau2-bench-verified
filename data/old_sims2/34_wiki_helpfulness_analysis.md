# Wiki Helpfulness Analysis — Policy + Wiki Configuration

**Source:** `34_gpt-4o_t4_outcome_oracle.json`  
**Setup:** gpt-4o agent with BOTH policy document AND wiki (knowledge base)  
**Results:** 38 failures out of 80 simulations (47.5% failure rate) across 13 distinct task types

**Comparison with wiki-only (no policy):** The no-policy run (`351_*.json`) had 43/80 failures (53.75%) across 15 task types. Adding the policy reduced failures by ~5 instances and eliminated 2 task types (19, 31) from the failure list entirely.

---

## Summary

| Task | Failures | Wiki Read? | Wiki Could Have Helped? | Root Cause |
|------|----------|-----------|------------------------|------------|
| 2    | 3/4      | Yes (booking) | **Yes** | Didn't verify passenger count against system |
| 16   | 4/4      | Yes (modifying-flights) | **No** | Picked wrong cheapest flight (math/reasoning) |
| 18   | 1/4      | Yes (changing-cabin) | **No** | Failed to communicate total savings amount |
| 22   | 2/4      | No articles fetched | Partially | Got stuck mid-task, didn't complete operations |
| 24   | 4/4      | Yes (cancel, booking, baggage) | **Yes** | Didn't search SEA (West Coast = more than LAX/SFO) |
| 25   | 1/4      | No articles fetched | **No** | Calculation/reasoning confusion |
| 29   | 4/4      | Yes (modifying-flights) | **Yes — but ignored** | Changed destination via update (wiki says can't) |
| 30   | 1/4      | Yes (multiple) | Partially | Changed return flight user didn't ask to change |
| 32   | 3/4      | Yes (modifying-flights, cabin) | **Yes — but misapplied** | Miscalculated upgrade cost; failed to execute |
| 35   | 4/4      | Yes (booking) | **Yes — but ignored** | Cancelled ineligible reservation; missed one-stop |
| 37   | 3/4      | Yes (cancel, cabin) | **Yes — but ignored** | Cancelled already-flown reservation (NQNU5R) |
| 44   | 4/4      | Yes (cancel, flights, cabin) | **Yes — but ignored** | Cancelled instead of upgrading; wrong operations |
| 48   | 4/4      | Yes (cancelling) | **Yes — but ignored** | Believed user's false 24h claim despite seeing data |

---

## Detailed Analysis Per Task

### Task 2 (3/4 failed) — Delayed flight compensation with false passenger count

**What happened:** User claims 3 passengers on delayed flight. Agent found the correct reservation (4OG6T3, 1 passenger, basic economy with insurance). Agent issued $150 certificate (3 × $50) instead of $50 (1 × $50) — it believed the user's claim of 3 passengers instead of using verified system data.

**Wiki article fetched:** booking-a-flight-reservation (not the relevant one)

**Relevant wiki info (delayed-flight-compensation.md — NOT fetched):**
- "If a user claims a different number of passengers than what is on file, verify against `get_reservation_details` and base the compensation calculation on the verified passenger count."

**Would wiki have helped?** **Yes** — if the agent had fetched `delayed-flight-compensation.md`, the explicit rule to verify passenger count would have prevented this. The failure is partly in article selection (fetched booking article instead of compensation article).

---

### Task 16 (4/4 failed) — Finding cheapest Economy flight

**What happened:** Agent searched correctly (direct + one-stop from ATL to PHL), but selected the wrong combination. Expected HAT110+HAT172 but chose HAT227+HAT139. This is a price comparison error.

**Wiki article fetched:** modifying-reservation-flights.md

**Would wiki have helped?** **No** — the wiki doesn't contain flight-price comparison logic. This is a math/reasoning error where the agent failed to correctly identify the cheapest economy option from the search results.

---

### Task 18 (1/4 failed) — Downgrade reservations and communicate savings

**What happened:** Agent successfully executed all 5 cabin downgrades (DB reward = 1.0) but failed to communicate the total savings amount ($23,553) to the user.

**Wiki article fetched:** changing-cabin-class.md

**Would wiki have helped?** **No** — this is a communication failure. The wiki doesn't address how to calculate and report total savings across multiple downgrades. The agent did the operations correctly but forgot to answer the user's question about total savings.

---

### Task 22 (2/4 failed) — Multiple action requests (flight change + passenger + bags)

**What happened:** Agent retrieved reservation details but never executed any of the three required modifications. It seems to have gotten stuck after identifying the reservation.

**Wiki articles fetched:** None (no list_articles or get_article calls in this trial)

**Would wiki have helped?** **Partially** — the wiki's multi-operation handling guidance (changing-cabin-class.md: "verify all originally requested modifications have been addressed before closing") might have helped. But the core issue is the agent stalling rather than missing knowledge.

---

### Task 24 (4/4 failed) — West Coast flight search

**What happened:** User wants "cheapest direct flight round trip from New York to anywhere West Coast." Agent searched JFK→LAX, JFK→SFO, EWR→LAX, EWR→SFO but **never searched SEA** (Seattle). The cheapest was JFK→SEA. Agent booked EWR→LAX instead.

**Wiki articles fetched:** cancelling-a-flight-reservation, booking-a-flight-reservation, checked-baggage-allowance

**Relevant wiki info (booking-a-flight-reservation.md):**
- "When the user accepts any airport in a metro area (e.g., New York), search all relevant airports (JFK, LGA, EWR)"

**Would wiki have helped?** **Yes, partially** — the wiki's metro-area guidance helped the agent search both JFK and EWR (it did both). But the wiki doesn't explicitly say "West Coast = LAX + SFO + SEA + other cities." The agent's failure is in not being exhaustive about West Coast destinations. A wiki entry covering "search all major airports in a region" would have helped more.

---

### Task 25 (1/4 failed) — Conditional payment booking

**What happened:** Agent calculated the price ($299) and the certificate remainder ($500 - $299 = $201) but then stopped without completing the booking.

**Wiki articles fetched:** None in this trial.

**Would wiki have helped?** **No** — this is an execution/reasoning failure. The agent understood the task but didn't complete it.

---

### Task 29 (4/4 failed) — Destination change (DTW→LGA to DTW→JFK)

**What happened:** Agent fetched the modifying-reservation-flights article which says "Origin, destination, and trip type must remain the same after a flight change." Despite reading this, the agent proceeded to use `update_reservation_flights` to change the destination from LGA to JFK — and confirmed the user's request without flagging the policy violation. The correct path is cancel + rebook.

Also, the user claimed insurance should waive change fees (health issue). The wiki explicitly says "Travel insurance does NOT waive fare differences or change fees when modifying flights." Agent seems to have ignored both rules.

**Wiki article fetched:** modifying-reservation-flights.md ✓

**Would wiki have helped?** **Yes — it WAS fetched but IGNORED.** The wiki contained the exact rules needed (can't change destination; insurance doesn't waive fees) but the agent didn't apply them. This is a compliance/following-instructions failure, not a knowledge gap.

---

### Task 30 (1/4 failed) — Don't remove bags + flight change

**What happened:** Agent correctly changed the outbound flight to nonstop (HAT266) but also changed the return flight to HAT190 instead of keeping the original HAT112. The user only asked to change the outbound one-stop to nonstop — the return should stay unchanged.

**Wiki articles fetched:** modifying-reservation-flights, changing-cabin-class, modifying-reservation-passengers, modifying-reservation-baggages

**Relevant wiki info (modifying-reservation-flights.md):**
- "Kept flight segments do not have their prices updated based on the current price."
- Steps say to include unchanged segments in the API call

**Would wiki have helped?** **Partially** — the wiki mentions kept segments, but doesn't explicitly warn against changing flights the user didn't ask to change. The agent's error is scope creep (searching for and changing the return flight unprompted).

---

### Task 32 (3/4 failed) — Basic economy upgrade then flight change

**What happened:** Across different trials:
- **Trial 0:** Agent calculated upgrade cost as $132 (exceeding user's $100 budget), so the user gave up. But the expected solution shows the upgrade + flight change IS doable within budget when done in the correct sequence (upgrade first at lower cost, then change to cheaper nonstop).
- **Trial 1:** Agent correctly found nonstop flight HAT041 ($136) but miscalculated the total cost. The expected solution does upgrade first (keeping same flights = lower price diff), then changes to nonstop separately.

**Wiki articles fetched:** modifying-reservation-flights.md, changing-cabin-class.md

**Relevant wiki info (changing-cabin-class.md):**
- "NEVER search for alternative flights when the user requests a cabin upgrade while keeping the same dates — if the user wants to keep the same flights, call `update_reservation_flights` with the existing flight segments and the new cabin class."
- "When a combined flight-date change and cabin upgrade is requested, calculate the price difference as: (new flight prices at new cabin) minus (original flight prices at original cabin)"

**Would wiki have helped?** **Yes — but misapplied.** The wiki says to upgrade cabin first with existing flights (cheaper), then change flights separately. The user explicitly asked for this two-step process. The agent searched for new flights before upgrading, inflating the perceived cost. Had it followed the wiki's guidance to upgrade-with-same-flights first, the cost would have been lower.

---

### Task 35 (4/4 failed) — Refuse cancellation pressure + book second cheapest

**What happened:** Agent **cancelled** reservation M20IZO despite it being ineligible (economy, no insurance, booking older than 24h, no airline cancellation). The user claimed to be a silver member deserving a refund. Then for the new booking, agent searched JFK→SFO but only found one direct flight and tried to book it (not the second cheapest including one-stop options).

**Wiki articles fetched:** booking-a-flight-reservation (AFTER the cancel)

**Relevant wiki info (cancelling-a-flight-reservation.md — NOT fetched before cancel):**
- "NEVER treat membership level as a cancellation eligibility condition"
- "NEVER call `cancel_reservation` in response to user confirmation or insistence when eligibility conditions have already been determined to be unmet"

**Relevant wiki info (booking-a-flight-reservation.md):**
- "search one-stop flights via `search_onestop_flight` before concluding no options exist"

**Would wiki have helped?** **Yes — but the cancellation article was NOT fetched before the agent cancelled.** The agent fetched the booking article only after already making the wrong cancel. Had it fetched the cancellation article first, the explicit anti-pressure rules would have prevented the erroneous cancellation. For the booking, the one-stop search guidance was technically available but the agent searched one-stop and still picked the wrong option.

---

### Task 37 (3/4 failed) — Two ineligible cancellations + one upgrade

**What happened:** Agent correctly denied IFOYYZ cancellation (basic economy, no eligibility). It performed the M20IZO upgrade to business correctly. But then it cancelled NQNU5R — a business reservation whose flights were on May 13-14 (already flown by current time May 15).

**Wiki articles fetched:** cancelling-a-flight-reservation, changing-cabin-class ✓

**Relevant wiki info (cancelling-a-flight-reservation.md):**
- "If any portion of the flight has already been flown, cancellation cannot be processed by the agent — transfer to a human agent is required."

**Would wiki have helped?** **Yes — it WAS fetched but IGNORED.** The wiki clearly states that already-flown flights can't be cancelled. The agent had the reservation data showing May 13-14 dates and knew the current date is May 15, but cancelled anyway. This is a reasoning/compliance failure.

---

### Task 44 (4/4 failed) — Cancel long flights + upgrade short flights

**What happened:** Agent needed to: (a) identify flights > 4 hours, (b) cancel those reservations if eligible, (c) upgrade flights ≤ 3 hours to business. Agent used `get_flight_status` repeatedly instead of computing durations from departure/arrival times. Then it cancelled NM1VX1 (which should have been upgraded) and tried to upgrade S61CZX (which the user didn't want upgraded per the duration criteria). It also searched for replacement flights instead of simply upgrading cabin on existing flights.

**Wiki articles fetched:** cancelling-a-flight-reservation, modifying-reservation-flights, changing-cabin-class ✓

**Relevant wiki info (changing-cabin-class.md):**
- "NEVER search for alternative flights when the user requests a cabin upgrade while keeping the same dates"
- Procedure: call `update_reservation_flights` with existing flights + new cabin

**Would wiki have helped?** **Yes — it WAS fetched but IGNORED.** The wiki's guidance on cabin upgrades (keep same flights, don't search) was available but not followed. The agent also confused which reservations to cancel vs. upgrade, suggesting a reasoning failure beyond just knowledge.

---

### Task 48 (4/4 failed) — 24-hour window timestamp verification

**What happened:** Agent initially CORRECTLY identified that the reservation was created on May 2, 2024 (outside 24h window) and told the user it was ineligible. But when the user pushed back ("I booked it 10 hours ago"), the agent reversed its correct judgment, misreading `2024-05-02T06:02:56` as "6:02 AM today" and cancelled the reservation.

**Wiki article fetched:** cancelling-a-flight-reservation.md ✓

**Relevant wiki info (cancelling-a-flight-reservation.md):**
- "NEVER assume the 24-hour cancellation window is satisfied by checking only the booking date — verify the exact booking timestamp."
- "NEVER call `cancel_reservation` in response to user confirmation or insistence when eligibility conditions have already been determined to be unmet."
- "A user saying 'yes, go ahead' does NOT satisfy the eligibility requirement — the agent must deny the cancellation regardless of user pressure."

**Would wiki have helped?** **Yes — it WAS fetched but IGNORED.** The agent read the cancellation wiki, initially applied it correctly, but then caved to user pressure and misread the timestamp (confusing May 2 with "today at 6:02 AM"). The wiki's anti-pressure rules were explicitly violated.

---

## Comparison: No-Policy vs Policy+Wiki

| Task | No-Policy Failures | Policy+Wiki Failures | Change |
|------|-------------------|---------------------|--------|
| 2    | 3/4 | 3/4 | Same |
| 8    | 2/4 | 0/4 | **Fixed** |
| 16   | 2/4 | 4/4 | **Worse** |
| 18   | — | 1/4 | New failure |
| 19   | 2/4 | 0/4 | **Fixed** |
| 22   | 3/4 | 2/4 | Improved |
| 24   | 4/4 | 4/4 | Same |
| 25   | 4/4 | 1/4 | **Much better** |
| 29   | 4/4 | 4/4 | Same |
| 30   | 1/4 | 1/4 | Same |
| 31   | 1/4 | 0/4 | **Fixed** |
| 32   | 1/4 | 3/4 | **Worse** |
| 35   | 4/4 | 4/4 | Same |
| 37   | 4/4 | 3/4 | Slightly better |
| 44   | 4/4 | 4/4 | Same |
| 48   | 4/4 | 4/4 | Same |

**Key observations:**
- Policy helped fix Tasks 8, 19, 31 (basic economy rules) and dramatically improved Task 25
- Tasks 16 and 32 got worse — possibly because the agent spent tokens on article retrieval and calculation rather than acting
- The persistent failures (29, 35, 37, 44, 48) share a common pattern: **the agent fetched the relevant wiki article but failed to apply its rules**

---

## Root Cause Categories

### 1. Wiki fetched and IGNORED (5 tasks: 29, 35-partial, 37, 44, 48) — 19/38 failures

The agent retrieved the correct article, had the relevant rule in context, but violated it anyway. This is the dominant failure mode in the policy+wiki setup.

Causes:
- **User pressure override** (48, 35): Agent reversed correct judgment when user pushed back
- **Timestamp/date misreading** (48): Confused `2024-05-02` with "today" 
- **Flown-flight check skipped** (37): Didn't compare flight dates to current time
- **Destination-change rule ignored** (29): Proceeded with modification despite rule violation
- **Cancel vs. upgrade confusion** (44): Cancelled when should have upgraded

### 2. Wrong article fetched or article not fetched (3 tasks: 2, 22, 35-partial) — 9/38 failures

Agent didn't retrieve the relevant wiki page before acting.

### 3. Reasoning/math errors (3 tasks: 16, 18, 32) — 8/38 failures

Correct knowledge available but agent made calculation errors or misapplied the procedure.

### 4. Incomplete search space (2 tasks: 24, 35-partial) — 8/38 failures

Agent didn't search all relevant options (missing SEA for West Coast, missing one-stop for second cheapest).

---

## Key Finding

**The wiki's "new information" (anti-patterns, verification rules, pressure resistance) is precisely what the agent most commonly violates even when it HAS the wiki in context.** The problem has shifted from "agent doesn't know the rule" to "agent doesn't enforce the rule under pressure or complex reasoning."

This suggests:
1. **Knowledge alone is insufficient** — the rules need stronger enforcement mechanisms (e.g., chain-of-thought verification steps, mandatory checklists before write operations)
2. **Article retrieval is a point of failure** — agents sometimes fetch the wrong article or fail to fetch at all before acting
3. **User pressure consistently overrides wiki rules** — Tasks 35 and 48 show the agent caving despite having read the anti-pressure rules
4. **Multi-step reasoning degrades compliance** — Tasks 32, 37, 44 involve multiple operations where the agent loses track of constraints mid-execution
