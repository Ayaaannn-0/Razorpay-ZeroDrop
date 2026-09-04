# Legal & Compliance Notes

This isn't a substitute for actual legal advice — it's a checklist so your submission doesn't get flagged for an obvious compliance gap. Razorpay operates in a regulated space (RBI-governed payments), so judges will notice if you've clearly ignored this.

---

## 1. Data You're Handling & Why It Matters

You will touch:
- Customer email & phone number → **PII (Personally Identifiable Information)**
- Partial card details (network, issuer, last 4 digits) → **sensitive financial metadata**
- Transaction amounts → **financial data**

**Rule of thumb for your build:** never store, log, or display a full card number, CVV, or OTP. Razorpay itself never sends you these — you'll only ever see masked/tokenized data via their API, which is good, but be deliberate about it in your docs anyway. Judges like seeing you explicitly call this out.

---

## 2. RBI (Reserve Bank of India) Relevant Rules

You don't need to become a compliance expert, but know these exist so your rule engine and explanations don't contradict them:

- **Recurring payment auto-debit limit** — RBI mandates additional authentication (AFA) for recurring transactions above ₹15,000 (this has been a real source of "silent" mandate failures — good material for your `decline_rules.json`)
- **UPI transaction limits** — vary by bank/UPI app, commonly ₹1,00,000/day for P2M
- **Card tokenization mandate** — RBI requires card details to be tokenized for online transactions since 2022; merchants can't store raw card numbers

Reference these accurately in your PRD's problem statement — don't invent numbers. If you're not 100% sure of a current limit, phrase it as "RBI-mandated additional authentication above a threshold" rather than quoting a number you haven't verified.

---

## 3. TRAI (Telecom Regulatory Authority of India) — SMS Compliance

If your MVP sends SMS notifications:
- Sender ID must be registered (DLT - Distributed Ledger Technology registration) for any commercial SMS in India
- Must include opt-out/unsubscribe language
- Cannot send promotional content disguised as transactional alerts

**For your hackathon build:** you won't actually complete DLT registration in a few weeks — that's fine. State clearly in your docs "Production deployment would require DLT-registered sender ID per TRAI regulations" — this shows you know the real-world requirement even though your demo uses a sandbox/test SMS provider.

---

## 4. Data Protection — India's DPDP Act (Digital Personal Data Protection Act, 2023)

India's own data protection law (parallel to GDPR). Key things to state you'd handle:
- **Consent** — customer must consent to being contacted (they already consented to the transaction, but explicit consent language matters)
- **Purpose limitation** — data collected for payment recovery shouldn't be reused for marketing without separate consent
- **Data minimization** — only collect/store what's needed (don't hoard full transaction histories "just in case")
- **Right to erasure** — customers can request their data be deleted

---

## 5. What to Put in Your Actual Submission

Add a short "Compliance & Trust" section to your pitch deck/demo covering:
1. We never store full card numbers or OTPs (Razorpay tokenizes this already)
2. SMS notifications would use a DLT-registered sender in production
3. We follow data minimization — only decline metadata needed for explanation, nothing more
4. Customer consent for notifications is implicit in transaction consent, but unsubscribe is always available

This single slide/section signals maturity to judges far beyond its length — most hackathon teams skip this entirely, so including it is a differentiator.

---

## 6. Intellectual Property Note

- Don't use Razorpay's logo/branding in a way that implies official endorsement — call it "built for Razorpay's buildathon" or "a concept demo," not "Razorpay's new product"
- Keep any sample data you use (bank names, error codes) factual/public — don't fabricate quotes or claim data you don't have
- If you reference real customer complaints you found via web search, don't quote them verbatim in your slides — paraphrase and cite the general source (e.g., "based on patterns seen in merchant community forums")

---

## 7. What NOT to Overbuild

You do not need to:
- Actually register for DLT
- Get real legal sign-off
- Implement a full DPDP-compliant data deletion pipeline

You DO need to:
- Show you're aware of these constraints in your docs/demo
- Design your data model so real compliance would be straightforward to add later (e.g., don't hardcode PII into unrelated tables)
