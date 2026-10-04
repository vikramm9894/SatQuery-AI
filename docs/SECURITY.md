# SatQuery AI — Security & Trust Architecture

**Document Version:** 2.0.0  
**Compliance Standard:** ISRO SIH26167 Data Integrity & Safety Charter

---

## 1. Zero-Trust Security Architecture
SatQuery AI handles high-resolution satellite imagery and national Earth observation data. The platform implements multi-layer defense-in-depth security principles across ingestion, query interpretation, computation, and report delivery.

```
Incoming Request
      │
      ▼
[1. Path Traversal & MIME Validation]  ──(Violation)──► [HTTP 403 / 422 Rejection]
      │
      ▼
[2. Prompt Injection Neutralizer]      ──(Hostile)──► [Redacted / Security Alert]
      │
      ▼
[3. Session Isolation & Quotas]        ──(Exceeded)──► [HTTP 413 Quota Exceeded]
      │
      ▼
[4. Deterministic Physics Sandbox]     ──(Fails)──► [Honest TARGET_NOT_FOUND]
      │
      ▼
[5. Cryptographic SHA-256 Run Seal]    ──(Signed)──► [HMAC Tamper-Proof Report]
```

---

## 2. Ingestion Defenses

### 2.1 Path Traversal Mitigation
All user-specified filenames, paths, and raster identifiers are rigorously sanitized by `satquery.security.sanitizer.validate_safe_path`:
- Prevents directory traversal sequences (`../`, `..\`).
- Disallows absolute path escaping outside designated session roots.
- Detects and rejects null bytes (`\x00`).

### 2.2 Magic Bytes Binary Validation
File headers are inspected at the binary level using `validate_file_magic`:
- Only authentic GeoTIFF (`II*\x00` / `MM\x00*`), PNG (`\x89PNG`), and JPEG headers are accepted.
- Windows PE executables (`MZ`), Linux binaries (`\x7fELF`), and script files (`#!/`, `<?php`, `<script`) are automatically rejected.

---

## 3. Agentic & Prompt Safety

### 3.1 Prompt Injection Defense
User queries undergo lexical filtering to neutralize adversarial jailbreak patterns:
- Detects phrases attempting system prompt overrides (`ignore previous instructions`, `you are now DAN`, `system: override`).
- Neutralizes malicious injection prefixes while preserving the underlying remote-sensing questions.

### 3.2 Anti-Hallucination & Honest Abstention
- The **Anti-Hallucination Guard** (`satquery.agent.anti_hallucination`) enforces a strict confidence threshold (default 0.40).
- If physical evidence fails to corroborate the user's premise, the system emits an honest `TARGET_NOT_FOUND` response with explanatory physics evidence rather than fabricating detections.

---

## 4. Cryptographic Proof of Chain of Custody
Every analysis run produces two cryptographic artifacts:
1. **Deterministic Run Signature (`run_signature_hash`)**: SHA-256 hash computed over input image checksums, query string, model versions, and final metrics.
2. **HMAC Tamper-Proof Audit Token (`report_tamper_token`)**: Cryptographically signed seal verifying report authenticity and preventing tampering.
