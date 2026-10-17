# CVE / vulnerability patching

## Read an advisory
Source = GitHub Advisory (GHSA), OSV, or NVD (CVE). Note the affected version range, the fixed version, and the **CVSS** score (9.0+ critical, 7.0–8.9 high) with its vector (attack vector, network-reachable, privileges required). CVSS 4.0 is current; many feeds still show 3.1.

## Is it reachable?
A vuln in a package whose vulnerable path you never call is lower priority. Reachability tools: `govulncheck` (Go, call-graph), `osv-scanner` v2 (Go call analysis on by default; needs the Go toolchain on PATH), Snyk. "Unreachable" is a prioritization signal, not "safe forever".

## Transitive deps
Force a patched transitive version when you can't wait for the parent:
- npm `"overrides"`, pnpm `"pnpm.overrides"`, yarn `"resolutions"`
- Cargo `[patch]`, Go `replace`, Python a pinned constraint

## Scanning & SBOM
`osv-scanner scan -r .` / `--lockfile=package-lock.json` / `--sbom=sbom.json`. Generate an SBOM (CycloneDX or SPDX) with `syft`, `cdxgen`, `npm sbom`, `cargo cyclonedx`; scan with `grype` or `osv-scanner`. Python: `pip-audit`; Rust: `cargo audit`; Go: `govulncheck`.
