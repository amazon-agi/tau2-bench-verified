# Trimmed Wiki Analysis: Run 36 (gpt-4o, oracle, policy + trimmed wiki)

## Summary

| Metric | Run 34 (full wiki) | Run 36 (trimmed wiki) |
|--------|--------------------|-----------------------|
| Pass rate | 42/80 (52.5%) | 42/80 (52.5%) |
| Wiki used (success) | ~83% | ~84% |
| Wiki used (failure) | ~79% | ~81% |

**Conclusion:** Aggregate pass rate is identical. Trimming redistributed which tasks pass/fail but did not improve the headline number.

---

## Per-Task Comparison (failures out of 4 trials)

| Task | Run 34 (full) | Run 36 (trimmed) | Delta | Notes |
|------|---------------|------------------|-------|-------|
| 48 | 4 | 1 | **-3 (improved)** | Timestamp guardrail now concise & at top |
| 37 | 3 | 2 | -1 | |
| 2 | 3 | 2 | -1 | |
| 32 | 3 | 2 | -1 | |
| 16 | 4 | 3 | -1 | |
| 22 | 2 | 4 | **+2 (worsened)** | Agent stalls after reading articles |
| 8 | 0 | 2 | +2 | |
| 25 | 1 | 2 | +1 | |
| 26 | 0 | 1 | +1 | |
| 31 | 0 | 1 | +1 | |
| 24 | 4 | 4 | 0 | |
| 29 | 4 | 4 | 0 | |
| 30 | 4 | 4 | 0 | |
| 35 | 4 | 4 | 0 | Benchmark DOB data issue |
| 44 | 4 | 4 | 0 | |
| 18 | 2 | 2 | 0 | |

---

## Key Findings

### 1. Task 48 — Clear improvement from trimmed wiki

Task 48 involves a cancellation request where the user's reservation was booked <24h ago and is thus within the free cancellation window. The guardrail "NEVER cancel based on ticket purchase timestamp — only the 24h-since-booking window applies" is now the first line of the cancellation article.

- **3 successes:** Agent fetched the cancellation article, saw the timestamp rule immediately, and correctly refused.
- **1 failure:** Agent did NOT fetch the wiki article and caved to user pressure.

The trimmed format (guardrails-first, concise) made the critical rule more salient.

### 2. Task 35 — Agent behavior improved but benchmark data issue masks it

In the full-wiki run, the agent sometimes cancelled the reservation under user pressure. In the trimmed run:
- Agent correctly refused cancellation in ALL 4 trials (wiki guardrail worked).
- Agent correctly searched one-stop flights (wiki "search one-stop before giving up" rule worked).
- Agent found the correct flights (HAT069+HAT258) in 2/4 trials.

However, ALL 4 trials fail because the agent uses DOB 1981-05-26 (from the user's profile via `get_user_details`) while the evaluation criteria expect 1985-05-26. This appears to be a benchmark data inconsistency — the agent is doing the right thing.

### 3. Task 22 — Regression from trimming

In the full wiki run: 2/4 failures. In the trimmed run: 4/4 failures.

Pattern: Agent fetches 2-3 wiki articles but then stalls — it reads the rules but doesn't execute the required workflow. The trimmed articles removed procedural guidance (step-by-step instructions) that the agent apparently needed to complete the task. This suggests some agents benefit from explicit procedure over concise guardrails.

### 4. Task 29 — "Wiki read but ignored" persists

All 4 trials fail. The agent reads the modification article containing "destination must remain the same" but still attempts to change the destination from LGA to JFK using `update_reservation_flights`. This is the dominant failure pattern that trimming cannot fix — the issue is agent compliance, not information access.

---

## Wiki Usage Patterns

### How the agent uses the trimmed wiki

1. **Fetches 1-2 articles** per task (vs. sometimes 3-4 with the full wiki) — less browsing overhead.
2. **Guardrails-first format works:** When the agent reads the article, the NEVER rules are encountered first. Task 48 is proof this increases compliance.
3. **Missing procedures hurt some tasks:** Task 22 shows that for complex multi-step operations, concise guardrails alone are insufficient — the agent needs procedural scaffolding.

### When wiki contributes to success

| Pattern | Frequency | Example |
|---------|-----------|---------|
| Wiki guardrail prevents wrong action | High | Task 48: "NEVER cancel based on timestamp" |
| Wiki info enables correct action | Medium | Task 35: "search one-stop flights" |
| Wiki fetched but ignored | High (failures) | Task 29: reads "destination must remain same", ignores it |
| Wiki not fetched | Low (~16%) | Occasional failures where agent skips wiki entirely |

---

## Conclusions

1. **Trimming doesn't improve aggregate pass rate** but significantly improves specific tasks where guardrail salience was the bottleneck (Task 48: 4→1 failures).

2. **Trimming can hurt tasks requiring procedural guidance** — removing step-by-step instructions leaves some agents unable to execute complex workflows (Task 22: 2→4 failures).

3. **The dominant failure mode ("wiki read but ignored") is unchanged** — this is a model compliance issue that no wiki formatting can solve. ~50% of failures in both runs exhibit this pattern.

4. **Optimal wiki design is task-dependent:**
   - For compliance/refusal tasks → concise guardrails-first format works best
   - For complex multi-step tasks → procedural guidance is still needed

5. **Recommended hybrid approach:** Keep the trimmed guardrails-first structure but add a brief "Steps" section for procedurally complex articles (booking, multi-payment, cancel-and-rebook workflows). This could capture the gains from both formats.
