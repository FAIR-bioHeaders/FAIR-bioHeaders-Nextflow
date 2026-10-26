# Security policy

This repository is an unreleased development prototype (`0.1.0-dev`). Security fixes
currently target its current development branch. The tested dependency is
FAIR-bioHeaders-Tools 0.8.2 (FHR schemaVersion 1 cited through the `fhr/v0.3.1`
release URL, FHP schemaVersion 1.0); no long-term support or response-time
commitment is made. Check the companion toolkit's security policy when reporting a
vulnerability in that dependency.

Report suspected vulnerabilities privately, including affected version/commit,
reproduction steps, impact, and any safe proof of concept. Avoid posting
credentials, private genome data, or exploit details in a public issue. Maintainers
should acknowledge receipt, assess severity, coordinate a fix and disclosure,
and credit the reporter with consent. Schema correctness issues without security
impact can use ordinary issues.

## Private reporting channel

Email [molik@fhref.org](mailto:molik@fhref.org) for FHR-Nextflow and the companion FHR repositories. Identify the affected repository and version. This is the maintainer-confirmed reporting address; do not assume GitHub private vulnerability reporting is enabled.

Coordinate disclosure privately with the maintainers. No guaranteed response deadline is stated. If a report involves David Molik, contact [Adam Wright](mailto:wright@fhref.org) at [wright@fhref.org](mailto:wright@fhref.org) directly. If it involves Adam Wright, use David’s address above. Do not copy a maintainer involved in the report; use an uninvolved reviewer for escalation.

## Pipeline-specific reporting

Include the Nextflow version, executor, converter version, container digest if
used, and the smallest safe input that reproduces the issue. Shell injection,
unsafe output paths, unexpected file access, and disclosure through work
directories or logs are relevant security concerns. Replace sensitive sample
metadata with synthetic values before sharing a reproduction.
