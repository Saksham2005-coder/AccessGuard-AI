# AccessGuard AI — Scanner Network Safety & Threat Model

## 1. Executive Summary

The AccessGuard AI web crawler and accessibility scanner inspects user-specified target web pages using headless Playwright Chromium. Because scanned URLs originate from tenant users and rendered pages may execute client-side JavaScript that triggers outbound subrequests, the scanner is inherently exposed to Server-Side Request Forgery (SSRF) and local network enumeration threats.

This document formalizes the threat vectors, multi-tier defense architecture, and operational constraints governing the scanner runtime.

---

## 2. Threat Vectors and Attack Scenarios

| Attack Vector | Attacker Objective | Risk Level |
|---|---|:---:|
| **Cloud Metadata Harvesting** | Access `169.254.169.254` (AWS/GCP/Azure) or `fd00:ec2::254` to steal temporary IAM credentials, service account tokens, or instance identity documents. | **CRITICAL** |
| **Local Service Enumeration** | Connect to internal databases, Redis instances, Celery queues, Docker sockets, or Kubernetes API endpoints located on localhost or RFC 1918 private subnets. | **CRITICAL** |
| **DNS Rebinding** | Configure a public domain name with a low TTL (0-1s) that initially resolves to a valid public IP (passing pre-navigation checks) and subsequently resolves to `127.0.0.1` when Playwright establishes connection. | **HIGH** |
| **Mixed DNS Answer Smuggling** | Register dual A/AAAA records where one record points to a public IP and the other points to an internal private IP (`10.0.0.1`), exploiting DNS resolver non-determinism. | **HIGH** |
| **HTTP Redirect Pivoting** | Point the crawler at an innocuous public URL that issues an HTTP 301/302 redirect targeting `http://169.254.169.254/latest/meta-data/` or internal admin panels. | **HIGH** |
| **Alternative IP Representations** | Use IPv4-mapped IPv6 notation (`::ffff:127.0.0.1`), octal (`0177.0.0.1`), hexadecimal (`0x7f000001`), or integer representations (`2130706433`) to bypass naive regex checks. | **MEDIUM** |
| **Dangerous Protocol Schemes** | Navigate to `file:///etc/passwd`, `data:`, `ftp:`, `javascript:`, or custom URI schemes to execute local code or access host filesystem resources. | **HIGH** |

---

## 3. Defense-in-Depth Architecture

AccessGuard AI mitigates scanner risks across five rigorous defense layers:

### Layer 1: URL Normalization & Protocol Constraints
- Standardized parsing using Python's `urllib.parse` engine.
- Only `http` and `https` schemes are accepted; `file:`, `data:`, `ftp:`, and `javascript:` URLs are rejected unconditionally.
- Embedded user credentials (`user:pass@host`) are strictly forbidden.
- Default ports (80 for HTTP, 443 for HTTPS) are normalized; arbitrary ports (e.g. 22, 5432, 6379, 8080) are rejected by default.

### Layer 2: Pre-Navigation DNS Resolution & IP Classification
- Every target hostname is pre-resolved using dnspython for both `A` and `AAAA` records with strict bounded network timeouts (3.0s).
- **All** returned IP addresses are parsed with Python's standard `ipaddress` library and classified before browser navigation commences.
- Targets are rejected if any returned address matches:
  - Loopback (`127.0.0.0/8`, `::1`)
  - Private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`)
  - Link-local subnets (`169.254.0.0/16`, `fe80::/10`)
  - Cloud provider metadata IPs (`169.254.169.254`, `fd00:ec2::254`, `100.100.100.200`)
  - Multicast (`224.0.0.0/4`, `ff00::/8`)
  - Reserved / Unspecified (`0.0.0.0/8`, `::`)
  - IPv4-mapped IPv6 encodings of any of the above.
- If a domain yields mixed public and private answers, the target is rejected in its entirety.

### Layer 3: Playwright Browser Hardening & Route Interception
- Headless Chromium operates in a sandboxed, unprivileged execution context without access to persistent profiles or host filesystem mounts.
- `context.route("**/*")` intercepts every outbound HTTP/HTTPS request, asset load, and subresource initiated by DOM scripts.
- Requests with forbidden schemes or IP literal destinations resolving to private subnets are aborted on the wire.
- Secondary popup tabs, downloads, and unexpected navigation windows are rejected immediately.

### Layer 4: Domain Ownership Verification Gate
- Prior to initiating scans, users must verify domain control by provisioning a 256-bit entropy DNS TXT record (`_accessguard-verification.<domain>`).
- Crawling is restricted to the verified root domain and approved subdomains; foreign domains and external cross-origin links are excluded from crawler queues.

### Layer 5: Network Egress & Environment Boundary
- **Production Safety Gate**: The `allow_loopback` setting is hard-gated in application code: if `APP_ENV=production`, attempting to enable loopback throws an uncatchable `PolicyViolationError`.
- For public cloud production deployments, container runners must be provisioned with outbound network firewall rules (or a dedicated egress proxy) blocking internal IP ranges at the hypervisor/VPC level.

---

## 4. Limitations and Operational Recommendations

> [!WARNING]
> DNS validation followed by browser navigation cannot completely eliminate DNS rebinding without kernel/network-level egress enforcement, because Chromium may re-resolve hostnames independently.

In production environments:
1. **Network Egress Firewall**: Enforce egress security group rules blocking TCP/UDP egress to RFC 1918 subnets and cloud metadata IPs from scanner runner nodes.
2. **Dedicated Worker Network**: Run Celery scan workers and Chromium containers on a separate isolated Docker / Kubernetes bridge network disconnected from internal PostgreSQL, Redis, and Qdrant clusters.
3. **No Ambient Credentials**: Never mount Kubernetes service account tokens, Docker sockets, or cloud provider IAM credentials into the scanner execution container.
