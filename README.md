# OfferCheck (InternShield) 🛡️
### AI-Assisted Fake Internship Offer Email Detection System

> Built by first-year B.Tech CSE students at Bennett University, advancing **UN SDG 16** (Target 16.5: Peace, Justice & Strong Institutions — Student Cyber Fraud Protection) and **UN SDG 8** (Target 8.6: Decent Work & Economic Growth — Safe Youth Employment).

---

## 📌 Project Overview
**OfferCheck** is an end-to-end security platform designed to detect fraudulent internship offers, advance-fee recruitment scams, and credential harvesting phishing attacks. Students paste raw email content or upload `.eml` files to receive a calibrated **0–100 Risk Score**, a definitive **Verdict Stamp**, weighted findings breakdown, and clear action protocols.

### 🎯 Key Differentiators
- **Strict Zero-Fee Enforcement:** Corporate internships pay stipends; legitimate recruiters never request fees. Any demand for registration, laptop courier, or training deposit triggers a critical high-risk override ($\ge 75$).
- **Bennett CDC Benchmarking:** Calibrated against verified university drives sent by **Sudeepta Chauhan** (Bennett University Career Development Centre) vs. deceptive lookalikes (`@bennett-careers.org`) and compromised student mail accounts (e.g. Umesh Chandra College phishing spoof).
- **Automated Spam Sequestering:** High-risk offers ($\text{Score} \ge 55$) are automatically quarantined into a local Spam Vault with 1-click exportable Outlook Mailbox filter rules.
- **Privacy First (PII Redaction):** In-flight redaction of Indian Aadhaar, PAN cards, phone numbers, bank accounts, and UPI handles before evaluation.

---

## 🧱 Architecture & Tech Stack

```
OfferCheck System Architecture
├── Frontend:
│   ├── Pure Dark Navy Design System (#0f1626, #16203a, #8ea2ff)
│   ├── Typography: Fraunces (Headings, Verdict Stamp) + Instrument Sans (Body)
│   ├── Rotated Animated Verdict Stamp (Low risk, Suspicious, Likely fake)
│   ├── Thin Risk Meter Bar on #2a3856 track
│   └── 6 Interactive Views: Analyzer, Simulator, How it Works, Spam Vault, Lab Tests, Rules
│
├── Backend & Detection Engines:
│   ├── Python 3.11/3.14 + FastAPI (Async REST API)
│   ├── Normalization (NFKC Unicode, HTML unescaping)
│   ├── Presidio & Regex PII Redactor (Aadhaar, PAN, Bank A/C, Phone)
│   ├── Rules Engine (17 YAML Heuristic Rules with Negation Guards)
│   ├── Cryptographic Header Evaluator (SPF, DKIM, DMARC)
│   └── Score Fusion Engine (0.65 * Rules + 0.35 * ML)
│
└── Infrastructure:
    ├── Docker Compose (FastAPI, Redis, PostgreSQL)
    └── Standalone Zero-Dependency Web App Server (Node.js)
```

---

## 🚦 Risk Score & Verdict Rubric

| Risk Score | Verdict Stamp | Visual Color | Primary Action Protocol |
|:---|:---|:---|:---|
| **0 – 24** | **LOW RISK** | `#4cc38a` (Green) | Standard verification via official portal; safe to proceed. |
| **25 – 54** | **SUSPICIOUS** | `#f0a63a` (Amber) | Caution: Check with college placement cell / mentor before responding. |
| **55 – 100** | **LIKELY FAKE** | `#ff6b73` (Red) | Threat: Auto-quarantined to Spam Vault. Report to Cyber Helpline 1930. |

*Safety rule: The system never outputs "verified". The safest positive verdict is always "Low risk".*

---

## ⚡ Quick Start

### Option 1: Standalone Web Application
Run the zero-dependency web interface on port 3000:
```bash
node server.js
```
Open **`http://localhost:3000`** in your browser.

### Option 2: Python Backend Tests
Run the unit test suite verifying the 17 heuristic rules, negation guards, and PII redactor:
```bash
cd backend
python -m pytest tests -v
```

### Option 3: Docker Compose
```bash
docker compose up -d
```

---

## 📁 Repository Structure
```
├── backend/
│   ├── app/
│   │   ├── engine/
│   │   │   ├── normalizer.py      # Unicode NFKC & HTML sanitizer
│   │   │   ├── parser.py          # SPF/DKIM/DMARC & header parser
│   │   │   ├── pii.py             # Indian Aadhaar, PAN, Phone, Bank redactor
│   │   │   └── rules.py           # YAML rules engine & hard overrides
│   │   └── rules.yaml             # 17 detection rules & weights
│   └── tests/
│       ├── test_normalizer_pii.py # 9 unit tests for normalizer & PII
│       └── test_rules.py          # 21 unit tests for rules & scoring
├── index.html                     # Full-featured Dark Navy Web Application
├── server.js                      # HTTP server with no-cache headers
├── docker-compose.yml             # Container orchestration
├── .env.example                   # Environment variable blueprint
└── README.md                      # Documentation
```

---

## ⚖️ Academic Context & SDGs
- **Primary SDG 16:** Peace, Justice & Strong Institutions (Target 16.5: Substantially reduce corruption and bribery in all forms; Target 16.4: Combat cyber financial crimes).
- **Secondary SDG 8:** Decent Work & Economic Growth (Target 8.6: Substantially reduce the proportion of youth not in employment, education, or training by preventing sham employment).
- **Legal Penalties:** Information Technology Act, 2000 (Section 66D: Cheating by personation; Section 66C: Identity theft; IPC 420: Cheating and dishonestly inducing property delivery).

---
*Developed for Bennett University Computer Science Engineering & Campus Safety Initiatives.*
