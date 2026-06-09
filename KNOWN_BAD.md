# KNOWN_BAD — gold fails its own grader

Mechanical defects (binary): the reference solution does not pass the official verifier at the pinned commit. Frozen pre-run, results-independent. Receipt: `data/cases/gold_fails_grader.defects.jsonl`. (These three are public Pro tasks audited pre-run; they sit outside the 728-task prose-set denominator.) **The full gold-passes-verifier sweep is now complete**: all 731 graded (727 eligible, 0 incomplete); it independently **re-confirmed exactly these three** and found **no genuine new defects** — one parallel-sweep candidate (a tutao instance) cleared on isolated rerun (gold RESOLVED, Accuracy 100%), per the DeepSWE isolation protocol. Receipt: `data/gold_sweep/`.

| instance_id | grader verdict |
|---|---|
| `instance_future-architect__vuls-bff6b7552370b55ff76d474860eead4ab5de785a-v1151a6325649aaf997cd541ebe533b53fddf1b07` | gold NOT resolved |
| `instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan` | gold NOT resolved |
| `instance_ansible__ansible-de5858f48dc9e1ce9117034e0d7e76806f420ca8-v1055803c3a812189a1133297f7f5468579283f86` | gold NOT resolved |
