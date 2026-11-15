# Reference Material

The original author notes, preserved exactly as they were written, before the
engineering audit. They are kept here for two reasons: to document where the
project came from, and to show which claims in the notes did not match the
actual lab.

| File | What it is |
|---|---|
| [`server-services-notes.md`](server-services-notes.md) | The original notes on the centralized DNS, HTTP/HTTPS and email services. |
| [`isp-nat-pat-live-demo.pdf`](isp-nat-pat-live-demo.pdf) | The original Bengali demonstration script for the NAT/PAT + ISP section. |

---

## Where the notes and the lab disagreed

The original notes described a **working** demonstration. The audit found
that three of the described behaviours did not actually work in the lab:

| The notes claim | What the lab actually did |
|---|---|
| "the complete Sales email address is `sales@company.com`" | The Sales mail client was configured as `sales@gmail.com`, so the mail server rejected every message. |
| The DNS server is `Server1` with two A records | DNS was enabled on **two** servers, and the mail server's record was `" mail.company.com"` with a leading space. |
| The mail domain is `company.com` and the users are `sales` and `hr` | This one was correct — but it was the *only* correct part of the e-mail chain. |

All of these are fixed in the shipped lab. The full record is in
[`../../docs/AUDIT-FINDINGS.md`](../../docs/AUDIT-FINDINGS.md).

---

## Why keep them?

1. **Honesty.** A repository that presents the polished result without ever
   showing the original misrepresents how the work was done.
2. **Reproducibility.** `apply_fixes.py` regenerates the hardened lab from the
   pristine `.pkt`, and these notes document the intent behind it.
3. **Reference.** The Bengali PDF is the author's own demonstration script and
   remains the most concise description of the PAT/ISP section. The English,
   cleaned-up version is [`../../docs/NAT-PAT-ISP.md`](../../docs/NAT-PAT-ISP.md).
