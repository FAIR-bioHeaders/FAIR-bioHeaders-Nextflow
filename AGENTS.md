# Agent instructions

## Current repository context

This is a Nextflow DSL2 development/demo suite, not the specification authority.
Use the checkout's pinned toolkit/validator and documented compatibility matrix;
new family releases do not silently upgrade the environment or modules. Route
family workflow expansion through linked toolkit/type-contract work. Supporting
new versions needs deliberate pin, fixture and channel-contract updates; never
invent metadata to satisfy a newly required field.

## Schema additions and their own development cycle

A new optional field, structured alternative, enum value, constraint, required
field or changed meaning is a schema-contract change, even when motivated by a
UI, exporter, parser fix or documentation task. Identify it explicitly as a
**schema addition** or other contract change in its issue and PR. Supporting an
already adopted field in a consumer is implementation work, not a new field.

Schema additions have their own proposal, review, compatibility, versioning and
release cycle. Keep them separately reviewable from routine fixes, website work,
packaging and dependency updates; link dependent implementation PRs rather than
silently adopting a field downstream. Shared fields/objects and cross-type rules
belong in FAIR-bioHeaders-Specification; type-specific design starts in the owning
development repository and is coordinated into shared publication. Name affected
types, requiredness, semantics, mappings, serializers and conformance fixtures.

During active construction of FHP, FHT and FHGFF3, maintainers may iterate on draft
fields with lighter process and include coordinated schema/implementation work in
one clearly scoped PR. Record the proposal and compatibility impact in that PR;
this flexibility does not make every field adopted or supported. Preserve already
published contracts and cited versions, label draft behavior, and obtain joint
maintainer review before publication. FHR additions retain the separate cycle.
Do not apply draft flexibility to released FHP/FHGFF3 schemas retroactively.

Use the shared specification's `docs/SCHEMA-VERSIONS.md` and
`schemas/versions.json`: contract versions are per type, distinct from repository
release tags and biological resource versions. Additive changes that preserve all
valid values and meanings qualify for a minor increment; invalidating records or
changing meanings requires a major increment. Do not assign a new version merely
for implementing an existing contract. Never rewrite immutable releases, fixed
schema aliases or existing file-bound headers as incidental cleanup. Header edits
require checksum recomputation and may affect downstream parent links.

Check the adoption decision and released support before implementing a proposal;
an issue or PR's existence does not establish adoption. Structured vouchers
(FAIR-bioHeaders-Specification#139/#140) and mapping profiles (#56 in that same
repository) have their own review history. Implemented subsets do not establish
full profile or header-family support. The mapping page tracked in
fair-bioheaders.github.io#29 depends on approved profiles. Recheck these records
rather than relying on a copied description of their temporary status.

This DSL2 module suite implements FAIR-bioHeaders-Specification issue #15 in <https://github.com/FAIR-bioHeaders/FHR-Nextflow>. Commit or push only within the user-authorized scope; publication of a release or a visibility change requires an explicit request.

Keep orchestration and JSON creation native to Nextflow. `modules/utils/main.nf` performs serialization, filename checks and shell quoting; it is not a second schema validator. Use the pinned converter for field validation, conversion and exact-byte checksums, and the pinned gff3-validate (0.1.0) for GFF3 rules; never reimplement either. Required FHR fields and schemaVersion semantics belong to the companion specification.

The FHR paper (<https://doi.org/10.1093/bib/bbae122>) motivates provenance preservation, minimal required metadata and interoperable serializations. Interpreting those goals here: pass sample IDs through channels, never invent authors/software/accessions/SeqCol digests, preserve sequence bytes, and validate before exposing outputs downstream.

Run `python tests/run.py` with Nextflow 26.04.6, Java 21 and the hash-locked environment in environment/requirements.txt (generated from requirements.in). Tests exercise module composition, both sequence formats, all conversions, malformed/missing metadata, metadata quoting and converter tests. Use `--converter-source ../FAIR-bioHeaders-Tools` to run its tests. Docker environment checks use `docker build -t fhr-nextflow:0.1.0 environment` and `-profile docker`.

Inspect module channel contracts and docs together. Native exec tasks write only under task.workDir. Quote staged paths, whitelist command formats and constrain output IDs. Do not copy or change schema rules in this repository. No placeholder checksum is silently supplied: standalone JSON requires a checksum; combine calculates the attached file's checksum, and the example publishes only attached-file metadata when given a sequence. Exceptions thrown from helper functions reach users as an opaque InvocationTargetException outside tasks; return a problem message and throw from the closure instead. Record verification and compatibility changes in CHANGELOG.md.

## Repository map and review

`main.nf` is the runnable example; `modules/*/main.nf` contains reusable processes and the JSON workflow; `subworkflows/attach/main.nf` composes attachment, validation and JSON extraction. `nextflow.config` configures the example, not importing projects. `environment/` pins the converter runtime. `tests/integration.nf` checks native composition; `tests/run.py` drives positive and rejection cases from an external project.

Read README, CONTRIBUTING, SECURITY and the pipeline guide before changing their contracts. Preserve CRLF fixture bytes and sample IDs. For documentation-only changes, check relative links and examples; rerun pipelines when executable behavior changes. Update CHANGELOG with relevant verification. Keep human-readable citations in Chicago style with DOI links and machine-readable citation metadata distinct from release identifiers.

David and Adam are the maintainers and jointly hold schema authority; the steering-group option in the companion GOVERNANCE.md is not active. Follow the conduct and security policies for private reporting and conflicts. Never invent a published repository URL, release date, DOI or archival record for this development prototype.

This repository uses MPL-2.0. Preserve its source notices and keep CITATION.cff and README licensing consistent. Do not apply the companion repositories' USDA government-work notice to this suite. External dependencies retain their own licenses.

## Licensing policy (2026-10-09)

This repository already uses MPL-2.0. Preserve its existing LICENSE and all
third-party terms. The USDA public-domain notices in companion repositories
do not apply here. Keep README badges and package/citation metadata consistent;
do not rewrite historical releases or silently relicense upstream material.

## Pin changes and the two Nextflow integration surfaces

This repository owns the runnable demo, DSL2 composition and external-project
integration tests. FAIR-bioHeaders-Tools separately owns nf-core-style modules
under its `nextflow/` tree; a change here does not update or validate those modules.
Keep cross-repository handoffs explicit and avoid creating another schema/parser.

For a compatibility upgrade, inspect `environment/requirements.in`, its generated
hash-locked `requirements.txt`, `environment/Dockerfile`, CI's converter commit and
Nextflow download/hash pins, README compatibility claims, examples and tests.
Change only the pins needed for the intended support; regenerate locks by their
documented command and retain reproducible artifact checks. The suite's own
version, toolkit version, validator version and schema contract are separate.

Run `python tests/run.py --converter-source /path/to/pinned-toolkit` for the
supported baseline and exercise the Docker sequence/GFF3 examples in CI. The
Python runner option is `--converter-source`; the Nextflow workflow parameter is
`--converter_source`. Keep these interfaces distinct. Record candidate-version
checks separately from the pinned baseline so a passing old environment is not
reported as support for a new header family or release.

## Issue, project and code-review behavior

### Issues and the connected project

- Add every issue you work on to the connected project (project #9, "FAIR
  BioHeaders — 2026 refresh") and set `Status` to `In Progress` when work starts.
- Keep `Status` current as the work moves (`Todo`, `In Progress`, `Blocked`,
  `Blocked - In Progress`, `Done`), and set `Outcome` when it closes.
- Link every PR to its issue (`Closes #N` or `Refs #N`). Do not do unreported work.
- After each work run (implementation, tests, review pass), post a status comment
  on the issue or PR: what changed, checks run and results, commit/PR links,
  blockers, and the next action. Do not rely on chat history.

### Code review on a PR

When a PR receives code review (human or Copilot):

1. Read the overall review and every inline comment before changing anything.
2. Make each fix in a **new commit**. Do not amend or force-push over reviewed
   commits; if a rebase is required, cite the new head in the replies.
3. Reply to each inline finding with the fix and the relevant commit hash.
4. Resolve that inline comment/thread.
5. After all findings are handled, post an overall reply to the review
   summarizing each finding's disposition and the commits.
6. Treat optional suggestions as required unless they are genuinely out of
   scope; state why and link a follow-up issue.

Do not push to a repository's main branch or merge a PR without maintainer
approval.
