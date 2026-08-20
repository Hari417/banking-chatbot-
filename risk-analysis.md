# Risk Analysis

**Project:** Banking RAG Chatbot v1  
**Type:** Architecture Risk Assessment  
**Date:** 2026-08-20

---

## Executive Summary

This document identifies, assesses, and proposes mitigations for risks in the Banking RAG Chatbot architecture. Risks are categorized by severity and likelihood, with clear ownership on architecture decisions.

**Risk Summary:**
| Level | Count | Status |
|-------|-------|--------|
| Critical | 2 | Mitigated |
| High | 4 | Mitigated |
| Medium | 6 | Monitored |
| Low | 4 | Accepted |

---

## Risk Register

### R001: LLM HALLUCINATION
**Category:** Model Behavior  
**Severity:** 🔴 **Critical**  
**Likelihood:** Likely

**Description:** The LLM may generate incorrect or fabricated information about banking products, policies, or procedures. This could mislead users and create compliance/legal risk.

**Evidence:**
- LLMs are known to hallucinate on edge cases
- Banking domain requires high accuracy
- Financial misinformation has consequences

**Impact:**
- User trust erosion
- Potential regulatory exposure
- Legal liability

**Mitigation:**
1. **Grounding requirement:** System prompt strictly limits answers to provided documents
2. **Source citations:** Every claim linked to specific document excerpts
3. **Response validation:** Check that response references only retrieved documents
4. **Abstention:** Return "I don't know" when confidence is low
5. **Content filter:** Block responses on disallowed topics

**Fallback:**
- Log all low-confidence responses for review
- human-in-the-loop for edge cases (if deployed)

**Status:** ✅ **Mitigated**

---

### R002: PROMPT INJECTION ATTACKS
**Category:** Security  
**Severity:** 🔴 **Critical**  
**Likelihood:** Possible

**Description:** Users or attackers may inject malicious prompts that:
- Override system instructions
- Extract sensitive information
- Cause the model to ignore constraints
- Perform unauthorized actions

**Evidence:**
- Jailbreak attacks are common on LLM systems
- Banking context makes this a higher-value target
- Prompt injection is a known vulnerability class

**Impact:**
- System compromise
- Information disclosure
- Compliance violation

**Mitigation:**
1. **Input sanitization:** Detect and block injection patterns
   - Keyword filtering: "ignore previous", "system prompt", etc.
   - Whitelist/blacklist approach
2. **Defense in depth:** System prompt in code, not user-provided
3. **Output filtering:** Validate response doesn't violate constraints
4. **Rate limiting:** Prevent abuse

**Limitations:**
- Sophisticated attacks may bypass detection
- This is an evolving threat

**Status:** ⚠️ **Accepted with Monitoring**

---

### R003: PII LEAKAGE
**Category:** Data Protection  
**Severity:** 🟠 **High**  
**Likelihood:** Unlikely

**Description:** The system might:
- Store/surface PII from documents in responses
- Retain PII from user queries in session logs
- Embed PII in vectorized form (less retrievable)

**Evidence:**
- Banking documents may contain sample customer data
- Users might paste account details in queries
- Supply chain attacks on embedding models

**Impact:**
- Privacy breach
- GDPR/CCPA violation
- Regulatory fine
- Reputation damage

**Mitigation:**
1. **PII detection:** Use Presidio or regex to detect PII in documents and queries
2. **Redaction:** Remove/detect PII before storing
3. **Query scrubbing:** Scrub input before processing
4. **No real data:** v1 uses only sample documents
5. **Log anonymization:** PII scrubbed from logs

**Status:** ✅ **Mitigated**

---

### R004: INFORMATION DISCLOSURE (BEYOND SCOPE)
**Category:** Scope Control  
**Severity:** 🟠 **High**  
**Likelihood:** Likely

**Description:** Users may ask questions about:
- Their account balances
- Transactions
- Other customers
- Internal systems
- Staff information

The system must not answer these or reveal information beyond the FAQ scope.

**Evidence:**
- Scope is FAQ-only, but users may not understand
- Training data may have incidental information
- LLM may generate plausible-sounding but wrong "personal" info

**Impact:**
- Security breach
- Compliance failure
- User confusion

**Mitigation:**
1. **Intent filter:** Detect out-of-scope queries
2. **Abstention training:** Train rejections for personal data requests
3. **System prompt:** Explicit statement about limitations
4. **Logging:** Track attempts for pattern analysis

**Sample rejections:**
- "I can't access individual account information."
- "I don't have access to transaction records."

**Status:** ✅ **Mitigated**

---

### R005: RETRIEVAL FAILURE
**Category:** System Performance  
**Severity:** 🟠 **High**  
**Likelihood:** Possible

**Description:** The retrieval system fails to find relevant documents:
- Embeddings mismatch (query vs document)
- Index corruption
- Query out of distribution
- Chunking strategy failures

**Impact:**
- Poor user experience
- "I don't know" responses (too conservative)
- Hallucinated answers (we fail, LLM generates anyway)

**Mitigation:**
1. **Hybrid retrieval:** BM25 catches what embeddings miss
2. **Query rewriting:** Rephrase queries for better matching
3. **Fallback:** Broaden search on no-results
4. **Monitoring:** Track retrieval metrics
5. **Graceful degradation:** Clear "no documents found" messages

**Testing:**
- Build evaluation dataset of edge cases
- Monitor recall@k

**Status:** ✅ **Mitigated**

---

### R006: LATENCY DEGRADATION
**Category:** Performance  
**Severity:** 🟠 **High**  
**Likelihood:** Likely

**Description:** Response time exceeds acceptable thresholds:
- Slow LLM API calls
- Inefficient retrievers
- Large documents context
- Concurrent users

**Target:** P50 < 2s, P99 < 5s

**Evidence:**
- LLM overheads: 1-3s typical
- Retrieval: 100-500ms
- Overhead accumulates
- Local models (Ollama) slower than APIs

**Mitigation:**
1. **Async streaming:** Return tokens as they arrive
2. **Cached embeddings:** Don't recompute
3. **Top-K limiting:** Don't retrieve too much
4. **Model selection:** Use faster models (GPT-4o-mini vs GPT-4o)
5. **Connection pooling:** Reuse LLM connections
6. **Optional components:** Enable/disable reranker per query

**Status:** ✅ **Mitigated**

---

### R007: SESSION STATE LOSS
**Category:** Reliability  
**Severity:** 🟡 **Medium**  
**Likelihood:** Unlikely

**Description:** In-memory session storage:
- Lost on process restart
- Lost on crash
- TTL expiration causes unexpected "new session"

**Impact:**
- Lost conversation context
- User frustration (must restate questions)
- But: user can just continue (no data loss)

**Mitigation:**
1. **Acceptable for v1:** Local prototype, single user
2. **Warn user:** Display "session expires after 30 min"
3. **v2 upgrade:** SQLite persistence

**Status:** ✅ **Accepted for v1**

---

### R008: FAISS INDEX CORRUPTION
**Category:** Data Integrity  
**Severity:** 🟡 **Medium**  
**Likelihood:** Rare

**Description:** The FAISS index file may:
- Become corrupted (disk errors, crashes during write)
- Get out of sync with metadata
- Be incompatible after library updates

**Impact:**
- Retrieval system unusable
- Requires complete re-indexing

**Mitigation:**
1. **Checksums:** Save SHA-256 alongside index
2. **Validation:** Startup check to verify index loads
3. **Backup:** Keep previous index version
4. **Automated rebuild:** On corruption, trigger re-index

**Status:** ⚠️ **Partially Mitigated**

---

### R009: EMBEDDING MODEL DRIFT
**Category:** Model/Data  
**Severity:** 🟡 **Medium**  
**Likelihood:** Rare

**Description:** Changes in embedding model or version cause:
- Query documents incompatible
- Different vector spaces
- Need to re-index

**Impact:**
- Wrong retrieval results
- Silent degradation

**Mitigation:**
1. **Pin versions:** Exact library versions in requirements
2. **Version metadata:** Store model info with index
3. **Validation:** Check embedding dimensions match at load
4. **Re-index pipeline:** Documented process for updates

**Status:** ✅ **Mitigated**

---

### R010: DEPENDENCY VULNERABILITIES
**Category:** Security Supply Chain  
**Severity:** 🟡 **Medium**  
**Likelihood:** Possible

**Description:** Third-party libraries may:
- Have unpatched CVEs
- Be abandoned
- Introduce breaking changes
- Contain malicious code (supply chain attacks)

**Impact:**
- System compromise
- Data breach
- Application failure

**Mitigation:**
1. **Minimal dependencies:** Only what is required
2. **Pin versions:** Exact version pinning
3. **Security scanning:** `pip-audit`, `safety`
4. **Virtual environment:** Isolation
5. **SBOM:** Track all dependencies

**Status:** ⚠️ **Mitigated**

---

### R011: API COST ESCALATION
**Category:** Financial  
**Severity:** 🟡 **Medium**  
**Likelihood:** Possible

**Description:** LLM API costs could increase unexpectedly:
- OpenAI price changes
- Traffic spikes (loops, retries)
- Accidental unbounded queries
- Model selection errors (use GPT-4 instead of 4o-mini)

**Impact:**
- Budget overrun
- Service shutdown

**Mitigation:**
1. **Rate limiting:** Hard limits on requests
2. **Max retry policies:** Prevent infinite loops
3. **Model constraints:** Enforce cheapest model in code
4. **Usage tracking:** Monitor token consumption
5. **Local fallback:** Ollama if API costs prohibitive

**Status:** ✅ **Mitigated**

---

### R012: LLM SERVICE UNAVAILABILITY
**Category:** Reliability  
**Severity:** 🟡 **Medium**  
**Likelihood:** Rare

**Description:** OpenAI API or other provider:
- Outage
- Rate limiting
- Geographic restrictions

**Impact:**
- Complete system down
- Poor user experience

**Mitigation:**
1. **Retry logic:** Exponential backoff with jitter
2. **Fallback:** Ollama local mode
3. **Circuit breaker:** Stop hammering dead services
4. **Health checks:** Monitor service availability

**Status:** ✅ **Mitigated**

---

### R013: KNOWLEDGE BASE STALE
**Category:** Data Quality  
**Severity:** 🟢 **Low**  
**Likelihood:** Likely

**Description:** The banking FAQ documents become outdated:
- Policy changes
- Rate changes
- Product updates
- New offerings

**Impact:**
- Outdated information
- User confusion
- Compliance issues

**Mitigation:**
1. **Document versioning:** Track document versions
2. **Ingestion timestamp:** Metadata on ingestion
3. **Regular checks:** Scheduled re-indexing
4. **Clear disclaimer:** "Based on documents as of [date]"

**Status:** ⚠️ **Accepted**

---

### R014: SCALING LIMITATIONS
**Category:** Performance  
**Severity:** 🟢 **Low**  
**Likelihood:** Certain

**Description:** v1 architecture will not scale:
- Single-process FAISS
- In-memory sessions
- File-based documents
- Local LLM (if used) is slow

**Impact:**
- Cannot handle 100+ concurrent users
- Not suitable for multi-tenant production

**Mitigation:**
1. **Scope definition:** v1 is single-user local prototype
2. **Architecture documentation:** Clear v1 limitations
3. **v2 roadmap:** Known migration path

**Status:** ✅ **Accepted by Design**

---

### R015: DOCUMENT FORMAT INCOMPATIBILITY
**Category:** System Integration  
**Severity:** 🟢 **Low**  
**Likelihood:** Possible

**Description:** Unusual document formats or:
- Scanned PDFs (image-based)
- Encrypted documents
- Corrupted files
- Complex layouts (tables, multi-column)

**Impact:**
- Ingestion failures
- Missing content
- Partial information

**Mitigation:**
1. **Format whitelist:** PDF, HTML, TXT supported
2. **Error handling:** Log and skip unsupported files
3. **OCR:** Mark as v2 feature if needed
4. **Pre-validation:** Check document before processing

**Status:** ⚠️ **Accepted**

---

### R016: REGULATORY COMPLIANCE GAP
**Category:** Compliance  
**Severity:** 🟢 **Low**  
**Likelihood:** Unlikely

**Description:** v1 prototype may not meet banking regulations:
- Audit trail requirements
- Data retention policies
- Consumer protection rules
- Accessibility (ADA/WCAG)

**Impact:**
- Regulatory sanctions
- Legal issues

**Mitigation:**
1. **Prototype disclaimer:** "Not for production use"
2. **Scope limitation:** Simple FAQ, no transactions
3. **Logging:** Document all queries (auditability)
4. **v2 compliance:** Engage compliance before production

**Status:** ✅ **Accepted for Prototype**

---

## Risk Heat Map

```
Likelihood
    │
High│  R004    R006
    │  R001
    │
Med │  R005    R002    R011    R012
    │
Low │  R014         R003    R008
    │              R007    R009
Rare├─────────────────────────────────────
    │ Critical  High    Medium   Low
    └────────────────────────────────────
               Impact
```

---

## Mitigation Strategy

### Immediate (Architecture)
| Risk | Action | Owner |
|------|--------|-------|
| R001 | Implement response validation | Forge |
| R002 | Build input sanitization | Forge |
| R003 | Integrate PII detection | Forge |
| R006 | Implement streaming | Forge |

### Monitoring (Sentinel)
| Metric | Alert Threshold |
|--------|-----------------|
| Hallucination rate | >5% |
| P99 latency | >5s |
| Retrieval recall@5 | <0.7 |
| Error rate | >1% |
| PII detection catches | Log all |

### Documentation
- Add risks to user guide
- Include in setup instructions
- Document limitations clearly

---

## Risk Acceptance

By proceeding with this architecture, we accept:

1. **R007** (Session loss) as acceptable for v1
2. **R014** (Scaling limitations) as by-design
3. **R016** (Compliance gaps) as prototype-appropriate

These are tracked and will be addressed in v2.

---

## Risk Review Schedule

| Milestone | Review |
|-----------|--------|
| Post-scout-research | Update with findings |
| Post-impl v1 | Validate mitigations work |
| Pre-v2 planning | Full reassessment |

---

*[End of Risk Analysis]*
