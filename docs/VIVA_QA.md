# Viva & Exam Preparation

Forty questions an examiner is likely to ask about this project, with model
answers. Read the **short answer** aloud in the first 30 seconds, then expand
only if the examiner asks for detail.

---

## Section 1 — The project in one paragraph

**Q1. Give me a one-minute summary of your project.**

> "I designed a multi-site enterprise network for a company with a head office
> and four remote branches. The head office runs a three-tier campus network —
> access, leaf and core — with two cores providing HSRP redundancy and a
> single centralised DHCP server. The central server VLAN hosts three servers:
> a web server, an authoritative DNS server and a mail server. All four
> branches are connected over an OSPF area 0 WAN with IPsec site-to-site VPN
> between the head office and each branch. Internet access for everybody is
> provided by a PAT edge router that translates every internal address to a
> single ISP-facing address."

---

## Section 2 — Centralised services

**Q2. What centralised server services did you implement?**

> "Three: DNS at 172.10.10.2, HTTP and HTTPS at 172.10.10.1, and email with
> SMTP and POP3 at 172.10.10.3. They live in Server VLAN 20, 172.10.10.0/24,
> and they are reachable from every site — the head office and all four
> branches — over the routed OSPF network."

**Q3. Why put the servers in a dedicated VLAN?**

> "Isolation and segmentation. The servers are the most critical asset in the
> company, so they get their own broadcast domain, their own subnet and their
> own gateway. It means a broadcast storm on a user VLAN can never reach
> them, and the security ACLs can treat server traffic differently from
> user traffic."

**Q4. How does a client know where the DNS server is?**

> "It does not need to be told. Every DHCP pool on the core includes
> `dns-server 172.10.10.2`, so the client receives the centralised DNS address
> together with its IP address and gateway. That is why the DNS field on the
> client is greyed out — it is controlled by the DHCP scope, not by hand."

**Q5. What is the difference between SMTP and POP3?**

> "SMTP — Simple Mail Transfer Protocol — sends mail. POP3 — Post Office
> Protocol version 3 — retrieves mail. In my lab a Sales user sends with SMTP
> to the central mail server, the server stores the message, and the HR user
> retrieves it with POP3."

**Q6. Why is `homelab.local` in the DNS zone?**

> "It is the self-record for the DNS server itself — it points at
> 172.10.10.2, which is the DNS server's own address. It is useful for
> troubleshooting: pinging `homelab.local` confirms the DNS service is
> answering and the zone is loaded."

---

## Section 3 — Routing and switching

**Q7. Why OSPF and not RIP?**

> "OSPF is a link-state protocol with a full view of the topology, fast
> convergence and authentication support. RIP would need the full 30-second
> hold-down before a failed link is removed, and its hop-count limit of 15
> would not scale. OSPF also lets me originate a default route with
> `default-information originate`, which is how the branches learn the
> Internet path."

**Q8. Why a single OSPF area?**

> "The WAN is only five routers in a star topology. A single flat area means
> every router has the same complete picture, convergence is fast, and there
> are no area-boundary summarisation rules to explain. With a larger network
> I would use areas and summarisation."

**Q9. What is HSRP and why do you need it?**

> "HSRP — Hot Standby Routing Protocol — lets two routers share one virtual
> default gateway for a VLAN. `core-01` has priority 110 and preempts, so it
> is active and `core-02` is standby. If `core-01` fails, `core-02` takes
> over the `.254` address and the clients keep working without changing their
> gateway."

**Q10. What is the role of the `standby preempt` command?**

> "Without preempt, a standby router only takes over when the active router
> fails. With preempt, the router with the higher priority takes the active
> role back as soon as it returns. That is what I want here, because
> `core-01` is also the DHCP server and I want it to be the active gateway
> whenever it is up."

**Q11. What are the leaf switches for?**

> "They are the layer-3 distribution tier for the access switches. Each leaf
> trunks VLANs 10, 11, 12 and 20 and connects to both cores, so an access
> switch is dual-homed and survives the loss of one core. The two leaves are
> also connected by an LACP port-channel so there is bandwidth and
> redundancy between them."

**Q12. Why is `portfast` configured on the access ports?**

> "Because a host port should never be a switch port. `spanning-tree
> portfast` puts the port straight into forwarding instead of waiting the
> full 30-second spanning-tree convergence. I pair it with `bpduguard` so
> that if someone plugs a switch into an access port the port is shut down
> rather than silently creating a loop."

**Q13. What does port-security do here?**

> "It pins exactly one MAC address per access port. I use
> `switchport port-security maximum 1` with `violation shutdown`, and a
> sticky MAC so the address is learned automatically. If an unauthorised
> device is connected, the port goes down instead of the switch being used
> for a MAC-flooding attack."

**Q14. What is the LACP port-channel between the leaves?**

> "Three physical links are bundled with `channel-group 1 mode active`, which
> is LACP in active mode. It gives more bandwidth between the leaves and,
> more importantly, redundancy — if one member link fails the port-channel
> keeps running over the other two."

---

## Section 4 — DHCP

**Q15. Where is the DHCP server and why there?**

> "On `core-01`, the HQ core. One central server for seven networks. It is
> the natural place because the core already holds the gateway for every
> user VLAN, and the design goal of the project is centralisation."

**Q16. How do the branches get an IP address if the DHCP server is in the HQ?**

> "With a DHCP relay. Each branch access switch has `ip helper-address
> 10.1.1.1`, which forwards the client's DHCP broadcast to the central
> server across the WAN. The server sees the relay's address and allocates
> a lease from the correct branch pool."

**Q17. What happens if `core-01` fails?**

> "The clients keep their existing leases for a while, but new leases stop.
> That is the trade-off of a single DHCP server. To reduce the risk,
> `core-02` has `ip helper-address 10.1.1.1` as well — but the pool itself
> only exists on `core-01`, so in a production build I would use DHCP
> failover, or move the pools to a dedicated server."

**Q18. Why did you exclude those addresses from the pools?**

> "Because a DHCP lease must never overlap an address that is already
> configured on the device. I exclude `.1` to `.20`, the two core SVI
> addresses `.252` and `.253`, and the HSRP address `.254`. In the original
> build `.252` and `.253` were not excluded, which meant DHCP could hand
> out an address that the core was using — that causes exactly the kind of
> intermittent failure that is very hard to diagnose."

---

## Section 5 — NAT and PAT

**Q19. What is the difference between NAT and PAT?**

> "NAT translates one private address to one public address. PAT — Port
> Address Translation, also called NAT overload — lets many internal
> sessions share a single public address by giving each session a different
> source port. In my lab `EDGE-RTR` does `ip nat inside source list 1
> interface GigabitEthernet0/1 overload`, so every internal host is
> represented outside by `200.1.1.1`."

**Q20. How do I prove the PAT is working?**

> "`show ip nat translations`. The inside-local column shows the many
> different internal addresses — `192.168.10.23`, `192.168.13.21`,
> `172.10.10.3` — while the inside-global column shows the same value
> `200.1.1.1` for all of them. Different inside-local addresses with one
> shared inside-global address is exactly what PAT looks like."

**Q21. Why do the branch users not need their own ISP connection?**

> "Because `core-01` originates a default route into OSPF with
> `default-information originate`. The branch learns `0.0.0.0/0` from the HQ
> over the WAN, sends its traffic to the head office, and the HQ edge router
> performs the translation. So the Internet path is: branch → HQ → EDGE-RTR →
> PAT → ISP."

**Q22. What is the `access-list 1` used for in NAT?**

> "It selects which inside networks are allowed to use the PAT pool. In my
> lab it permits all seven user networks plus the server VLAN. It is not a
> security control — the security controls are the named extended ACLs on
> the core."

---

## Section 6 — Security

**Q23. What security controls are in the lab?**

> "Five layers. Named extended ACLs on the core isolate the Sales, HR and
> Accounts departments from each other while still allowing DHCP. IPsec with
> AES and SHA-HMAC encrypts the branch traffic. Port-security and BPDU guard
> protect the access layer. HSRP provides gateway redundancy. And PAT hides
> the internal address space from the Internet."

**Q24. How does the Sales ACL work?**

> "`SALES-SECURITY` is applied inbound on `Vlan10`. The first line permits
> DHCP so leases and renewals still work, then it denies traffic from the
> Sales subnet to HR and to Accounts, and finally permits everything else —
> which is why Sales can reach the web server, the mail server and the
> Internet, but not another department."

**Q25. Why is the `permit udp any eq bootpc any eq bootps` line first?**

> "Because the explicit deny rules come after it in the list, and ACLs are
> evaluated top to bottom. If the deny came first it would block the DHCP
> traffic of the neighbouring department and those clients would end up with
> an address but no DNS server."

**Q26. What is IPsec and why is it used on the WAN?**

> "IPsec encrypts and authenticates the IP traffic that crosses an untrusted
> network. Here it protects the traffic between the HQ and each branch
> across the serial links. I use AES for encryption, SHA-HMAC for
> authentication, and pre-shared keys — one per branch, configured on both
> ends."

**Q27. What would you improve in production?**

> "The IKE group is 2, which is legacy and uses a small key size. I would
> move to group 14 and replace the shared pre-shared key with a strong
> random key, or better, move to IKEv2 with certificates. I would also add
> SSH with `transport input ssh`, syslog, and disable the unused services on
> the servers. These are documented in `docs/SECURITY.md`."

---

## Section 7 — The services in the field

**Q28. Walk me through what happens when a user opens the company website.**

> "Four steps. One — the client already has its IP, gateway and DNS server
> from DHCP. Two — the client asks the DNS server where `www.company.com` is
> and gets `172.10.10.1`. Three — OSPF gives the client the path to the
> server VLAN. Four — HTTP carries the request to the web server and the
> portal is returned."

**Q29. Walk me through the email flow.**

> "The user types `hr@company.com`. The client resolves `mail.company.com`
> through the central DNS server to `172.10.10.3`. SMTP sends the message to
> the central mail server, which stores it in the `hr` mailbox. On the HR
> side the client uses POP3 to log in as `hr` and download the message."

**Q30. How do you prove the services are centralised and not just local?**

> "I run the same tests from a branch. From `BR1-PC1` I ping
> `www.company.com` and `mail.company.com`, I open the portal in the web
> browser and I send an email to HR and receive the reply. Those services are
> physically in the head office server VLAN — if the branch can use them, the
> centralisation is real."

---

## Section 8 — Troubleshooting

**Q31. A client has an IP address but cannot reach the server. What do you check?**

> "I work bottom up. First, can it ping the gateway `192.168.x.254`? Then can
> it ping the server `172.10.10.1` by IP? If the IP works but the hostname
> does not, it is a DNS problem, not a routing problem. Then I check the
> DHCP lease with `ipconfig` to confirm the DNS server address was actually
> handed out."

**Q32. `ping www.company.com` says "could not find host". Where do you start?**

> "With `ping 172.10.10.2`. If that fails it is a connectivity problem. If it
> works, I check `ipconfig` on the client — if the DNS field is empty the
> DHCP pool is missing the `dns-server` line. If the DNS field is correct, I
> look at the DNS service on the server and the record itself, including a
> possible leading space in the record name."

**Q33. The email client says "server not found" but I can ping the mail server.**

> "Then it is not a network problem — I have already proved connectivity by
> IP. The classic cause in this project was that the mail server's `Domain
> Name` field was blank. With SMTP and POP3 enabled but no domain configured,
> the server rejects the session. You must set the domain to `company.com`
> and press Set."

---

## Section 9 — General networking questions

**Q34. What is the OSI model and where does each technology fit?**

> "Layer 1 — physical, the copper and serial cabling. Layer 2 — data link,
> Ethernet, VLANs, STP, LACP. Layer 3 — network, IP addressing, OSPF, NAT
> and PAT, and IPsec which works at layer 3. Layer 4 — transport, TCP and
> UDP, which is where the port numbers let PAT distinguish many sessions on
> one address. Layers 5 to 7 — the applications: DNS, HTTP, HTTPS, SMTP and
> POP3."

**Q35. What is a subnet mask and why `/24` everywhere?**

> "The mask tells the device which part of the address is the network part
> and which is the host part. `/24` means 255.255.255.0, so 254 usable host
> addresses per subnet. I use `/24` everywhere because the network is small
> and one subnet per department is the right granularity. The only exception
> is the ISP link at `/30`, which gives exactly two usable addresses — "
> "enough for a point-to-point link and nothing more."

**Q36. What is the difference between a switch and a router?**

> "A switch forwards frames using MAC addresses and works at layer 2. A
> router forwards packets using IP addresses and works at layer 3. My leaf
> and core switches are layer-3 switches — they route between VLANs — while
> the WAN routers and the edge router are dedicated routers."

**Q37. What is a default route?**

> "A route for `0.0.0.0/0` — the match-all. It is used when no more
> specific route exists. `core-01` has a static default to `10.3.3.2`, the
> edge router, and it originates that into OSPF so the branches inherit it."

**Q38. Explain `show ip nat translations` in detail.**

> "Four columns. **Inside local** is the original private address of the
> host — `192.168.10.23`. **Inside global** is the address the host is
> represented by on the inside of the NAT — `200.1.1.1`, the edge router's
> ISP-facing interface. **Outside local** is the destination as the router
> saw it. **Outside global** is the destination as the Internet sees it. The
> `icmp` is the protocol and the numbers are the port numbers, which is how
> PAT keeps the sessions apart."

---

## Section 10 — Rapid-fire one-liners

| Question | Answer |
|---|---|
| DHCP gives the client what? | IP address, mask, default gateway and DNS server |
| DNS translates what to what? | Hostname to IP address |
| HTTP vs HTTPS? | Same content, HTTPS adds TLS encryption |
| Which port does DNS use? | UDP and TCP 53 |
| Which port does SMTP use? | TCP 25 |
| Which port does POP3 use? | TCP 110 |
| Which port does HTTP use? | TCP 80 (HTTPS 443) |
| What is OSPF's administrative distance? | 110 for OSPF, so it beats a static default route of 1? No — a static route of 1 is preferred; that is why the edge router uses statics and the core uses OSPF for the internal networks |
| What is the STP default timer? | 15 seconds hello, 20 seconds forward delay, 30 seconds total convergence for a port |
| What does `ip routing` do on a switch? | Enables layer-3 switching so the switch can route between its SVIs |
| What is an SVI? | A logical layer-3 interface for a VLAN, `interface Vlan10` |
| What is the `ip helper-address`? | The DHCP relay address on a branch SVI |
| What is the purpose of `default-information originate`? | Makes OSPF advertise a default route into the area |
| How many IPsec tunnels? | Four, one per branch |
| Which interface is NAT inside? | `GigabitEthernet0/0`, the enterprise-facing side |
| Which interface is NAT outside? | `GigabitEthernet0/1`, the ISP-facing side |
| What is the private address range? | `10.0.0.0/8`, `172.16.0.0/12` and `192.168.0.0/16` |

---

## Section 11 — Closing statement

**Q39. What would you do next with this design?**

> "Three things. First, add DHCP failover between the two cores so a core
> failure does not stop new leases. Second, replace the pre-shared keys and
> move the IKE policy to a modern Diffie-Hellman group, or move to IKEv2 with
> certificates. Third, add a second ISP with BGP so the default route is
> resilient instead of depending on a single static default."

**Q40. What did you learn from this project?**

> "That the hard part of networking is not the configuration commands — it is
> the consistency between them. The mail client had the wrong domain, the
> DHCP pool could hand out an address that belonged to a core interface, two
> DNS servers disagreed, and nine devices shared the same hostname. None of
> those are visible in a screenshot of the topology; they only show up when
> you actually run the tests, which is why I automated the audit in this
> repository."
