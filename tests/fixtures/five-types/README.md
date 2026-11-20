# Selected five-type integration inputs

Every payload here is copied byte-for-byte from immutable shared specification
v0.8.0, commit 72cb46b98160ecc7a7f20ef579a6879d5030c40b. `provenance.json` records
paths, sizes and SHA-256 digests. These are selected integration cases, not a new
normative corpus: the shared FHT 93 and native-owning FHGM 92 suites remain their
own authorities. Preserved owning FHGM carrier bytes are tested against the
separately published native0.1 contract; no header selector was rewritten.

All examples are synthetic. Preserve supplied metadata and source licensing;
see the [source license](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.8.0/LICENSE).
No annotation, sequence or checksum is invented here. Runtime gzip variants wrap
the same byte-exact source, and the toolkit performs extraction/stripping and
recombination. Tests assert exact decompressed payload bytes, not compressed
bitstream identity or biological derivation.
