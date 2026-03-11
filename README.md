# WIFI SCAN – Network Security Auditor

**Developed by @ghvstprogrammer on X/Twitter**  

A Python-based educational and defensive network security tool. Designed to scan Wi-Fi networks, analyze router security, and monitor connected devices — all in a safe, ethical manner.  

> ⚠️ **Warning:** This tool is for educational purposes only. It does not crack Wi-Fi passwords or exploit networks. Only use it on networks you own or have permission to audit.

---

## Features

### 1. Scan Wi-Fi Networks
- Detects nearby Wi-Fi networks using Linux `nmcli`.
- Displays:
  - SSID
  - Signal strength
  - Channel
  - Security type (WPA3, WPA2, WPA, WEP, Open)
- Classifies encryption strength: Strong, Moderate, Weak, Very Weak, Open
- Displays signal exposure risk: Low, Medium, High

### 2. Analyze Selected Network
- Select a network and view a detailed report:
  - SSID
  - Encryption type
  - Signal strength
  - Exposure risk
  - Channel

### 3. Router & Network Analysis
- Detects router (default gateway) IP automatically.
- Scans router for open ports using `nmap`.
- Identifies connected devices via ARP.
- Inspects DNS configuration (`/etc/resolv.conf`).

### 4. Security Score
- Generates a Wi-Fi security score (0–10) based on:
  - Encryption type
  - Router detection
  - Network configuration indicators

### 5. Security Recommendations
- Use WPA3 encryption
- Use strong Wi-Fi passwords (14+ characters)
- Disable WPS
- Change default router credentials
- Update firmware regularly
- Monitor unknown devices
- Use guest networks for visitors

### 6. Hacker-style Terminal UI
- ASCII banner at launch
- Colorful terminal text (ANSI codes)
- Menu-driven interface with animations
- Professional layout for demo purposes

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ghvstprogrammer/wifi-scan.git
cd wifi-scan

Usage

Run the tool:

python3 wifi_scan.py

Menu Options

Scan Wi-Fi Networks

Analyze Selected Network

Discover Connected Devices

Scan Router Ports

Check DNS

Generate Security Score

View Security Recommendations

Exit

If no wireless interface is detected, the tool will still allow router and LAN analysis via Ethernet.

Requirements

Linux environment (Kali, Ubuntu, Debian recommended)

Python 3

nmcli (NetworkManager CLI)

nmap

Optional: USB Wi-Fi adapter for real wireless scanning

Cannot scan Wi-Fi networks without a wireless interface (wlan0). Ethernet (eth0) supports only LAN and router analysis.

Contributing

Fork the repository

Create a branch for your feature: git checkout -b feature-name

Commit your changes: git commit -m "Add feature"

Push: git push origin feature-name

Open a Pull Request

License

MIT License © 2026 @ghvstprogrammer

Notes

Designed for educational and ethical use only

Tested on Kali Linux 2025.2 and Ubuntu 24.04
Best paired with a USB Wi-Fi adapter in VMware for real network scanning
