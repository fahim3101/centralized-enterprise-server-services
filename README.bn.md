# Centralized Enterprise Server Services

[![Cisco Packet Tracer](https://img.shields.io/badge/Packet%20Tracer-9.0.1-0D9D8B?style=for-the-badge&logo=cisco&logoColor=white)](https://www.netacad.com/courses/packet-tracer)
[![CI](https://github.com/fahim3101/centralized-enterprise-server-services/actions/workflows/ci.yml/badge.svg)](https://github.com/fahim3101/centralized-enterprise-server-services/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-2E7D32?style=for-the-badge)](README.md)

> **English version → [README.md](README.md)**

একটি প্রফেশনাল, প্রোডাকশন-রেডি **Cisco Packet Tracer** ল্যাব — যেখানে **কেন্দ্রীভূত DNS, HTTP/HTTPS ও Email** সার্ভিস তৈরি করে হেড অফিস এবং চারটি রিমোট ব্রাঞ্চে OSPF/IPsec WAN-এর মাধ্যমে পৌঁছানো হয়, সাথে PAT-ভিত্তিক ইন্টারনেট এক্সেস।

---

## সংক্ষিপ্ত

সাধারণ "কম্পিউটার নেটওয়ার্ক" প্রজেক্টে একটি সার্ভার আর একটি ফ্ল্যাট LAN থাকে। এই প্রজেক্টে একটি **সম্পূর্ণ এন্টারপ্রাইজ WAN আর্কিটেকচার** আছে, যেখানে আছে:

| স্তর | প্রযুক্তি |
|---|---|
| Access | VLAN, trunk, port-security, STP, LACP port-channel |
| Distribution | **HSRP** — প্রতিটি ইউজার VLAN-এ first-hop redundancy |
| Routing | **OSPF area 0** — ৬টি সাইট জুড়ে, default-route origination সহ |
| WAN | **IPsec site-to-site VPN** (AES + SHA-HMAC) |
| Services | **DHCP, DNS, HTTP, HTTPS, SMTP, POP3** |
| Security | Named extended **ACL**, **PAT** |
| Internet | **NAT/PAT** → সিমুলেটেড ISP → Internet server |

এই রিপোজিটরির সবকিছু আসল ল্যাব ফাইল [`lab/main_project.pkt`](lab/main_project.pkt) থেকে **প্রোগ্রাম করে বের করা** — কনফিগ, IP প্ল্যান, ক্যাবলিং আর সার্ভিস ডেফিনিশন হাতে লেখা নয়। তাই ডকুমেন্টেশন আর ল্যাব কখনো আলাদা হয়ে যেতে পারে না।

---

## টপোলজি

```
 ┌──────────┐   Serial + IPsec    ┌──────────────┐   10.3.3.0/24   ┌──────────┐
 │ Branch 1 │◄───────────────────►│  HQ-WAN-RTR  │◄────────────────►│ EDGE-RTR │
 │  .13/24  │   5.1.1.0/24        └──────┬───────┘                  │   PAT    │
 └──────────┘                             │ 10.1.1.0/24               └────┬─────┘
 ┌──────────┐   Serial + IPsec             │                              │
 │ Branch 2 │◄─────────────────────────────┤                       ┌──────┴─────┐
 │  .14/24  │   6.1.1.0/24           ┌─────┴──────┐                │    ISP     │
 └──────────┘                          │  core-01  │                └──────┬─────┘
 ┌──────────┐   Serial + IPsec          │ HSRP ACT  │                       │
 │ Branch 3 │◄─────────────────────────┤ DHCP srv  │              ┌────────┴────────┐
 │  .15/24  │   7.1.1.0/24             │ OSPF area0│              │ Internet Server │
 └──────────┘                          └─────┬──────┘              │  203.0.113.10  │
 ┌──────────┐   Serial + IPsec                │                     └─────────────────┘
 │ Branch 4 │◄─────────────────────────┐      │
 │  .16/24  │   8.1.1.0/24          ┌──┴──────┴──┐   ┌─────────────────────────┐
 └──────────┘                        │  leaf-01/02│   │   Server VLAN 20        │
                                     └──────┬────┘   │  172.10.10.0/24         │
                                            │        │                         │
                                     ┌──────┴────┐   │ Server0 .1 HTTP/HTTPS    │
                                     │ Access    │   │ Server1 .2 DNS          │
                                     │ Sales/HR/ │   │ Server2 .3 SMTP/POP3    │
                                     │ Accounts  │   └─────────────────────────┘
                                     └───────────┘
```

পূর্ণ ডায়াগ্রাম: [`docs/images/topology.md`](docs/images/topology.md)

---

## কেন্দ্রীভূত সার্ভিসগুলো

### DNS — `Server1` @ `172.10.10.2`

পুরো এন্টারপ্রাইজের জন্য একটিমাত্র authoritative DNS।

```
www.company.com  ->  172.10.10.1   (Web Server)
mail.company.com ->  172.10.10.3   (Mail Server)
homelab.local    ->  172.10.10.2   (নিজের নিজের রেকর্ড)
```

### Web — `Server0` @ `172.10.10.1`

HTTP ও HTTPS চালু, কোম্পানির কর্পোরেট ইন্ট্রানেট পোর্টাল সার্ভ করছে
([`assets/web/index.html`](assets/web/index.html))।

### Email — `Server2` @ `172.10.10.3`

SMTP domain `company.com`, POP3 রিট্রিভাল, তিনটি মেলবক্স:

| User | Password | ঠিকানা |
|---|---|---|
| `sales` | `sales123` | `sales@company.com` |
| `hr` | `hr123` | `hr@company.com` |
| `shanto` | `shanto123` | `shanto@company.com` |

### DHCP — `core-01`

একটিমাত্র DHCP সার্ভার **সাতটি** ইউজার নেটওয়ার্কের জন্য (৩টি HQ ডিপার্টমেন্ট + ৪টি ব্রাঞ্চ)। ব্রাঞ্চগুলো `ip helper-address` দিয়ে DHCP relay করে।

---

## ডিভাইস ইনভেন্টরি

মোট **৪২টি ডিভাইস**। পূর্ণ টেবিল: [`docs/DEVICE-INVENTORY.md`](docs/DEVICE-INVENTORY.md)

| গ্রুপ | ডিভাইস |
|---|---|
| HQ Core | `core-01`, `core-02` |
| HQ Leaf | `leaf-01`, `leaf-02` |
| HQ Access | `access-sales-01`, `access-hr-01`, `access-accounts-01` |
| HQ WAN | `HQ-WAN-RTR` |
| Internet Edge | `EDGE-RTR`, `ISP` |
| Branch | `BR1..BR4-WAN-RTR` + `BR1..BR4-ACCESS` |
| Server | `Server0` (Web), `Server1` (DNS), `Server2` (Mail), `Server3` (Internet) |
| Endpoint | ৯টি HQ PC, ৮টি Branch PC |

---

## IP প্ল্যান (সংক্ষেপে)

| ব্যবহার | নেটওয়ার্ক | গেটওয়ে |
|---|---|---|
| Sales | `192.168.10.0/24` | `192.168.10.254` |
| HR | `192.168.11.0/24` | `192.168.11.254` |
| Accounts | `192.168.12.0/24` | `192.168.12.254` |
| Branch 1–4 | `192.168.13–16.0/24` | `.254` |
| **Server VLAN 20** | `172.10.10.0/24` | `172.10.10.254` |
| PAT ঠিকানা | `200.1.1.1` (ISP পাশে) | — |

পূর্ণ টেবিল: [`docs/IPAM.md`](docs/IPAM.md)

---

## যা যা ঠিক করা হয়েছে

মূল ল্যাবে **২৮টি সমস্যা** ছিল। সবগুলো ঠিক করা হয়েছে — বিস্তারিত:
[`docs/AUDIT-FINDINGS.md`](docs/AUDIT-FINDINGS.md)

সবচেয়ে গুরুতরগুলো:

| # | সমস্যা | সমাধান |
|---|---|---|
| 🔴 | Sales মেল ক্লায়েন্টের ঠিকানা ছিল `sales@gmail.com` — সার্ভারের domain `company.com`, তাই মেল **চলতই না** | `sales@company.com` করা হয়েছে |
| 🔴 | **দুটি সার্ভারে DNS চালু** ছিল, একটির রেকর্ড নামে leading space ছিল (`" mail.company.com"`) — split-brain DNS | একটিমাত্র authoritative DNS রাখা হয়েছে |
| 🔴 | DHCP pool-এ core-এর SVI address (`.252`, `.253`) exclude করা ছিল না — intermittent connection loss | exclusion ঠিক করা হয়েছে |
| 🟠 | **৯টি ডিভাইসের hostname ছিল `Switch`, ৫টির `Router`** — CLI output অস্পষ্ট | সব hostname ইউনিক করা হয়েছে |
| 🟠 | ব্রাঞ্চ PC-র নামে typo ছিল `192.186.x.x` (সঠিক `192.168.x.x`) | `BR1-PC1` … `BR4-PC2` করা হয়েছে |
| 🟠 | `core-02`-এ DHCP relay ছিল না — core-01 fail হলে lease আসত না | `ip helper-address` যোগ করা হয়েছে |
| 🟠 | Web server Packet Tracer-এর default splash page দেখাচ্ছিল | আসল কর্পোরেট পোর্টাল বসানো হয়েছে |
| 🟡 | সব সার্ভারে FTP/TFTP চালু ছিল | বন্ধ করা হয়েছে |

---

## দ্রুত শুরু

### ল্যাব চালানো

1. Cisco Packet Tracer খুলুন
2. `File → Open` → [`lab/main_project.pkt`](lab/main_project.pkt)
3. DHCP lease settle হতে ও OSPF converge হতে ~৬০ সেকেন্ড অপেক্ষা করুন
4. `SALES-PC1` → `Desktop → Command Prompt`:

   ```
   C:\>ping www.company.com
   C:\>ping mail.company.com
   C:\>ipconfig
   ```

5. `Desktop → Web Browser` → `http://www.company.com`
6. `Desktop → Email` → `sales@company.com` থেকে `hr@company.com`-এ মেল পাঠান

### কনফিগ আবার বের করা

```bash
pip install -r scripts/requirements.txt
python scripts/pkt_export.py lab/main_project.pkt --out configs/
```

### অটোমেটেড অডিট চালানো

```bash
python scripts/audit_lab.py lab/main_project.pkt --strict --allow-warning "IPsec DH group"
```

```
[PASS] 35টি check — 0 failure
```

---

## ডকুমেন্টেশন ইনডেক্স

| ডকুমেন্ট | বিষয় |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | স্তর ধরে ডিজাইনের যুক্তি |
| [`docs/DEVICE-INVENTORY.md`](docs/DEVICE-INVENTORY.md) | প্রতিটি ডিভাই, পোর্ট ও ভূমিকা |
| [`docs/IPAM.md`](docs/IPAM.md) | প্রতিটি IP ঠিকানা ও তার কাজ |
| [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) | ধাপে ধাপে সব সার্ভিস কনফিগারেশন |
| [`docs/TESTING.md`](docs/TESTING.md) | ২০টি টেস্ট ও প্রত্যাশিত আউটপুট |
| [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) | সমস্যা → কারণ → সমাধান |
| [`docs/VIVA_QA.md`](docs/VIVA_QA.md) | ৪০টি ভাইভা প্রশ্ন ও উত্তর |
| [`docs/NAT-PAT-ISP.md`](docs/NAT-PAT-ISP.md) | PAT / ISP ডেমো স্ক্রিপ্ট |
| [`docs/SECURITY.md`](docs/SECURITY.md) | সিকিউরিটি মডেল ও হার্ডনিং পরিকল্পনা |
| [`docs/AUDIT-FINDINGS.md`](docs/AUDIT-FINDINGS.md) | মূল ল্যাবের সব সমস্যা ও সমাধান |

---

## স্বীকৃতি

- ল্যাব ডিজাইন ও কনফিগারেশন: প্রজেক্টের লেখক।
- টপোলজি ডায়াগ্রাম: Mermaid (GitHub-এ রেন্ডার হয়)।
- ল্যাব টুলিং: [`pkt-core`](https://pypi.org/project/pkt-core/) — Packet Tracer ফাইল ফরম্যাটের ওপেন-সোর্স রিভার্স-ইঞ্জিনিয়ারিং লাইব্রেরি।

## লাইসেন্স

[MIT License](LICENSE)।
