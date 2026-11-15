# Server Service Definitions

Packet Tracer stores server services inside the `.pkt` container, not in the
running-config, so these are documented separately. Everything here is
extracted from [`lab/main_project.pkt`](../../lab/main_project.pkt).

Regenerate with:

```bash
python scripts/pkt_export.py lab/main_project.pkt --services
```

---

## `Server0` â€” Corporate Web Server

| Property | Value |
|---|---|
| IP address | `172.10.10.1` |
| Subnet mask | `255.255.255.0` |
| Default gateway | `172.10.10.254` |
| Hostname | `www.company.com` |
| HTTP | **enabled** |
| HTTPS | **enabled** |
| FTP | disabled |
| TFTP | disabled |
| Default page | [`assets/web/index.html`](../../assets/web/index.html) |

### Packet Tracer path

`Server0` â†’ `Services` tab â†’ `HTTP` â†’ `HTTP Service: ON`,
`HTTPS Service: ON` â†’ `Files` tab â†’ upload
[`assets/web/index.html`](../../assets/web/index.html) as `index.html` â†’
`Apply`.

### The page

The default Packet Tracer splash page was replaced with a corporate intranet
portal that lists the service catalogue, the DNS names, the IP plan and the
gateways â€” so the browser window itself becomes evidence during the
demonstration.

### Verify

```
SALES-PC1> ping www.company.com        â†’ 172.10.10.1
```

`Desktop â†’ Web Browser` â†’ `http://www.company.com` â†’ the portal renders.
`https://www.company.com` â†’ the same page over TLS.

---

## `Server1` â€” Authoritative DNS Server

| Property | Value |
|---|---|
| IP address | `172.10.10.2` |
| Subnet mask | `255.255.255.0` |
| Default gateway | `172.10.10.254` |
| DNS service | **enabled** |

### The zone

| Name | Type | Address | TTL |
|---|---|---|---|
| `homelab.local` | A Record | `172.10.10.2` | 86400 |
| `mail.company.com` | A Record | `172.10.10.3` | 86400 |
| `www.company.com` | A Record | `172.10.10.1` | 86400 |

`homelab.local` is the self-record for the DNS server itself.

### Packet Tracer path

`Server1` â†’ `Services` â†’ `DNS` â†’ `DNS Service: ON` â†’ add each record with the
`Add` button.

> **Exactly one server may run the DNS service.** In the original build the
> mail server also had DNS enabled, with a malformed record
> (`" mail.company.com"` â€” a leading space) and only one of the three names.
> Two DNS servers with different zone data is split-brain DNS and produces
> non-deterministic results for the client.

### How clients find this server

`core-01` advertises it through every DHCP pool:

```
ip dhcp pool SALES
 dns-server 172.10.10.2
```

---

## `Server2` â€” Corporate Mail Server

| Property | Value |
|---|---|
| IP address | `172.10.10.3` |
| Subnet mask | `255.255.255.0` |
| Default gateway | `172.10.10.254` |
| Hostname | `mail.company.com` |
| SMTP | **enabled** |
| POP3 | **enabled** |
| SMTP domain | `company.com` |
| DNS service | disabled (kept single-authority) |

### Mailboxes

| Username | Password | Address |
|---|---|---|
| `shanto` | `shanto123` | `shanto@company.com` |
| `sales` | `sales123` | `sales@company.com` |
| `hr` | `hr123` | `hr@company.com` |

### Packet Tracer path

1. `Server2` â†’ `Services` â†’ `EMAIL`
2. `SMTP Service: ON`, `POP3 Service: ON`
3. `Domain Name:` â†’ type `company.com` â†’ press **Set**
4. `Create New User` â†’ `shanto` / `shanto123`, `sales` / `sales123`,
   `hr` / `hr123`

> **The domain field must be set.** With SMTP and POP3 enabled but the domain
> blank, the server rejects every session and the client reports
> *"Server not found"* even though DNS resolution and IP connectivity are
> both perfect. This was a real defect in the original build â€” see
> [`../AUDIT-FINDINGS.md`](../../docs/AUDIT-FINDINGS.md) Â§C-01.

### Client configuration

| Field | `SALES-PC1` | `HR-PC1` |
|---|---|---|
| Your Name | Sales User | HR User |
| Email Address | `sales@company.com` | `hr@company.com` |
| Incoming Mail Server (POP3) | `mail.company.com` | `mail.company.com` |
| Outgoing Mail Server (SMTP) | `mail.company.com` | `mail.company.com` |
| Username | `sales` | `hr` |
| Password | `sales123` | `hr123` |

> The client must use the **hostname**, not the IP address. That forces the
> client to resolve `mail.company.com` through the centralised DNS server,
> which is what proves DNS and mail working together.

---

## `Server3` â€” Simulated Internet Server

| Property | Value |
|---|---|
| IP address | `203.0.113.10` |
| Subnet mask | `255.255.255.0` |
| Default gateway | `203.0.113.1` (the `ISP` router) |
| HTTP | enabled |
| Role | The "Internet" for the PAT demonstration |

`203.0.113.0/24` is the RFC 5737 TEST-NET-3 documentation range, so it can
never collide with a real network.

### Verify

```
SALES-PC1> ping 203.0.113.10
```

---

## Service matrix

| Service | Server | Enabled | Notes |
|---|---|---|---|
| HTTP | `Server0` | âœ… | Corporate portal |
| HTTPS | `Server0` | âœ… | Same content over TLS |
| DNS | `Server1` | âœ… | The only DNS server in the lab |
| SMTP | `Server2` | âœ… | Domain `company.com` |
| POP3 | `Server2` | âœ… | 3 mailboxes |
| HTTP | `Server3` | âœ… | Simulated Internet |
| FTP | all | âŒ | Disabled |
| TFTP | all | âŒ | Disabled |
| DHCP | all | âŒ | The only DHCP server is `core-01` |

