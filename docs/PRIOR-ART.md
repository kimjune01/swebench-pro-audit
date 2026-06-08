# Prior art & novelty

Survey by codex/gpt-5.5 (live web search; raw output in `prior-art-survey-codex-raw.txt`), with the
load-bearing citations **independently re-verified** by web search. Confidence is flagged per item.

## Verified-real citations

**Contamination / leakage / freshness (mostly about Verified)**
- Jimenez, Yang, Wettig, Yao, Pei, Press, Narasimhan. *SWE-bench: Can Language Models Resolve Real-World
  GitHub Issues?* ICLR 2024. The base benchmark; public issue/PR construction is the contamination surface.
- Aleithan et al. *SWE-Bench+: Enhanced Coding Benchmark for LLMs.* arXiv:2410.06992, Oct 2024.
  **Verified.** Manual audit: **32.67% solution leakage**, 31% weak tests; filtering drops SWE-agent+GPT-4
  12.47% → 3.97%.
- Badertdinov et al. *SWE-rebench.* arXiv:2505.20411, 2025. Decontaminated, fresh-task pipeline. *(cited as
  real; ID not independently re-verified here.)*
- Zhang et al. *SWE-bench Goes Live!* arXiv:2505.23419, 2025. Live post-2024 issue benchmark. *(not re-verified.)*
- OpenAI. *Why SWE-bench Verified no longer measures frontier coding capabilities.* Feb 2026.
  **Verified.** Audited ~27.6% of Verified → **59.4% of audited tasks have flawed tests** rejecting
  functionally-correct submissions; frontier models reproduce **exact gold patches** (contamination).
  Stops reporting Verified, **recommends Pro**.

**Construct validity / test-as-oracle (about SWE-bench / Verified)**
- Wang, Pradel, Liu. *Are "Solved Issues" in SWE-bench Really Solved Correctly? An Empirical Study.*
  arXiv:2503.15223, ICSE 2026. **Verified.** PatchDiff differential testing: plausible patches pass the
  tests yet diverge from developer intent.
- Garg, Steenhoek, Huang. *Saving SWE-Bench: A Benchmark Mutation Approach.* MSR, arXiv, Oct 2025.
  *(cited as real; not independently re-verified.)*
- Wang, Bianchi, Zhu et al. *Automated Benchmark Auditing for AI Agents and LLMs.* arXiv:2605.26079,
  May 2026. **UNVERIFIED — treat as uncertain until checked.**

**Scaffold vs model attribution**
- Yang, Jimenez, Wettig et al. *SWE-agent: Agent-Computer Interfaces…* NeurIPS 2024. Scaffold design
  materially moves SWE-bench scores.
- Fan, Vasilevski, Lin et al. *SWE-Effi: Re-Evaluating Software AI Agent System Effectiveness…*
  arXiv:2509.09853, Sept 2025. Effectiveness = scaffold-model *synergy*, not scaffold or model alone.

**SWE-bench Pro specifically**
- Deng, Da, Pan et al. (Scale AI). *SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering
  Tasks?* arXiv:2509.16941, Sept 2025. **Verified** (authors confirmed). The benchmark itself + its
  rationale; long-horizon, multi-file, human-augmented. **Not an external audit.**
- Datacurve. *DeepSWE* blog, 2026. The only Pro-specific external critique found (verifier false
  pos/neg via an LLM analyzer). **Non-peer-reviewed; the author sells a competing benchmark.** (Note:
  this is the bench [we have separately audited](https://github.com/kimjune01/swebench-pro).)

## The split that matters

OpenAI debunked **Verified**, not Pro — and recommends Pro as the cure. So:

| claim | Verified | **Pro** |
|---|---|---|
| contamination / recall | established & official (OpenAI, Aleithan) | claimed-*resistant*; our gold-overlap ~2% (frontier) supports it |
| test over-determination / underdetermined prose | established (OpenAI, Wang/Pradel/Liu) | **thinly examined** (only Datacurve's verifier audit) |
| **oracle-gated iteration is the lift, not reasoning** | nobody | **nobody** |

## Novelty verdict

- **A — oracle-free causal ablation** (diagnosis ~0; cross-model ~0; self-audit false-green; the lift is
  the oracle gate, not reasoning): **appears novel.** Prior art shows tests *misgrade*; none shows the
  *success mechanism is search-against-the-oracle, not understanding.*
- **B — losses are downstream of solved localization** (recall 1.0 → still loses; residual is a
  test-hidden behavioral detail): **precise form appears novel**; the broader underdetermined-prose /
  over-determined-test *framing* is already known (for Verified).
- **Defensible frame:** not "Pro is flawed," but **"on the bench OpenAI now trusts, oracle-gated
  iteration — not diagnosis/localization — explains the above-baseline lift, on an axis no prior audit
  examined."** Needs no contamination claim to stand.

## Do not overclaim

- Don't restate the Verified flaw-catalogue as discovery. Auditing **Pro's** construct validity is the
  open part; the contamination angle is Verified's and does not transfer to Pro.
- Re-verify the two UNVERIFIED items before citing.
