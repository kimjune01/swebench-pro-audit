# License

This repository is **dual-licensed**: **code under [AGPL-3.0](LICENSE-CODE.txt)**, and **everything else under CC BY-SA-NS** (defined below). The two are deliberately matched — AGPL §13 carries the network-source obligation for code, the Network Services clause below does the same for non-code material. See [Scope](#scope) for the split.

## CC BY-SA-NS (content)

This work is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/), with the following additional condition:

> **Network Services.** If you use a Derivative Work to provide a service over a computer network, you must make the Corresponding Source of the Derivative Work available to users of the service, under the terms of this license or a Compatible License, at no charge.

## Definitions

**Corresponding Source** means the complete source material from which the Derivative Work can be regenerated: the original prose, code, and configuration; any modifications to them; and any build instructions (prompts, scripts, workflows) used in the compilation.

**Compatible License** means CC BY-SA-NS, AGPL 3.0, or any later version of either, or any license at least as protective of the Network Services clause defined above.

> *Compatibility is upward-only.* Plain CC BY-SA 4.0 is **not** a Compatible License — it lacks the Network Services clause and would let a downstream relicense one hop down to escape the network requirement, breaking the chain. AGPL 3.0 qualifies because its own §13 ("Remote Network Interaction") provides the equivalent obligation for code.

## Why

CC BY-SA closes the redistribution loophole — derivatives must stay open. AGPL closes the SaaS loophole for code — running it as a service counts as distribution. CC BY-SA-NS does the equivalent for everything else here: the audit prose, the findings tables, the committed receipts (driver logs, recon handoffs, the craft patch and grade). Either way, if you build a service on top, source flows back to users.

See [the writeup](https://june.kim/cc-by-sa-ns) for the longer argument.

## Scope

**Code → [AGPL-3.0](LICENSE-CODE.txt).** The executable parts: `tools/` (the `diag_oracle.py` diagnosis-vs-gold scorer) and any scripts added later. AGPL §13 (Remote Network Interaction) carries the network-source obligation.

**Everything else → CC BY-SA-NS** (above): the `README`, `docs/` (thesis, prior-art map, findings), and the `data/` receipts (per-instance driver logs, recon handoffs, craft patch + grade output). The Network Services clause gives non-code material the equivalent of AGPL §13.

## Not legal advice

No lawyer has reviewed this. The license is a draft AGPL-for-prose hybrid. Use accordingly.
