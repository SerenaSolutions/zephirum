# Open-Source Core, Post-Quantum-Sealed Authorship
2026-10-15 · house policy record

Open source and secrecy are opposites: the code stays readable so the world can
run, verify and adopt it. What we protect is AUTHORSHIP and INTEGRITY:

1. The entire core tree hash (docs/AUTHORSHIP_MANIFEST.json) is sealed with an
   ML-DSA-44 (FIPS 204, post-quantum) signature inside the house receipt chain.
   Any tree copied or modified produces a different hash — the seal is our
   unforgeable authorship proof, valid even against quantum adversaries.
2. Priority records already in place: DOI 10.5281/zenodo.23330695 (immutable),
   signed commits, daily signed science log.
3. Trademark + program registration (INPI) dossier prepared for the founder.
4. The competitive research finding stays in the private workspace — never in
   this repository (house rule).
5. License: MIT for the public core (adoption first). A dual/restrictive
   license for the commercial gate tier remains a founder decision.

Copying the code is legal under MIT. Forging our authorship trail is
cryptographically impossible — today and post-quantum.
