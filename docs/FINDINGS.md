# Findings (data behind the README claims)

All runs oracle-free (held-out tests withheld from the agent), official-graded after. Implementer =
codex/gpt-5.5 throughout. Pre-selected existence cases; single rollout per arm. These demonstrate a
mechanism; they do not estimate a rate.

## 1. Diagnosis is inert (oracle-free), same-model

recon→craft (codex prose diagnosis → codex craft) vs craft-only, 6 existence cases. Both arms = codex,
so contamination is a constant and the **delta** is clean. `data/oracle_free_codex/`.

| instance | craft_only | recon_craft |
|---|---|---|
| ansible | ✓ | ✓ |
| NodeBB | ✓ | ✓ |
| qutebrowser | ✗ | ✗ |
| protonmail | ✗ | ✗ |
| tutao | ✗ | ✗ |
| element | ✗ | ✗ |

**0/6 discordant.** The handoff changes nothing.

## 2. Cross-model diagnosis is inert, on the 4 losses

Opus-4.8 diagnosis → codex craft. `data/oracle_free_opus/`.

| instance | craft_only | recon_craft (Opus handoff) |
|---|---|---|
| qutebrowser | ✗ | ✗ |
| protonmail | ✓ | ✗ |
| tutao | ✗ | ✗ |
| element | ✗ | ✗ |

recon_craft **0/4**. The lone discordant cell (protonmail) is anti-thesis and is craft Pass@1 variance:
protonmail's craft-only was ✗ in run 1 and ✓ here, same blind arm. **Blind-craft variance > diagnosis effect.**

## 3. Self-authored audit loop is false-green

codex craft → codex writes+runs a reproduction from the prose → revise, oracle-free. `data/self_audit/`.

| instance | self-verdict | official |
|---|---|---|
| qutebrowser | AUDIT GREEN | ✗ |
| protonmail | AUDIT GREEN | ✗ |
| tutao | AUDIT GREEN | ✗ |
| element | AUDIT GREEN | ✗ |

**4/4 self-declared fixed; 0/4 actually resolved.** A self-built check is not just inert — trusting it
ships broken fixes believing them correct.

## 4. Diagnosis localizes well; losses are downstream

Diagnosis recall/precision vs the gold patch (`tools/diag_oracle.py`, deterministic, no LLM judge),
codex recon, on the 4 losses:

| instance | recall | precision | gold shape |
|---|---|---|---|
| qutebrowser | **1.00 (8/8)** | 0.62 | 8 regions, one file |
| element | 0.64 (7/11) | 0.996 | 11 regions |
| tutao | 0.44 (4/9) | 0.58 | 9 regions |
| protonmail | 0.44 (17/39) | 0.72 | **39 regions, 11 files** |

Precision is high → not wrong bugs. Recall tracks **fix-breadth**: protonmail's gold is a 4-concern
Redux-elements overhaul across 11 files — a feature mislabeled as a bug — which the prose cannot
determine. "Low recall" there is task underspecification, not a narrow inquiry.

## 5. Craft autopsy: perfect localization, still lost (`qutebrowser-e34dfc68`)

`data/craft_autopsy/` — craft's patch, the grade, per-test results.

- Diagnosis recall **1.0** (named all 8 gold regions in `urlutils.py`).
- Craft touched **only `urlutils.py`** (correct file), wrote a 208-line fix, and **independently rebuilt
  the gold's own concept** — a `_host_has_forbidden_chars()` helper wired into `_is_url_naive`/`_is_url_dns`.
- Grade: **233/248 pass, 15 fail.** All 15 are one cluster of `test_is_url` DNS-mode cases.
- Failing assertion: `assert fake_dns.used → False`. Craft returns early on forbidden-char hosts
  **before** the DNS request; gold consults DNS. The held-out test pins gold's *when-to-consult-DNS*
  ordering — across `%20`-URLs, underscore hosts, and `never`-mode space-strings — a detail the problem
  statement never specifies.

**Calibrated read:** not claiming craft's fix is equally valid (some of the 15 may be genuine craft
bugs). The defensible claim is narrower and sufficient: after *perfect* localization and the *correct*
concept, the residual is a behavioral matrix the prose underdetermines and only the held-out test
enumerates. Localization was never the bottleneck.

## The decomposition this implies

- floor (~50%, contaminated est.): prose determines the fix → reasoning solves it.
- +45 (floor → ~95%): prose underdetermines the fix; the **oracle** supplies the spec via iterate-to-green.
  This band is the entire harness lift, and it is unreachable oracle-free except by recall or a lucky guess.
- ~5% (→100%): irreducibly hard + bench defects.

Oracle-free reasoning is capped at the floor. The clean floor (contamination-removed) is likely below
50% and is unmeasured — the open experiment is oracle-free **+ post-cutoff**.
