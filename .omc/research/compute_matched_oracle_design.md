# Compute-Matched Oracle Study: Experimental Design

**Status:** Draft Research Memo  
**Date:** 2026-04-01  
**Authors:** [TeamBench Team]  
**Purpose:** Resolve the compute confound in TeamBench by running oracle baselines matched on LLM call count to the full team pipeline.

---

## 1. The Confound

### 1.1 Current Setup

TeamBench compares five conditions on each task:

| Condition | Roles Active | LLM Calls (1 round) | LLM Calls (2 rounds) | Information Access |
|-----------|-------------|---------------------|----------------------|-------------------|
| **Oracle** | 1 agent, unrestricted | 1 | 1 | spec.md + workspace + all tools |
| **Restricted** | 1 agent, no spec | 1 | 1 | workspace + all tools (no spec.md) |
| **No Planner** | Executor + Evaluator | 2 | 4 | Executor: brief only; Evaluator: spec + workspace (read-only) |
| **No Evaluator** | Planner + Executor | 2 | 2 | Planner: spec (read-only); Executor: plan + workspace |
| **Full Team** | Planner + Executor + Evaluator | 3 | 5 | As above, all three roles |

The Oracle makes **1 LLM call** with full information. The Full Team makes **3-5 LLM calls** with partitioned information. Any performance difference between Oracle and Full Team conflates two distinct effects:

1. **Compute effect:** More LLM calls = more tokens generated = more opportunity to reason, plan, revise, and self-correct.
2. **Collaboration effect:** Information asymmetry forces structured decomposition (spec analysis -> implementation -> verification), which may surface requirements that a single agent overlooks even when given full access.

### 1.2 Why This Matters

The current data shows:

- **Mean Oracle score: 0.668** vs **Mean Full Team: 0.655** (Full Team is *lower* on average)
- **Mean No-Verify: 0.711** (the *best* condition overall)
- **No-Verify >= Full Team on 81.5% of tasks** (106/130)
- **Mean uplift is negative: -0.012**
- **16 catastrophic failures** where Full Team scores 0.0 but Oracle scores > 0.3

These numbers suggest the Evaluator actively *hurts* performance via false rejections. But we cannot determine whether the Planner's benefit (information relay) would survive if the Oracle were simply given more compute. Specifically:

- If Oracle-3pass (plan -> execute -> self-verify) matches Full Team, the entire "collaboration benefit" story collapses to "more compute helps."
- If Oracle-3pass exceeds Full Team, the collaboration pipeline is *worse than useless* -- the information partitioning and Evaluator false rejections destroy value that raw compute would have captured.
- If Oracle-3pass is still below Full Team on the positive-uplift subset, then information asymmetry provides a structural advantage that cannot be replicated by a single agent thinking longer.

### 1.3 Specific Confounds to Disentangle

1. **Token generation budget:** The Planner generates a plan (~500-2000 tokens). Does the Oracle benefit from generating a plan before implementing, even without forced role separation?
2. **Self-verification opportunity:** The Evaluator reads spec + workspace to verify. Does the Oracle benefit from a separate verification pass with the same prompt structure?
3. **Forced attention to spec:** The Planner *must* read spec.md because that is its only input. The Oracle reads spec.md but may skim it. Does structured forced attention help?
4. **Error correction loop:** In 2-round Full Team, the Evaluator's feedback drives round-2 fixes. Does self-critique achieve the same error correction?
5. **Majority voting / diversity:** Multiple independent attempts may succeed on different tasks. Is "best of 3" a stronger baseline than structured collaboration?

---

## 2. Proposed Conditions

### 2.1 Oracle-Reflect (1 LLM call, enhanced prompt)

**Call count:** 1  
**Purpose:** Test whether self-reflection in the prompt recovers the Planner's benefit without additional compute.

**Prompt structure:**
```
You have full access to the specification and workspace.
Before implementing ANY changes, you MUST:
1. Read spec.md completely
2. List ALL requirements explicitly (number them)
3. For each requirement, identify the specific files and changes needed
4. Flag any requirements that seem ambiguous or easy to miss
5. Only THEN begin implementation
6. After implementing, verify each numbered requirement is satisfied

[standard tools available]
```

**Input:** spec.md + workspace + all tools  
**Output:** Implementation in workspace  
**What it tests:** Whether the Oracle's failure to catch subtle requirements (e.g., CSRF in the demo task) is a prompt engineering problem vs. a structural decomposition problem.

### 2.2 Oracle-2Pass (2 LLM calls, sequential)

**Call count:** 2  
**Purpose:** Match the compute of the No-Evaluator condition (Planner + Executor).

**Call 1 -- Plan:**
```
You are a planning agent. Read spec.md and the workspace.
Produce a detailed execution plan that:
- Lists every requirement from the spec
- Identifies the specific files to modify
- Notes edge cases and subtle requirements
- Prioritizes by difficulty

Output your plan to plan.md.
You may NOT modify any workspace files other than plan.md.
```
**Input:** spec.md + workspace (read-only except plan.md)  
**Output:** plan.md

**Call 2 -- Execute:**
```
You are an implementation agent. Read plan.md and implement all changes.
Follow the plan precisely. If the plan is unclear, use your best judgment.
After implementing, run any available tests.
```
**Input:** plan.md + workspace + all tools  
**Output:** Modified workspace

**What it tests:** Whether the Oracle benefits from separating planning from execution *within a single agent*, without information asymmetry.

### 2.3 Oracle-3Pass (3 LLM calls, sequential)

**Call count:** 3  
**Purpose:** Match the compute of the Full Team (1 round). This is the **primary comparison condition**.

**Call 1 -- Plan:** Same as Oracle-2Pass Call 1.  
**Input:** spec.md + workspace (read-only except plan.md)  
**Output:** plan.md

**Call 2 -- Execute:** Same as Oracle-2Pass Call 2.  
**Input:** plan.md + workspace + all tools  
**Output:** Modified workspace

**Call 3 -- Self-Verify:**
```
You are a verification agent. You have access to spec.md and the workspace (read-only).
Check the implementation against EVERY requirement in spec.md.
For each requirement, state whether it is satisfied and provide evidence.
Write your assessment to attestation.json with the format:
{"verdict": "PASS"|"FAIL"|"PARTIAL", "score": 0.0-1.0, "missing": [...], "feedback": "..."}

If your verdict is PARTIAL or FAIL, write specific remediation steps.
You may NOT modify any workspace files other than attestation.json.
```
**Input:** spec.md + workspace (read-only except attestation.json)  
**Output:** attestation.json

**Scoring:** The task grader scores the workspace as-is (attestation.json is not used for scoring -- only for analysis of self-verification accuracy). This matches how the Full Team is scored: the grader evaluates the workspace after the Executor's last round.

**What it tests:** Whether a single agent's plan-execute-verify loop matches the Full Team's structurally enforced plan-execute-verify loop. If Oracle-3Pass ~= Full Team, the benefit is compute, not collaboration.

### 2.4 Oracle-3Pass-Feedback (5 LLM calls, 2 rounds)

**Call count:** 5  
**Purpose:** Match the compute of the Full Team (2 rounds).

**Round 1:** Oracle-3Pass (3 calls) as above.  
**Round 2:**
- **Call 4 -- Fix:** Agent reads attestation.json + workspace, implements fixes. Same tools as Call 2.
- **Call 5 -- Re-Verify:** Same as Call 3, produces updated attestation.json.

**What it tests:** Whether self-feedback loops (reading your own attestation and fixing) are as effective as the Evaluator-to-Executor feedback loop in the Full Team. This directly tests whether the Evaluator's value comes from being a *different agent* or merely from being a *separate verification pass*.

### 2.5 Oracle-BestOf3 (3 LLM calls, independent)

**Call count:** 3  
**Purpose:** Test whether diversity across independent attempts outperforms structured collaboration.

**Attempt 1, 2, 3:** Each is a standard Oracle call (1 LLM call, full access, identical prompt). Run independently with different random seeds (temperature > 0).

**Scoring:** Take the **maximum** score across the 3 attempts. This is the most generous interpretation of what 3x compute buys.

**What it tests:** Whether the Full Team's benefit (where it exists) comes from structured decomposition or simply from having multiple chances to get the right answer. If BestOf3 >= Full Team, the collaboration adds no value beyond sampling diversity.

### 2.6 Oracle-BestOf3-Majority (3 LLM calls, independent)

**Call count:** 3  
**Purpose:** More realistic version of BestOf3 -- you don't always know which attempt is best.

**Scoring:** Take the **median** score across the 3 attempts (or use majority vote for binary pass/fail).

**What it tests:** Whether the Full Team's structured approach yields more consistent results than independent sampling.

### Summary of Conditions

| Condition | LLM Calls | Information | Sequential? | Key Question |
|-----------|-----------|-------------|-------------|--------------|
| Oracle (existing) | 1 | Full | - | Baseline |
| Oracle-Reflect | 1 | Full | - | Is it a prompt problem? |
| Oracle-2Pass | 2 | Full | Yes | Does forced planning help? |
| Oracle-3Pass | **3** | Full | Yes | **Is it compute or collaboration?** |
| Oracle-3Pass-Feedback | 5 | Full | Yes | Does self-feedback match team feedback? |
| Oracle-BestOf3 | 3 | Full | No | Is diversity enough? |
| Oracle-BestOf3-Majority | 3 | Full | No | Is diversity reliable? |
| Full Team (existing) | 3/5 | Partitioned | Yes | Collaboration reference |

---

## 3. Hypotheses and Interpretation Matrix

### 3.1 Primary Hypothesis (Oracle-3Pass vs Full Team)

| Result | Interpretation | Implication for TeamBench |
|--------|---------------|--------------------------|
| **Oracle-3Pass >= Full Team** | Collaboration adds no value beyond compute. Structurally enforced roles are unnecessary; a single agent with a plan-execute-verify prompt chain performs equivalently. | TeamBench measures compute scaling, not collaboration. The benchmark needs redesign or reframing. |
| **Oracle-3Pass < Full Team** (on positive-uplift tasks) | Information asymmetry provides structural benefit. Forcing the Planner to *only* see the spec (and nothing else) produces better plans than a full-access agent's self-planning. | TeamBench's core claim is validated. The forced attention mechanism is real. |
| **Oracle-3Pass > Full Team** (overall) | The collaboration pipeline is actively harmful. The Evaluator's false rejections and the information partitioning overhead destroy more value than collaboration creates. Oracle-3Pass captures the compute benefit without the collaboration cost. | The current Full Team pipeline needs fixing. The Evaluator is the bottleneck, not the collaboration structure. |

### 3.2 Secondary Hypotheses

| Comparison | If A >= B | If A < B |
|------------|-----------|----------|
| **Oracle-Reflect vs Oracle** | Self-reflection prompt helps; the Oracle's failure was partially a prompt problem. | The Oracle's failures are structural, not prompt-related. Forced attention requires forced role separation. |
| **Oracle-2Pass vs Oracle** | Separating planning from execution helps even within one agent. The Planner's value is the *act of planning*, not the information asymmetry. | Planning within one agent doesn't help. The benefit requires that planning happens in a context *without* implementation tools (forced constraint). |
| **Oracle-2Pass vs No-Evaluator** | A single agent's 2-pass is as good as Planner + Executor. The Planner's benefit is entirely from the planning step, not from being a separate entity. | The Planner as a separate agent adds value beyond just "planning first." |
| **Oracle-BestOf3 vs Full Team** | Sampling diversity is more valuable than structured collaboration. | Structured collaboration produces value that cannot be replicated by independent sampling. |
| **Oracle-3Pass-Feedback vs Full Team (2-round)** | Self-feedback is as effective as cross-agent feedback. | Cross-agent verification catches errors that self-verification misses (blind-spot hypothesis). |
| **Oracle-BestOf3 vs Oracle-3Pass** | Independent diversity beats structured sequential processing. | Structured reasoning (plan then execute then verify) is more effective than raw diversity. |

### 3.3 The Null Result Problem

If **all** compute-matched conditions perform similarly to Oracle (within noise), the conclusion is:
- Extra compute doesn't help for these tasks.
- Neither collaboration nor more thinking improves performance.
- The tasks may have a "capability ceiling" -- either the model can solve them in one pass or it cannot.

This would be an important negative result: it would suggest that current multi-agent frameworks are performing elaborate rituals that amount to nothing more than a single well-prompted agent.

---

## 4. Task Selection

### 4.1 Current Dataset Summary (130 tasks in task_results.json)

| Subset | Count | Description |
|--------|-------|-------------|
| Positive uplift (Full > Oracle) | 55 | Tasks where collaboration currently helps |
| Negative uplift (Full < Oracle) | 25 | Tasks where collaboration currently hurts |
| Zero uplift | 50 | Tasks where collaboration makes no difference |
| Catastrophic (Full = 0, Oracle > 0.3) | 16 | Tasks where the pipeline completely fails |

### 4.2 Recommended Task Selection: Stratified Sample of 60

Running all 7 new conditions on all 130 tasks requires 130 x 7 x ~3 = ~2,730 LLM calls (expensive). A stratified sample balances statistical power with cost.

**Stratum 1: Positive Uplift (n=25)**  
Randomly sample 25 of the 55 positive-uplift tasks. These are where collaboration currently helps -- the key question is whether compute-matched baselines eliminate the advantage.

**Stratum 2: Negative Uplift (n=15)**  
All 25 negative-uplift tasks are important, but sample 15 for cost. These test whether compute-matched baselines *also* fail (suggesting inherent task difficulty) or succeed (confirming the pipeline hurts).

**Stratum 3: Catastrophic Failures (n=10)**  
Sample 10 of the 16 catastrophic failures. These are the most informative: if Oracle-3Pass still scores >0.3 while Full Team scores 0.0, the Evaluator false-rejection problem is confirmed independently of compute.

**Stratum 4: Zero Uplift with High Oracle (n=10)**  
Sample 10 tasks where uplift = 0 and Oracle > 0.7. These test whether ceiling effects mask a compute benefit.

**Total: 60 tasks x 7 conditions = 420 runs.**

### 4.3 Alternative: Use TeamBench-Mini (28 tasks)

The existing Mini-28 subset is already balanced across categories. Running 7 conditions x 28 tasks = 196 runs is cheaper but may lack statistical power. The advantage is direct comparability with the existing leaderboard.

**Recommendation:** Run on Mini-28 first as a pilot (196 runs). If results are promising/surprising, extend to the full stratified-60 (420 runs).

### 4.4 Power Analysis

Key parameters:
- **Effect size of interest:** 0.05 in mean score (a meaningful practical difference on [0,1] scale)
- **Standard deviation of uplift:** 0.33 (observed from current data)
- **Paired design:** Each task serves as its own control (Oracle-3Pass score vs Full Team score for the same task)
- **Within-task SD of score difference:** Estimated ~0.20 (lower than cross-task SD due to pairing)

For a two-sided paired t-test at alpha = 0.05, power = 0.80:

| Effect size (d) | Required N |
|-----------------|------------|
| 0.05 | ~128 (need full dataset) |
| 0.08 | ~50 |
| 0.10 | ~32 |
| 0.15 | ~15 |

With 60 tasks (stratified), we can detect an effect of ~0.08 (8 percentage points). With Mini-28, we can detect ~0.12. Given the observed mean uplift is only -0.012, detecting small effects requires the full sample.

**Recommendation:** Minimum N = 60 for the primary comparison (Oracle-3Pass vs Full Team). The Mini-28 pilot can detect only large effects (>12 points).

---

## 5. Statistical Analysis Plan

### 5.1 Primary Outcome

**Metric:** Partial score in [0, 1] per task per condition.

**Primary comparison:** Oracle-3Pass vs Full Team, paired by task.

### 5.2 Tests

| Analysis | Test | Justification |
|----------|------|---------------|
| Primary: Oracle-3Pass vs Full Team | Wilcoxon signed-rank test | Scores are bounded [0,1], likely non-normal; paired design |
| Sensitivity: same comparison | Paired bootstrap CI (10,000 resamples) | Non-parametric, provides CI directly |
| Secondary: pairwise condition comparisons | Wilcoxon signed-rank with Holm-Bonferroni correction | 6 new conditions compared to Full Team = 6 comparisons |
| Pass/fail: binary version | McNemar's test | Paired binary data |
| Subgroup: by oracle quintile | Stratified Wilcoxon | Test whether the effect differs by task difficulty |

### 5.3 Multiple Comparisons

Seven conditions compared to Full Team = 7 primary tests (including the existing Oracle).

**Correction:** Holm-Bonferroni (step-down procedure). This is less conservative than Bonferroni while still controlling the familywise error rate at 0.05.

**Pre-registered primary comparison:** Oracle-3Pass vs Full Team (alpha = 0.05, no correction needed for a single pre-registered test). All other comparisons are exploratory and corrected.

### 5.4 Effect Size

**Primary effect size:** Mean paired difference (Oracle-3Pass score minus Full Team score) with 95% bootstrap CI.

**Minimum meaningful difference:** 0.05 (5 percentage points). Anything smaller is practically insignificant even if statistically significant.

**Cohen's d equivalent:** Using within-pair SD of ~0.20, d = 0.05/0.20 = 0.25 (small effect).

### 5.5 Handling Partial Scores vs Binary

Run all analyses twice:
1. **Partial scores** (primary): Uses the full [0,1] grader output. More sensitive.
2. **Binary pass/fail** (secondary): score >= threshold (e.g., 0.9) counts as pass. More interpretable, matches leaderboard pass rates.

Report both. If they disagree, partial scores take precedence (more information).

### 5.6 Reporting

For each comparison, report:
- Mean score per condition
- Mean paired difference with 95% bootstrap CI
- Wilcoxon signed-rank p-value (two-sided)
- Effect size (Cohen's d for paired data)
- Number of tasks where condition A > B, A = B, A < B

---

## 6. Expected Timeline and Cost Estimate

### 6.1 Model Calls

**Test model:** Claude Sonnet 4.6 (consistent with existing evaluations).

| Phase | Tasks | Conditions | Calls/Condition | Total Calls |
|-------|-------|-----------|-----------------|-------------|
| Pilot (Mini-28) | 28 | 7 new | avg 2.7 | ~530 |
| Full (Stratified-60) | 60 | 7 new | avg 2.7 | ~1,130 |
| **Total** | | | | **~1,660** |

Breakdown of calls per condition per task:
- Oracle-Reflect: 1
- Oracle-2Pass: 2
- Oracle-3Pass: 3
- Oracle-3Pass-Feedback: 5
- Oracle-BestOf3: 3
- Oracle-BestOf3-Majority: 3 (same runs, different scoring)

BestOf3 and BestOf3-Majority share the same 3 runs (different aggregation), so actual unique calls per task across all conditions: 1 + 2 + 3 + 5 + 3 = **14 calls/task** (not 17, since BestOf3-Majority reuses BestOf3 runs).

Revised totals:
- Pilot: 28 x 14 = **392 calls**
- Full: 60 x 14 = **840 calls**
- **Grand total: 1,232 unique LLM calls**

### 6.2 Cost Estimate

Assuming Claude Sonnet 4.6 pricing (~$3/M input tokens, ~$15/M output tokens):
- Average input context per call: ~8,000 tokens (spec + workspace + plan/attestation)
- Average output per call: ~4,000 tokens (plan, code edits, verification)
- Cost per call: ~$0.024 input + ~$0.060 output = ~$0.084

| Phase | Calls | Estimated Cost |
|-------|-------|---------------|
| Pilot (Mini-28) | 392 | ~$33 |
| Full (Stratified-60) | 840 | ~$71 |
| **Total** | 1,232 | **~$104** |

This is very affordable. The primary constraint is wall-clock time, not cost.

### 6.3 Execution Time

Each task takes ~2-5 minutes (Docker container startup + LLM calls + grading).
- Sequential: 1,232 calls x ~3 min = ~62 hours
- With 8x parallelism: **~8 hours**
- With 16x parallelism: **~4 hours**

### 6.4 Minimum Viable Version

If budget or time is constrained, run **only Oracle-3Pass on Mini-28**:
- 28 tasks x 3 calls = **84 LLM calls**
- Cost: **~$7**
- Time: **~1 hour** (sequential)
- Provides the single most important comparison: is the Full Team benefit compute or collaboration?

---

## 7. The Finding That Would Change the Field

### 7.1 What the Data Already Tells Us

The current data contains an uncomfortable truth that the website presentation somewhat obscures:

- **Mean uplift is negative (-0.012).** The Full Team is, on average, *worse* than the Oracle.
- **No-Verify is the best condition** (mean 0.711 vs Full Team 0.655 vs Oracle 0.668).
- **The Evaluator is catastrophically harmful** on 16 tasks (Full Team = 0.0, Oracle > 0.3).
- **81.5% of tasks** have No-Verify >= Full Team.

The website highlights the "Equalizer Effect" (+32.1% for the weakest model) and "Hardest Tasks Benefit Most" (+15.3% on Q1), which are real but mask the overall story. The collaboration benefit is concentrated in a specific corner of the design space: weak models on hard tasks. For the majority of the evaluation surface, collaboration hurts.

### 7.2 My Prediction

Based on the data patterns, I predict:

1. **Oracle-Reflect will slightly improve over Oracle** (by ~2-3%). The Oracle's failures are partly inattention (skimming spec.md), and a forced-reflection prompt will catch some missed requirements. This is the least interesting result.

2. **Oracle-2Pass will roughly match No-Evaluator** (which already averages 0.711). Separating planning from execution helps, and a single agent's self-plan is comparable to the Planner agent's plan -- perhaps better, since the Oracle-2Pass planner also sees the workspace.

3. **Oracle-3Pass will exceed Full Team on average.** The single agent with plan-execute-verify will outperform the Full Team because:
   - The self-verifier has full context (saw the plan, knows what was intended)
   - No information loss from the relay chain
   - No false rejections from a separately-prompted Evaluator
   - Expected mean: ~0.70, vs Full Team 0.655

4. **Oracle-BestOf3 (max) will be the overall best condition.** Independent sampling with best-of selection is a powerful strategy that structured collaboration cannot beat on heterogeneous tasks.

5. **On the Q1 (hardest) tasks only, Full Team may still match or beat Oracle-3Pass.** The information asymmetry may matter most when tasks are hard enough that a single agent genuinely misses requirements even with 3 passes. This would be a nuanced and publishable finding.

### 7.3 Scenario: Results That Would Change the Field

**Scenario A: Oracle-3Pass >= Full Team across the board (including Q1 tasks)**

This is the "multi-agent collaboration is theater" result. It would demonstrate that the entire ecosystem of Planner-Executor-Verifier frameworks (AutoGen, CrewAI, MetaGPT, etc.) is performing an expensive ritual that a single agent with a structured prompt chain can replicate. The implication: invest in better prompt engineering and inference-time compute scaling, not agent collaboration frameworks.

**Why it's field-changing:** It directly challenges the narrative driving hundreds of millions in multi-agent startup funding. A rigorous, compute-matched comparison in a structurally-enforced benchmark (not prompt-based) would be extremely hard to dismiss.

**Scenario B: Oracle-3Pass < Full Team, but only on Q1 tasks with large spec-workspace divergence**

This is the "collaboration helps, but only when information is genuinely hard to extract" result. It would identify the precise conditions under which role separation adds value: tasks where the specification contains critical requirements that are not obvious from the codebase, AND the task is hard enough that a single agent fails to catch them even with 3 passes.

**Why it's field-changing:** It provides the first empirical characterization of *when* multi-agent collaboration is warranted. Every framework paper claims collaboration helps; none can say precisely when. This result would give practitioners a decision function: use multi-agent only when [spec complexity > X] AND [task difficulty > Y].

**Scenario C: Oracle-BestOf3 > Full Team > Oracle-3Pass**

This would mean structured collaboration beats sequential self-prompting (validating some collaboration value), but independent sampling beats both (suggesting the value is diversity, not structure). The implication: the optimal multi-agent strategy is embarrassingly parallel independent attempts, not structured role decomposition.

**Why it's field-changing:** It would redirect the field from designing elaborate agent topologies toward simple ensemble/sampling strategies. Majority voting over independent attempts is trivially parallelizable and scales linearly with compute.

### 7.4 Regardless of Direction

Any clean result from a compute-matched study would be valuable because:

1. **No existing multi-agent benchmark controls for compute.** Every comparison in the literature (AutoGen, CrewAI, MetaGPT, ChatDev) compares N agents making N calls against 1 agent making 1 call. This is the first clean ablation.

2. **The structural enforcement makes results credible.** Unlike prompt-based role assignment (which agents can and do ignore), TeamBench's container isolation ensures roles are actually enforced. Compute-matched comparisons in this setting are trustworthy.

3. **The partial scoring gives sensitivity.** Binary pass/fail would require enormous N. The [0,1] grader makes it feasible to detect meaningful differences with 60 tasks.

---

## 8. Implementation Checklist

### Phase 1: Infrastructure (1-2 days)

- [ ] Implement Oracle-Reflect prompt template
- [ ] Implement Oracle-2Pass runner (plan call -> execute call, shared workspace)
- [ ] Implement Oracle-3Pass runner (plan -> execute -> verify, shared workspace)
- [ ] Implement Oracle-3Pass-Feedback runner (3Pass + fix + re-verify)
- [ ] Implement Oracle-BestOf3 runner (3 independent Oracle calls, track all scores)
- [ ] Verify that plan.md and attestation.json are written/read correctly between calls
- [ ] Verify that workspace state is preserved between sequential calls
- [ ] Verify that workspace state is reset between independent BestOf3 calls

### Phase 2: Pilot on Mini-28 (1 day)

- [ ] Run all 7 new conditions on Mini-28 (392 calls)
- [ ] Score all runs with existing graders
- [ ] Compute summary statistics and check for implementation bugs
- [ ] Verify that Oracle-Reflect and Oracle (existing) produce different results (sanity check)
- [ ] Verify that Oracle-BestOf3 individual runs produce varied results (temperature > 0)

### Phase 3: Full Study on Stratified-60 (2-3 days)

- [ ] Select stratified sample (25 positive + 15 negative + 10 catastrophic + 10 high-oracle-zero-uplift)
- [ ] Run all 7 conditions on all 60 tasks (840 calls)
- [ ] Run analysis pipeline (see Section 5)
- [ ] Generate figures: paired difference plots, condition-by-quintile heatmaps, scatter plots

### Phase 4: Write-up (2-3 days)

- [ ] Draft results section for paper appendix or standalone report
- [ ] Create compute-matched comparison table for website
- [ ] Update FAQ ("Is the oracle baseline fairly optimized?") with empirical evidence
- [ ] If results warrant, draft a short paper or technical report

### Total: ~7-9 days from start to report.

---

## 9. Appendix: Exact Prompt Templates

### A. Oracle-Reflect System Prompt Addition

```
IMPORTANT: Before writing ANY code, you must complete these steps:

STEP 1 - REQUIREMENTS ANALYSIS:
Read spec.md from start to finish. List every requirement as a numbered item.
Do not skip any section. Pay special attention to:
- Requirements buried in subsections
- Implicit requirements (e.g., "must not introduce regressions")
- Edge cases mentioned in examples
- Non-functional requirements (performance, security, etc.)

STEP 2 - COVERAGE PLAN:
For each numbered requirement, write:
- Which file(s) need modification
- What the change is
- How you will verify it

STEP 3 - RISK CHECK:
Review your plan. Are there any requirements you might be tempted to
skip as "out of scope" or "handled elsewhere"? If so, they are probably
in scope. Implement them.

STEP 4 - IMPLEMENT:
Now implement all changes following your plan.

STEP 5 - SELF-CHECK:
Go back to your numbered requirements list. For each one, verify the
implementation satisfies it. If any requirement is unsatisfied, fix it
before declaring done.
```

### B. Oracle-2Pass and Oracle-3Pass Plan Call Prompt

```
You are a planning agent for a software engineering task.

Your job is to analyze the specification and workspace, then produce a
detailed execution plan. You may read any file but may only write to plan.md.

Requirements for your plan:
1. List EVERY requirement from spec.md (numbered, with section references)
2. For each requirement, specify the exact file(s) and change(s) needed
3. Flag subtle or easily-missed requirements with [IMPORTANT]
4. Note any ambiguities or potential conflicts
5. Order tasks by dependency (what must be done first)

Write your complete plan to plan.md.
```

### C. Oracle-3Pass Verify Call Prompt

```
You are a verification agent. Your job is to check whether the
implementation satisfies all requirements in spec.md.

You have read-only access to the workspace and spec.md.
You may only write to attestation.json.

For each requirement in spec.md:
1. State the requirement
2. Check whether it is implemented (cite specific code/files)
3. Verdict: PASS / FAIL / PARTIAL

Write attestation.json:
{
  "verdict": "PASS" | "FAIL" | "PARTIAL",
  "requirements_checked": N,
  "requirements_passed": M,
  "score": M/N,
  "missing": ["requirement X - description", ...],
  "feedback": "Specific remediation steps for missing requirements"
}
```

---

## 10. Pre-Registration Statement

To prevent post-hoc rationalization, this study should be pre-registered before running. The key commitments:

1. **Primary hypothesis:** Oracle-3Pass vs Full Team, Wilcoxon signed-rank, alpha = 0.05.
2. **Direction:** Two-sided (we do not pre-commit to a direction).
3. **Minimum N:** 60 tasks (stratified sample as described).
4. **Analysis will be reported regardless of outcome.** Null results are publishable.
5. **Subgroup analyses** (by quintile, by category) are pre-specified as exploratory.
6. **No cherry-picking conditions.** All 7 conditions will be reported.

---

*This document is a research design memo. It should be reviewed by the team before execution begins. The most important output is a clean answer to: "Does the Full Team outperform a compute-matched single agent?" The answer, whatever it is, will be valuable.*
