# Ambiguity witness -- future-architect_472df0e1  (codebase-plurality)

- instance_id: `instance_future-architect__vuls-50580f6e98eeb36f53f27222f7f4fdfea0b21e8d`
- class: **codebase-plural** (PROVEN -- two live conflicting precedents, prose silent)
- repo `future-architect/vuls` @ `472df0e1b6`

## The underdetermined choice
Whether a produced models.CveContent Title is populated from the source vulnerability title, populated from another source text field, or left unset when ingesting vulnerability feeds.

## The codebase already does it more than one way (live, comparable, prose-silent)
A from-codebase solver finds these coexisting production precedents making the choice differently; the prose names no rule, so either is defensible. The hidden test pins one.

1. `detector/wordpress.go` -- copies the WPScan payload title into CveContent.Title
   ```
   Title:        vulnerability.Title,
   ```
2. `detector/github.go` -- uses the source advisory summary as CveContent.Title while storing description separately as Summary
   ```
   Title:         v.Node.SecurityAdvisory.Summary,
					Summary:       v.Node.SecurityAdvisory.Description,
   ```
3. `gost/redhat.go` -- leaves CveContent.Title unset and records the source description only as Summary
   ```
   return &models.CveContent{
		Type:          models.DebianSecurityTracker,
		CveID:         cve.CveID,
		Summary:       cve.Description,
   ```

_Guard: each precedent verified to occur verbatim at base_commit in a non-test, non-example, non-vendor, non-deprecated path (grep); the prose is silent on the choice. codex proposed; citations mechanically verified._
