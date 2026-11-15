Centralized Enterprise Server Services - DNS, HTTP/HTTPS and Email
Overview
The enterprise network contains a dedicated Server VLAN for centralized services.

Server VLAN information:

Network: 172.10.10.0/24
Default Gateway: 172.10.10.254
VLAN: VLAN 20
Three separate servers are used:

Server0: 172.10.10.1 → HTTP/HTTPS Web Server
Server1: 172.10.10.2 → DNS Server
Server2: 172.10.10.3 → Email Server
All servers use:

Subnet Mask: 255.255.255.0
Default Gateway: 172.10.10.254
The purpose of this design is to provide centralized application services to the headquarters and all remote branch sites.

Easy way to remember the services:

DHCP = Gives IP configuration to clients
DNS = Converts names into IP addresses
HTTP/HTTPS = Provides the company website
SMTP = Sends email
POP3 = Receives email
OSPF = Provides the route between networks/sites
ACL = Controls which traffic is allowed or denied

1. DNS Server
The DNS Server is:

IP Address: 172.10.10.2
Subnet Mask: 255.255.255.0
Default Gateway: 172.10.10.254
DNS stands for Domain Name System.

The main purpose of DNS is to translate an easy-to-remember hostname/domain name into an IP address.

For example:

www.company.com → 172.10.10.1

mail.company.com → 172.10.10.3

Therefore, users do not need to remember the IP addresses of all company servers.

Instead of typing:

172.10.10.1

the user can use:

www.company.com

Similarly, instead of remembering:

172.10.10.3

the Email client can use:

mail.company.com

2. DNS Server Configuration
In Cisco Packet Tracer:

Server1 → Services → DNS

DNS Service was turned ON.

The following DNS A records were added:

Record 1:

Name: www.company.com

Type: A Record

Address: 172.10.10.1

Record 2:

Name: mail.company.com

Type: A Record

Address: 172.10.10.3

Therefore:

www.company.com → 172.10.10.1 → HTTP Server

mail.company.com → 172.10.10.3 → Email Server

3. DNS Integration with DHCP
All user PCs in the enterprise network receive their IP configuration automatically through DHCP.

Because the PCs use DHCP, the DNS Server address is also distributed automatically through the DHCP pools.

The centralized DNS Server address is:

172.10.10.2

Example configuration on core01:

enable
configure terminal

ip dhcp pool SALES
dns-server 172.10.10.2
exit

ip dhcp pool HR
dns-server 172.10.10.2
exit

ip dhcp pool ACCOUNTS
dns-server 172.10.10.2
exit

ip dhcp pool BRANCH1
dns-server 172.10.10.2
exit

ip dhcp pool BRANCH2
dns-server 172.10.10.2
exit

ip dhcp pool BRANCH3
dns-server 172.10.10.2
exit

ip dhcp pool BRANCH4
dns-server 172.10.10.2
exit

end
A DHCP client therefore receives:

IP Address
Subnet Mask
Default Gateway
DNS Server
For example, a Sales PC can receive:

IP Address: 192.168.10.x

Subnet Mask: 255.255.255.0

Default Gateway: 192.168.10.254

DNS Server: 172.10.10.2

This means DNS information does not have to be manually configured on every client PC.

4. DNS Testing
DNS can be tested from any Headquarters or Branch PC.

Command:

ping www.company.com
Successful output resolves the name to:

172.10.10.1

Example:

Pinging 172.10.10.1 with 32 bytes of data:
Reply from 172.10.10.1
Reply from 172.10.10.1
Reply from 172.10.10.1
Reply from 172.10.10.1
This proves:

www.company.com → DNS Server → 172.10.10.1

Mail DNS can be tested with:

ping mail.company.com
Successful output resolves:

mail.company.com → 172.10.10.3

Example:

Pinging 172.10.10.3 with 32 bytes of data:
Reply from 172.10.10.3
Reply from 172.10.10.3
Reply from 172.10.10.3
Reply from 172.10.10.3
This proves that the Email Server DNS record is also working.

5. HTTP/HTTPS Web Server
The Web Server is:

Server: Server0
IP Address: 172.10.10.1
Subnet Mask: 255.255.255.0
Default Gateway: 172.10.10.254
DNS Name: www.company.com
The purpose of this server is to host the centralized company website or internal enterprise portal.

6. HTTP Server Configuration
In Cisco Packet Tracer:

Server0 → Services → HTTP

The following services were enabled:

HTTP: ON

HTTPS: ON

The server hosts the default index.html webpage.

The default webpage can later be replaced with a customized company webpage.

7. HTTP Server Testing
From a client PC:

Desktop → Web Browser

Enter:

http://www.company.com

The communication process is:

PC → asks DNS Server for www.company.com → DNS Server 172.10.10.2 responds with 172.10.10.1 → PC connects to 172.10.10.1 → HTTP Server sends the webpage → Website opens successfully

Therefore:

DNS = Finds the server

HTTP = Provides the webpage

The same test can be performed from a remote Branch PC:

http://www.company.com

If the webpage opens successfully from a remote branch, it also proves that the centralized Web Server is accessible across the multi-site OSPF network.

8. Email Server
The Email Server is:

Server: Server2
IP Address: 172.10.10.3
Subnet Mask: 255.255.255.0
Default Gateway: 172.10.10.254
DNS Name: mail.company.com
Email Domain: company.com
The Email Server provides centralized internal company email communication.

9. SMTP and POP3
The Email Server uses SMTP and POP3.

SMTP stands for Simple Mail Transfer Protocol.

SMTP is used to SEND email.

Easy way to remember:

SMTP = SEND

Example:

Sales PC → SMTP → Email Server

POP3 stands for Post Office Protocol version 3.

POP3 is used by the Email client to RECEIVE/RETRIEVE emails from the Email Server.

Easy way to remember:

POP3 = RECEIVE

Example:

Email Server → POP3 → HR PC

Therefore:

SMTP = Send Email

POP3 = Receive Email

10. Email Server Configuration
In Cisco Packet Tracer:

Server2 → Services → EMAIL

The following services were enabled:

SMTP Service: ON

POP3 Service: ON

The Email domain was configured as:

company.com

After typing company.com, the Set button was used to apply the Email domain.

11. Email User Accounts
User accounts were created on the Email Server.

Example Sales account:

Username: sales

Password: sales123

Therefore the complete Sales email address is:

sales@company.com

Example HR account:

Username: hr

Password: hr123

Therefore the complete HR email address is:

hr@company.com

The email address format is:

username@domain

Therefore:

sales + @ + company.com

becomes:

sales@company.com

12. Email DNS Configuration
The centralized DNS Server contains:

mail.company.com → 172.10.10.3

Therefore, when an Email client is configured with:

Incoming Mail Server: mail.company.com

Outgoing Mail Server: mail.company.com

the PC first asks the DNS Server:

"Where is mail.company.com?"

DNS Server 172.10.10.2 responds:

172.10.10.3

The PC then communicates with the Email Server at:

172.10.10.3

13. Sales Email Client Configuration
On the Sales PC:

Desktop → Email

Configuration:

Your Name: Sales User

Email Address: sales@company.com

Incoming Mail Server: mail.company.com

Outgoing Mail Server: mail.company.com

Username: sales

Password: sales123

Then the configuration is saved.

14. HR Email Client Configuration
On the HR PC:

Desktop → Email

Configuration:

Your Name: HR User

Email Address: hr@company.com

Incoming Mail Server: mail.company.com

Outgoing Mail Server: mail.company.com

Username: hr

Password: hr123

Then the configuration is saved.

15. Email Send/Receive Test
A test Email was sent from Sales to HR.

Sender:

sales@company.com

Receiver:

hr@company.com

Example:

To: hr@company.com

Subject: Email Server Test

Message:

Hello HR, This is a test email from the Sales department.

The Send button was used.

The Email flow is:

sales@company.com → SMTP → mail.company.com → DNS resolves mail.company.com → 172.10.10.3 → Email Server → message stored for HR → HR uses POP3 → hr@company.com receives the message

On the HR PC:

Desktop → Email → Receive/Get Mail

The email was successfully received.

A reverse test can also be performed:

hr@company.com → sales@company.com

This demonstrates bidirectional company email communication.

16. Complete Server Architecture
The final centralized Server VLAN design is:

                Server VLAN 20
                172.10.10.0/24
                       |
              Gateway 172.10.10.254
                       |
         --------------------------------
         |              |               |
         |              |               |
   172.10.10.1    172.10.10.2     172.10.10.3
    WEB SERVER      DNS SERVER       EMAIL SERVER
         |              |               |
    HTTP/HTTPS       DNS Records       SMTP/POP3
                        |
         --------------------------------
         |                              |
  www.company.com                mail.company.com
   172.10.10.1                    172.10.10.3
Easy summary:

172.10.10.1 = Website

172.10.10.2 = DNS / Name-to-IP translation

172.10.10.3 = Email

17. How All Services Work Together
Example 1: User opens the website

The user types:

www.company.com

The process is:

PC → DNS Server 172.10.10.2 → DNS says www.company.com = 172.10.10.1 → OSPF provides the route to Server VLAN → PC connects to Web Server 172.10.10.1 → HTTP Server provides the website

Therefore several technologies work together:

DHCP → Configures the PC

DNS → Finds the server IP

OSPF → Finds the network path

ACL → Controls whether traffic is permitted

HTTP → Provides the website

Example 2: User sends Email

Sales sends email to:

hr@company.com

The process is:

Sales PC → mail.company.com → DNS Server translates mail.company.com to 172.10.10.3 → OSPF routes the traffic → SMTP sends the Email to Server2 → Email Server stores the Email → HR PC uses POP3 to retrieve the Email

Therefore:

DNS → Finds Email Server

OSPF → Provides path

SMTP → Sends Email

POP3 → Receives Email

18. Important Troubleshooting Performed
Problem 1: DNS field on PC could not be edited
The PCs were configured as DHCP clients.

Therefore the DNS field was automatically controlled by DHCP and could not be manually edited normally.

Solution:

The DNS Server address was added to the DHCP pools:

dns-server 172.10.10.2
After the DHCP configuration was refreshed, the PC received:

DNS Server: 172.10.10.2

Problem 2: mail.company.com could not be resolved
Symptom:

Ping request could not find host mail.company.com.
First, direct connectivity to the DNS Server was tested:

ping 172.10.10.2
The ping succeeded.

Therefore:

Network connectivity = Working

DNS resolution = Problem

The DNS record was checked and recreated:

mail.company.com → 172.10.10.3

After that:

ping mail.company.com
resolved to:

172.10.10.3

and successfully received replies.

Problem 3: Email showed "Server not found"
DNS resolution and IP connectivity were already working.

The Email Server configuration was checked.

The following problem was discovered:

Domain Name field = Blank

The Email domain was then configured:

company.com

and the Set button was clicked.

After configuring:

Domain Name = company.com

the Email service worked successfully.

Therefore the root cause was not OSPF, VLAN, DHCP or DNS.

The missing Email Server domain was the problem.

19. How to Demonstrate DNS to the Examiner
If the examiner asks:

"Show me that DNS is working."

From any Sales, HR, Accounts or Branch PC:

ping www.company.com
Show that the PC automatically resolves:

www.company.com → 172.10.10.1

Then:

ping mail.company.com
Show:

mail.company.com → 172.10.10.3

Explain:

"Sir, I am not pinging the server IP directly. The client sends the company hostname to the centralized DNS server at 172.10.10.2. DNS then returns the correct server IP."

20. How to Demonstrate HTTP to the Examiner
Open a client PC:

Desktop → Web Browser

Enter:

http://www.company.com

When the webpage opens, explain:

"Sir, the client first uses DNS to resolve www.company.com to 172.10.10.1. After receiving the IP address, the client sends an HTTP request to the centralized Web Server."

21. How to Demonstrate Email to the Examiner
Open Sales PC:

Desktop → Email

Send:

From: sales@company.com

To: hr@company.com

Then open HR PC:

Desktop → Email → Get Mail/Receive

Show the received message.

Explain:

"Sir, SMTP is responsible for sending the email to the centralized Email Server, and POP3 is used by the HR client to retrieve the email from the server."

For an even stronger demonstration, reply from:

hr@company.com

to:

sales@company.com

22. How to Prove This Is a Multi-Site Centralized Service
Perform the same tests from a Branch PC.

DNS:

ping www.company.com
Mail:

ping mail.company.com
Web Browser:

http://www.company.com

If the remote branch can reach these centralized services, explain:

"Sir, the Web, DNS and Email services are centrally hosted in the headquarters Server VLAN. Remote branch/country networks reach these centralized services through the routed WAN network using OSPF."

This proves that the project is not only a local VLAN project.

The project contains centralized services that are available across multiple routed sites.

23. How to Show DHCP and DNS Integration
On core01:

show ip dhcp binding
This shows that clients are receiving addresses from the centralized DHCP service.

Then open a client:

Desktop → IP Configuration

Show:

IP Address: 192.168.x.x

Default Gateway: 192.168.x.254

DNS Server: 172.10.10.2

Explain:

"Sir, I do not manually configure DNS on every user PC. The centralized DHCP service automatically provides the DNS server address to the clients."

24. Viva Quick Memory Notes
Remember the following:

DHCP = Gives client configuration

DNS = Name to IP

OSPF = Finds network path

ACL = Allows or blocks traffic

HTTP = Website

SMTP = Send Email

POP3 = Receive Email

Another easy way:

DHCP asks:

"What is my IP configuration?"

DNS asks:

"Where is the server?"

OSPF asks:

"How do I reach that network?"

ACL asks:

"Am I allowed to go there?"

HTTP asks:

"Give me the website."

SMTP says:

"Send my mail."

POP3 says:

"Give me my mail."

25. Viva Answer
If the examiner asks:

"What centralized server services did you implement?"

Answer:

"I implemented centralized DNS, HTTP/HTTPS and Email services in the Server VLAN. The DNS Server at 172.10.10.2 resolves company domain names to server IP addresses. The Web Server at 172.10.10.1 hosts the company website and is accessible using www.company.com. The Email Server at 172.10.10.3 provides company email using SMTP for sending and POP3 for receiving. Client devices automatically receive the centralized DNS Server address through DHCP, and remote branches can access these services through OSPF routing."

26. Final Verification Checklist
DNS Server:

172.10.10.2 reachable
DNS Service ON
www.company.com → 172.10.10.1
mail.company.com → 172.10.10.3
HTTP Server:

172.10.10.1 reachable
HTTP ON
HTTPS ON
http://www.company.com opens successfully
Email Server:

172.10.10.3 reachable
SMTP ON
POP3 ON
Domain = company.com
sales user exists
hr user exists
DHCP:

Clients receive DNS = 172.10.10.2
DNS Test:

ping www.company.com
ping mail.company.com
HTTP Test:

http://www.company.com
Email Test:

sales@company.com → hr@company.com
Reverse Email Test:

hr@company.com → sales@company.com
Remote Site Test:

Run DNS, HTTP and Email tests from a Branch PC to demonstrate centralized multi-site enterprise services.
