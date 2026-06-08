# KNOWN_AMBIGUOUS — gold passes, prose underdetermines

Gold passes its verifier, but the hidden test checks behavior no requirement determines (a specification lottery). The blank cells in each attribution are the evidence. Screen = codex coverage table; confirm with the decontaminated panel (see docs/ADMISSIBILITY-SPEC.md).

| case | instance_id | coverage | gaps | example gap behaviors | attribution |
|---|---|---|---|---|---|
| qutebrowser | `instance_qutebrowser__qutebrowser-e34dfc68647d087ca3175d9ad3f023c30d8c9746-v363c8a7e5ccdf6968fc7ab84a2053ac78036691d` | 17/21 | 4 | is_url('existing-tld.domains') is True under dns autosearch; is_url('example.search_string') is True under naive autosearch; is_url('example_search.string') is True under naive autosearch; is_url('test') is True when auto_search is 'never' and url.open_base_u | [table](data/attribution/qutebrowser.md) |
| tutao | `instance_tutao__tutanota-51818218c6ae33de00cbea3a4d30daac8c34142e-vc4e41fd0029957297843cb9dec4a25c7c756f029` | 16/29 | 13 | saveBlob with no default download path creates the selected parent dir; saveBlob with no default download path throws CancelledError when the ; saveBlob with a default download path creates /a/download/path with {r; saveBlob with a default download path and existing blob writes /a/down … | [table](data/attribution/tutao.md) |
