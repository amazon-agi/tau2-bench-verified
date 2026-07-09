# All-in-System-Prompt Analysis: Run 37 (gpt-4o, oracle, merged policy with guardrails)

## Summary

| Run | Configuration | Pass rate |
|-----|--------------|-----------|
| 34 | policy + full wiki (tools) | 42/80 (52.5%) |
| 36 | policy + trimmed wiki (tools) | 42/80 (52.5%) |
| **37** | **merged policy (no wiki tools)** | **43/79 (54.4%)** |

Small improvement (+1.9pp) but one trial is missing so not definitive. The real story is in the per-task shifts.

---

## Per-Task Comparison

| Task | R34 (wiki) | R36 (trimmed) | R37 (sysprompt) | Delta vs R36 |
|------|-----------|---------------|-----------------|--------------|
| 32 | 3 | 2 | **0** | -2 improved |
| 24 | 4 | 4 | 3 | -1 improved |
| 26 | 0 | 1 | 0 | -1 improved |
| 31 | 0 | 1 | 0 | -1 improved |
| 37 | 3 | 2 | **4** | +2 worsened |
| 18 | 1 | 1 | 2 | +1 worsened |
| 48 | 4 | 1 | 1 | 0 (maintained) |
| 29 | 4 | 4 | 4 | 0 (stuck) |
| 35 | 4 | 4 | 4 | 0 (stuck) |
| 22 | 2 | 4 | 4 | 0 (stuck) |
| 44 | 4 | 4 | 4 | 0 (stuck) |

---

## Key Findings

### What improved

**Task 32 (2→0 failures):** Perfect score. This is a flight modification task. With guardrails embedded in the system prompt (persistent, authoritative), the agent correctly follows modification rules in all 4 trials. No wiki lookup overhead = more focused execution.

**Tasks 26, 31 (1→0 failures):** Eliminated stochastic single-trial failures. These were likely cases where wiki tool calls added noise or distracted the agent.

### What worsened

**Task 37 (2→4 failures):** Multi-operation task (cancel 2 reservations + upgrade 1). The agent fails because it picks the wrong payment card.

Root cause analysis:
- User says "use my credit card ending in 7334"
- Agent needs to call `get_user_details` to map "ending in 7334" to the actual `credit_card_id`
- In R36, the wiki consultation flow (list_articles → get_article) implicitly triggered `get_user_details` as part of the lookup procedure
- In R37, without that wiki-driven procedural nudge, the agent skips the lookup and guesses the wrong card ID
- Additionally: agent incorrectly cancels NQNU5R (already-flown business flight) in some trials

This is a **lost procedural guidance** regression — the merged policy says "payment methods must be in profile" but doesn't explicitly say "look up the profile to resolve a user's card description to its system ID."

### Persistent failures (unchanged)

- **Task 29:** Agent still changes destination despite "origin/destination cannot change" being in the guardrails section. Same-city rationalization (LGA≈JFK) persists.
- **Task 35:** Benchmark DOB data inconsistency (profile=1981, expected=1985).
- **Task 44, 22:** Complex multi-step tasks where the agent struggles regardless of policy format.

---

## Did the fix address "Recency Bias" and "Not Authoritative"?

### Recency bias: PARTIALLY FIXED
- Task 48 (timestamp guardrail) stays at 1 failure — the guardrail remains effective in the system prompt
- Task 32 improved to 0 failures — consistent compliance when rules are always visible
- Task 29 UNCHANGED — proves that for certain rationalized violations, proximity alone doesn't help

### Authority: PARTIALLY FIXED  
- Overall pass rate slightly improved
- Fewer stochastic single-trial failures (Tasks 26, 31, 32)
- But Task 37 shows that removing wiki tools loses procedural scaffolding the agent relied on

---

## The tradeoff

| Approach | Strengths | Weaknesses |
|----------|-----------|------------|
| Wiki tools | Procedural guidance, step-by-step scaffolding | Recency decay, not authoritative, adds tool-call overhead |
| All-in-policy | Always visible, authoritative, no lookup latency | Cannot provide procedural scaffolding without bloating system prompt |

---

## Recommendation: Hybrid v2

The optimal approach combines both:

1. **Guardrails in system prompt** (keep from R37) — proven to work for compliance tasks
2. **Add one missing procedural rule to the policy:**
   > "When the user references a payment method by partial description (e.g., 'card ending in 7334'), always call `get_user_details` to resolve the exact payment ID before proceeding."
3. **Add clarification for same-city airports:**
   > "Same-city airports (JFK, LGA, EWR) are DIFFERENT destinations. Changing between them is a destination change and is NOT permitted."
4. **Optionally keep wiki tools for complex multi-step procedures** (booking, cancel-and-rebook) where step-by-step guidance helps execution — but mark them as supplementary, not primary policy source.
