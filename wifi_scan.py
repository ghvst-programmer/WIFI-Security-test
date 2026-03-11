#!/usr/bin/env python3
# =============================================================================
# WIFI SCAN - Defensive WiFi Auditing & Monitoring Tool
# Developer: @ghvstprogrammer on X/Twitter
# =============================================================================
#
# PURPOSE:
#   A defensive WiFi auditing and monitoring tool for cybersecurity awareness
#   and educational purposes. Does NOT exploit networks or crack passwords.
#
# REQUIRED SYSTEM DEPENDENCIES (Linux):
#   - nmcli       : NetworkManager CLI for WiFi scanning
#   - arp         : ARP table lookup (net-tools package)
#   - ip          : IP routing info (iproute2 package)
#   - nmap        : Port scanning (nmap package)
#
# INSTALL DEPENDENCIES:
#   sudo apt install network-manager net-tools iproute2 nmap
#
# USAGE:
#   sudo python3 wifi_scan.py
#   (Some features require root/sudo privileges)
#
# =============================================================================

import os
import sys
import time
import subprocess
import threading
import random
import re
import socket
from datetime import datetime

# =============================================================================
# ANSI COLOR CODES
# =============================================================================

class C:
    """Terminal color constants using ANSI escape codes."""
    RESET     = '\033[0m'
    BOLD      = '\033[1m'
    DIM       = '\033[2m'

    BLACK     = '\033[30m'
    RED       = '\033[31m'
    GREEN     = '\033[32m'
    YELLOW    = '\033[33m'
    BLUE      = '\033[34m'
    MAGENTA   = '\033[35m'
    CYAN      = '\033[36m'
    WHITE     = '\033[37m'

    BBLACK    = '\033[90m'
    BRED      = '\033[91m'
    BGREEN    = '\033[92m'
    BYELLOW   = '\033[93m'
    BBLUE     = '\033[94m'
    BMAGENTA  = '\033[95m'
    BCYAN     = '\033[96m'
    BWHITE    = '\033[97m'

    BG_BLACK  = '\033[40m'
    BG_GREEN  = '\033[42m'
    BG_RED    = '\033[41m'
    BG_BLUE   = '\033[44m'

# =============================================================================
# GLOBAL STATE
# =============================================================================

scanned_networks  = []   # List of dicts from last WiFi scan
gateway_ip        = None # Detected default gateway
security_score    = 0    # Running security score

# =============================================================================
# UTILITY HELPERS
# =============================================================================

def clear():
    """Clear terminal screen."""
    os.system('clear')

def run_cmd(cmd, timeout=15):
    """Run a shell command and return (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return '', 'Command timed out', 1
    except Exception as e:
        return '', str(e), 1

def check_root():
    """Return True if running as root."""
    return os.geteuid() == 0

def separator(char='─', width=70, color=C.BBLACK):
    """Print a horizontal separator line."""
    print(f"{color}{char * width}{C.RESET}")

def section_header(title, color=C.BCYAN):
    """Print a formatted section header."""
    separator()
    pad = (68 - len(title)) // 2
    print(f"{C.BBLACK}│{C.RESET}{' ' * pad}{color}{C.BOLD}{title}{C.RESET}{' ' * pad}{C.BBLACK}│{C.RESET}")
    separator()

# =============================================================================
# LOADING / SCANNING ANIMATIONS
# =============================================================================

_anim_stop = False

def _spinner_worker(msg, color):
    """Worker thread for spinner animation."""
    frames = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
    idx = 0
    while not _anim_stop:
        print(f"\r  {color}{frames[idx]}{C.RESET}  {msg}   ", end='', flush=True)
        idx = (idx + 1) % len(frames)
        time.sleep(0.08)

def start_spinner(msg="Scanning...", color=C.BGREEN):
    """Start a spinner animation in background thread."""
    global _anim_stop
    _anim_stop = False
    t = threading.Thread(target=_spinner_worker, args=(msg, color), daemon=True)
    t.start()
    return t

def stop_spinner(t=None):
    """Stop the spinner animation."""
    global _anim_stop
    _anim_stop = True
    time.sleep(0.15)
    print('\r' + ' ' * 60 + '\r', end='', flush=True)

def scan_animation(label="Scanning", color=C.BGREEN, steps=20, delay=0.05):
    """Display a progress bar scanning animation."""
    print()
    for i in range(steps + 1):
        pct   = int((i / steps) * 100)
        filled = int((i / steps) * 40)
        bar   = '█' * filled + '░' * (40 - filled)
        print(f"\r  {color}{label}  [{bar}] {pct:3d}%{C.RESET}", end='', flush=True)
        time.sleep(delay)
    print()

def glitch_text(text, color=C.BGREEN):
    """Print text with a brief glitch effect."""
    chars = '!@#$%^&*<>?/|\\~'
    for _ in range(3):
        scrambled = ''.join(random.choice(chars) if random.random() < 0.4 else c for c in text)
        print(f"\r  {C.BBLACK}{scrambled}{C.RESET}", end='', flush=True)
        time.sleep(0.07)
    print(f"\r  {color}{C.BOLD}{text}{C.RESET}      ")

# =============================================================================
# ASCII BANNER
# =============================================================================

BANNER = r"""
 ██╗    ██╗██╗███████╗██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗
 ██║    ██║██║██╔════╝██║    ██╔════╝██╔════╝██╔══██╗████╗  ██║
 ██║ █╗ ██║██║█████╗  ██║    ███████╗██║     ███████║██╔██╗ ██║
 ██║███╗██║██║██╔══╝  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║
 ╚███╔███╔╝██║██║     ██║    ███████║╚██████╗██║  ██║██║ ╚████║
  ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
"""

def print_banner():
    """Print the styled ASCII banner."""
    clear()
    print()
    # Gradient-style banner (green → cyan)
    lines = BANNER.strip('\n').split('\n')
    gradient = [C.GREEN, C.BGREEN, C.BGREEN, C.BCYAN, C.BCYAN, C.CYAN]
    for i, line in enumerate(lines):
        color = gradient[i % len(gradient)]
        print(f"  {color}{C.BOLD}{line}{C.RESET}")

    print()
    glitch_text("developed by @ghvstprogrammer on x/twitter", C.BMAGENTA)
    print()

    ts = datetime.now().strftime('%Y-%m-%d  %H:%M:%S')
    root_status = (f"{C.BGREEN}ROOT ✔{C.RESET}" if check_root()
                   else f"{C.BRED}NOT ROOT ✘{C.RESET}")
    host = socket.gethostname()

    separator('═', color=C.BBLACK)
    print(f"  {C.BBLACK}[{C.BCYAN}HOST{C.BBLACK}]{C.RESET}  {C.BWHITE}{host:<20}{C.RESET}  "
          f"{C.BBLACK}[{C.BCYAN}TIME{C.BBLACK}]{C.RESET}  {C.BWHITE}{ts:<20}{C.RESET}  "
          f"{C.BBLACK}[{C.BCYAN}PRIV{C.BBLACK}]{C.RESET}  {root_status}")
    separator('═', color=C.BBLACK)
    print()

# =============================================================================
# MAIN MENU
# =============================================================================

MENU_ITEMS = [
    ("1", "Scan WiFi Networks"),
    ("2", "Analyze Selected Network"),
    ("3", "Monitor Connected Devices"),
    ("4", "Scan Router Ports"),
    ("5", "DNS Inspection"),
    ("6", "WiFi Security Score"),
    ("7", "Security Recommendations"),
    ("8", "Exit"),
]

def print_menu():
    """Print the main menu."""
    print(f"  {C.BCYAN}{C.BOLD}MAIN MENU{C.RESET}")
    separator('─')
    for key, label in MENU_ITEMS:
        bullet = f"{C.BG_BLACK}{C.BGREEN} {key} {C.RESET}"
        print(f"  {bullet}  {C.BWHITE}{label}{C.RESET}")
    separator('─')
    print()

def get_choice(prompt="  Select option: ", valid=None):
    """Read a menu choice from user."""
    while True:
        try:
            val = input(f"{C.BYELLOW}{prompt}{C.RESET}").strip()
            if valid is None or val in valid:
                return val
            print(f"  {C.BRED}Invalid choice. Try again.{C.RESET}")
        except (KeyboardInterrupt, EOFError):
            print()
            return '8'

# =============================================================================
# FEATURE 1 — WIFI NETWORK SCANNER
# =============================================================================

def classify_security(sec):
    """Return (rating_label, color) for an encryption type string."""
    s = sec.upper()
    if 'WPA3' in s:
        return 'STRONG',    C.BGREEN
    elif 'WPA2' in s:
        return 'MODERATE',  C.BYELLOW
    elif 'WPA' in s:
        return 'WEAK',      C.BYELLOW
    elif 'WEP' in s:
        return 'VERY WEAK', C.BRED
    elif s in ('OPEN', 'NONE', '--', ''):
        return 'CRITICAL',  C.BRED
    else:
        return 'UNKNOWN',   C.BBLACK

def signal_to_percent(signal_str):
    """Convert nmcli signal strength (0-100) to int, or parse dBm."""
    try:
        val = int(signal_str)
        if val < 0:          # dBm value
            val = max(0, min(100, 2 * (val + 100)))
        return val
    except (ValueError, TypeError):
        return 0

def classify_exposure(pct):
    """Return (label, color) for signal exposure."""
    if pct >= 80:
        return 'HIGH',   C.BRED
    elif pct >= 50:
        return 'MEDIUM', C.BYELLOW
    else:
        return 'LOW',    C.BGREEN

def scan_wifi_networks():
    """Scan nearby WiFi networks using nmcli."""
    global scanned_networks
    section_header("WIFI NETWORK SCANNER")

    if not check_root():
        print(f"  {C.BYELLOW}⚠  Some details may be limited without root privileges.{C.RESET}")

    print(f"  {C.BBLUE}Initiating passive WiFi scan via nmcli...{C.RESET}")
    scan_animation("Scanning airspace", C.BGREEN, steps=25, delay=0.04)

    # Rescan trigger (best-effort)
    run_cmd("nmcli dev wifi rescan 2>/dev/null", timeout=10)
    time.sleep(1.5)

    # Pull fields: SSID, signal, chan, security
    stdout, stderr, rc = run_cmd(
        "nmcli -t -f SSID,SIGNAL,CHAN,SECURITY dev wifi list 2>/dev/null"
    )

    networks = []
    if rc != 0 or not stdout:
        # Fallback: try iwlist
        stdout2, _, rc2 = run_cmd("iwlist scanning 2>/dev/null")
        if rc2 == 0 and stdout2:
            networks = _parse_iwlist(stdout2)
        else:
            print(f"  {C.BRED}✘  Unable to scan. Ensure nmcli / wireless tools are installed{C.RESET}")
            print(f"     {C.BBLACK}and a wireless interface is active.{C.RESET}")
            _press_any_key()
            return
    else:
        networks = _parse_nmcli(stdout)

    if not networks:
        print(f"  {C.BYELLOW}No networks found. Check wireless interface.{C.RESET}")
        _press_any_key()
        return

    scanned_networks = networks

    # ── Table header ──────────────────────────────────────────────────────────
    col_ssid = 28
    col_sig  = 8
    col_chan = 6
    col_sec  = 18
    col_rate = 12
    col_exp  = 10

    def th(txt, w): return f"{C.BCYAN}{C.BOLD}{txt:<{w}}{C.RESET}"

    print()
    print(f"  {th('SSID', col_ssid)}{th('SIG%', col_sig)}{th('CH', col_chan)}"
          f"{th('SECURITY', col_sec)}{th('RATING', col_rate)}{th('EXPOSURE', col_exp)}")
    separator()

    for net in networks:
        ssid     = (net['ssid'][:col_ssid-2] + '..') if len(net['ssid']) > col_ssid - 1 else net['ssid']
        sig_pct  = net['signal']
        chan     = net['channel']
        sec      = net['security'] or 'OPEN'
        rating, r_color = classify_security(sec)
        exp_lbl, e_color = classify_exposure(sig_pct)

        sig_bar = _signal_bar(sig_pct)
        print(f"  {C.BWHITE}{ssid:<{col_ssid}}{C.RESET}"
              f"{sig_bar} {sig_pct:>2}%  "
              f"{C.BWHITE}{str(chan):<{col_chan}}{C.RESET}"
              f"{C.BWHITE}{sec:<{col_sec}}{C.RESET}"
              f"{r_color}{rating:<{col_rate}}{C.RESET}"
              f"{e_color}{exp_lbl:<{col_exp}}{C.RESET}")

    separator()
    print(f"  {C.BBLACK}Found {C.BWHITE}{len(networks)}{C.BBLACK} networks  │  "
          f"{C.BGREEN}■{C.BBLACK} STRONG  "
          f"{C.BYELLOW}■{C.BBLACK} WEAK  "
          f"{C.BRED}■{C.BBLACK} CRITICAL{C.RESET}")
    print()
    _press_any_key()

def _signal_bar(pct):
    """Return a short colored signal bar string."""
    bars = int(pct / 20)
    if pct >= 80:   color = C.BGREEN
    elif pct >= 50: color = C.BYELLOW
    else:           color = C.BRED
    return f"{color}{'▓' * bars}{'░' * (5 - bars)}{C.RESET}"

def _parse_nmcli(raw):
    """Parse nmcli -t output into list of dicts."""
    nets = []
    seen = set()
    for line in raw.splitlines():
        parts = line.split(':')
        if len(parts) < 4:
            continue
        ssid     = parts[0].strip()
        signal   = signal_to_percent(parts[1].strip())
        channel  = parts[2].strip()
        security = ':'.join(parts[3:]).strip()
        if not ssid or ssid in seen:
            continue
        seen.add(ssid)
        nets.append({'ssid': ssid, 'signal': signal,
                     'channel': channel, 'security': security})
    return nets

def _parse_iwlist(raw):
    """Minimal iwlist parse fallback."""
    nets = []
    current = {}
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith('Cell '):
            if current.get('ssid'):
                nets.append(current)
            current = {'ssid': '', 'signal': 0, 'channel': '?', 'security': 'UNKNOWN'}
        elif 'ESSID:' in line:
            m = re.search(r'ESSID:"(.*?)"', line)
            current['ssid'] = m.group(1) if m else ''
        elif 'Signal level=' in line:
            m = re.search(r'Signal level=(-?\d+)', line)
            if m:
                current['signal'] = signal_to_percent(m.group(1))
        elif 'Channel:' in line:
            m = re.search(r'Channel:(\d+)', line)
            if m:
                current['channel'] = m.group(1)
        elif 'Encryption key:' in line:
            current['security'] = 'WPA' if 'on' in line.lower() else 'OPEN'
    if current.get('ssid'):
        nets.append(current)
    return nets

# =============================================================================
# FEATURE 2 — ANALYZE SELECTED NETWORK
# =============================================================================

def analyze_network():
    """Display detailed analysis for a user-selected network."""
    section_header("ANALYZE SELECTED NETWORK")

    if not scanned_networks:
        print(f"  {C.BYELLOW}⚠  No networks scanned yet. Run option 1 first.{C.RESET}")
        _press_any_key()
        return

    print(f"  {C.BCYAN}Available networks:{C.RESET}")
    print()
    for i, net in enumerate(scanned_networks, 1):
        print(f"  {C.BGREEN}[{i:>2}]{C.RESET}  {C.BWHITE}{net['ssid']}{C.RESET}")
    print()

    choices = [str(i) for i in range(1, len(scanned_networks) + 1)]
    idx_str = get_choice("  Select network number: ", choices)
    net = scanned_networks[int(idx_str) - 1]

    sec     = net['security'] or 'OPEN'
    rating, r_color = classify_security(sec)
    sig_pct = net['signal']
    exp_lbl, e_color = classify_exposure(sig_pct)

    print()
    separator('═')
    print(f"  {C.BCYAN}{C.BOLD}NETWORK REPORT{C.RESET}")
    separator('═')

    def row(label, value, vcolor=C.BWHITE):
        print(f"  {C.BBLACK}{label:<22}{C.RESET}{vcolor}{value}{C.RESET}")

    row("SSID",             net['ssid'])
    row("Encryption Type",  sec)
    row("Security Rating",  rating, r_color)
    row("Signal Strength",  f"{sig_pct}%  {_signal_bar(sig_pct)}")
    row("Channel",          str(net['channel']))
    row("Exposure Risk",    exp_lbl, e_color)

    separator()
    print(f"  {C.BCYAN}{C.BOLD}SECURITY ANALYSIS{C.RESET}")
    separator()

    explanations = {
        'STRONG':    (C.BGREEN,  "WPA3 is the latest standard. Excellent protection against modern attacks."),
        'MODERATE':  (C.BYELLOW, "WPA2 is widely supported and reasonably secure. Upgrade to WPA3 if possible."),
        'WEAK':      (C.BYELLOW, "WPA (TKIP) is outdated. Vulnerable to dictionary attacks. Upgrade immediately."),
        'VERY WEAK': (C.BRED,    "WEP is completely broken. Can be cracked in minutes. Replace immediately."),
        'CRITICAL':  (C.BRED,    "Open network — no encryption. All traffic is visible to anyone nearby."),
        'UNKNOWN':   (C.BBLACK,  "Encryption type could not be determined."),
    }
    ec, expl = explanations.get(rating, (C.BBLACK, "No analysis available."))
    print(f"  {ec}{expl}{C.RESET}")

    if sig_pct >= 80:
        print(f"  {C.BRED}High signal exposure — this network is widely detectable.{C.RESET}")
    elif sig_pct >= 50:
        print(f"  {C.BYELLOW}Moderate signal — visible at distance.{C.RESET}")
    else:
        print(f"  {C.BGREEN}Low signal spread — limited detectability.{C.RESET}")

    separator()
    print()
    _press_any_key()

# =============================================================================
# FEATURE 3 — MONITOR CONNECTED DEVICES (ARP Scan)
# =============================================================================

def monitor_devices():
    """ARP-scan the local network for connected devices."""
    global gateway_ip
    section_header("MONITOR CONNECTED DEVICES")

    if not check_root():
        print(f"  {C.BYELLOW}⚠  Root recommended for accurate ARP scanning.{C.RESET}")

    gw = _detect_gateway()
    if gw:
        gateway_ip = gw
        print(f"  {C.BBLACK}Gateway detected:{C.RESET} {C.BWHITE}{gw}{C.RESET}")

    # Determine local subnet from default route interface
    iface, subnet = _get_local_subnet()
    if not subnet:
        print(f"  {C.BRED}Could not determine local subnet.{C.RESET}")
        _press_any_key()
        return

    print(f"  {C.BBLACK}Interface:{C.RESET} {C.BWHITE}{iface}{C.RESET}  "
          f"{C.BBLACK}Subnet:{C.RESET} {C.BWHITE}{subnet}{C.RESET}")
    print()

    scan_animation("ARP scanning", C.BCYAN, steps=20, delay=0.06)

    # Try arp-scan first, fall back to nmap -sn
    devices = []
    stdout, _, rc = run_cmd(f"arp-scan --localnet -I {iface} 2>/dev/null", timeout=20)
    if rc == 0 and stdout:
        devices = _parse_arpscan(stdout)
    else:
        stdout2, _, rc2 = run_cmd(f"nmap -sn {subnet} 2>/dev/null", timeout=30)
        if rc2 == 0 and stdout2:
            devices = _parse_nmap_sn(stdout2)
        else:
            # Last resort: read arp cache
            stdout3, _, _ = run_cmd("arp -n 2>/dev/null")
            devices = _parse_arp_cache(stdout3)

    if not devices:
        print(f"  {C.BYELLOW}No devices discovered. Try running as root.{C.RESET}")
        _press_any_key()
        return

    # ── Table ─────────────────────────────────────────────────────────────────
    col_ip  = 18
    col_mac = 20
    col_ven = 28

    def th(t, w): return f"{C.BCYAN}{C.BOLD}{t:<{w}}{C.RESET}"

    print()
    print(f"  {th('IP ADDRESS', col_ip)}{th('MAC ADDRESS', col_mac)}{th('VENDOR / INFO', col_ven)}")
    separator()

    for dev in devices:
        ip_col  = C.BWHITE if dev['ip'] != gw else C.BGREEN
        vendor  = dev.get('vendor', 'Unknown')
        tag     = f"{C.BBLACK}[GATEWAY]{C.RESET} " if dev['ip'] == gw else ""
        print(f"  {ip_col}{dev['ip']:<{col_ip}}{C.RESET}"
              f"{C.BWHITE}{dev['mac']:<{col_mac}}{C.RESET}"
              f"{C.BBLACK}{tag}{C.RESET}{C.BWHITE}{vendor:<{col_ven}}{C.RESET}")

    separator()
    count = len(devices)
    color = C.BGREEN if count < 10 else (C.BYELLOW if count < 20 else C.BRED)
    print(f"  Total devices found: {color}{count}{C.RESET}")

    if count > 20:
        print(f"  {C.BRED}⚠  High device count detected! Review unknown devices.{C.RESET}")
    elif count > 10:
        print(f"  {C.BYELLOW}⚠  Moderate device count. Verify unknown entries.{C.RESET}")

    print()
    _press_any_key()

def _detect_gateway():
    """Detect default gateway IP."""
    stdout, _, rc = run_cmd("ip route show default 2>/dev/null")
    if rc == 0 and stdout:
        m = re.search(r'default via (\S+)', stdout)
        if m:
            return m.group(1)
    # Fallback
    stdout2, _, _ = run_cmd("route -n 2>/dev/null")
    for line in stdout2.splitlines():
        if line.startswith('0.0.0.0'):
            parts = line.split()
            if len(parts) >= 2:
                return parts[1]
    return None

def _get_local_subnet():
    """Return (interface, subnet_cidr) of default route."""
    stdout, _, rc = run_cmd("ip route show default 2>/dev/null")
    iface = 'wlan0'
    if rc == 0 and stdout:
        m = re.search(r'dev (\S+)', stdout)
        if m:
            iface = m.group(1)
    # Get IP/prefix for interface
    stdout2, _, _ = run_cmd(f"ip -o -f inet addr show {iface} 2>/dev/null")
    m = re.search(r'inet (\S+)', stdout2)
    if m:
        return iface, m.group(1)
    return iface, None

def _parse_arpscan(raw):
    devices = []
    for line in raw.splitlines():
        m = re.match(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:]{17})\s*(.*)', line)
        if m:
            devices.append({'ip': m.group(1), 'mac': m.group(2),
                            'vendor': m.group(3).strip() or 'Unknown'})
    return devices

def _parse_nmap_sn(raw):
    devices = []
    ip, mac = None, 'N/A'
    for line in raw.splitlines():
        m_ip  = re.search(r'Nmap scan report for (\S+)', line)
        m_mac = re.search(r'MAC Address: ([0-9A-Fa-f:]{17})\s*(.*)', line)
        if m_ip:
            ip  = m_ip.group(1)
            mac = 'N/A'
        if m_mac and ip:
            mac = m_mac.group(1)
            vendor = m_mac.group(2).strip('() ')
            devices.append({'ip': ip, 'mac': mac, 'vendor': vendor or 'Unknown'})
            ip = None
        elif ip and re.search(r'Host is up', line):
            # Flush IP without MAC (local host)
            devices.append({'ip': ip, 'mac': 'N/A', 'vendor': 'Local host'})
            ip = None
    return devices

def _parse_arp_cache(raw):
    devices = []
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) >= 3 and re.match(r'\d+\.\d+\.\d+\.\d+', parts[0]):
            devices.append({'ip': parts[0], 'mac': parts[2], 'vendor': 'ARP Cache'})
    return devices

# =============================================================================
# FEATURE 4 — ROUTER PORT SCAN
# =============================================================================

ROUTER_PORTS = {
    21:  ('FTP',      'File transfer — often insecure'),
    22:  ('SSH',      'Secure Shell — generally safe if patched'),
    23:  ('Telnet',   'INSECURE — plaintext credentials!'),
    25:  ('SMTP',     'Mail — unusual on home router'),
    53:  ('DNS',      'Domain Name Service'),
    80:  ('HTTP',     'Web admin panel — unencrypted'),
    443: ('HTTPS',    'Secure web admin — preferred over HTTP'),
    8080:('HTTP-Alt', 'Alt web panel — check if needed'),
    8443:('HTTPS-Alt','Alt secure web panel'),
}

def scan_router_ports():
    """Scan router/gateway for open ports using nmap."""
    global gateway_ip
    section_header("ROUTER PORT SCAN")

    gw = gateway_ip or _detect_gateway()
    if not gw:
        print(f"  {C.BRED}Gateway not detected. Run feature 3 first.{C.RESET}")
        _press_any_key()
        return

    print(f"  {C.BBLACK}Target gateway:{C.RESET} {C.BWHITE}{gw}{C.RESET}")
    print(f"  {C.BBLUE}Launching nmap port scan...{C.RESET}")
    print()

    # Build port list
    ports = ','.join(str(p) for p in ROUTER_PORTS.keys())

    sp = start_spinner(f"Scanning {gw}", C.BCYAN)
    stdout, stderr, rc = run_cmd(
        f"nmap -p {ports} --open {gw} 2>/dev/null", timeout=30
    )
    stop_spinner(sp)

    if rc != 0 or not stdout:
        print(f"  {C.BRED}nmap failed. Ensure nmap is installed: sudo apt install nmap{C.RESET}")
        if stderr:
            print(f"  {C.BBLACK}{stderr[:200]}{C.RESET}")
        _press_any_key()
        return

    open_ports = _parse_nmap_ports(stdout)

    col_port = 8
    col_svc  = 12
    col_desc = 38
    col_risk = 12

    def th(t, w): return f"{C.BCYAN}{C.BOLD}{t:<{w}}{C.RESET}"
    print(f"  {th('PORT', col_port)}{th('SERVICE', col_svc)}{th('DESCRIPTION', col_desc)}{th('RISK', col_risk)}")
    separator()

    if not open_ports:
        print(f"  {C.BGREEN}No open ports detected in scanned range.{C.RESET}")
    else:
        for port in open_ports:
            info  = ROUTER_PORTS.get(port, ('Unknown', 'Unknown service'))
            svc   = info[0]
            desc  = info[1]
            # Risk classification
            if port == 23:
                risk, rc_ = 'CRITICAL', C.BRED
            elif port in (21, 80):
                risk, rc_ = 'HIGH',     C.BYELLOW
            elif port in (22, 443, 8443):
                risk, rc_ = 'LOW',      C.BGREEN
            else:
                risk, rc_ = 'MEDIUM',   C.BYELLOW
            print(f"  {C.BWHITE}{str(port):<{col_port}}{C.RESET}"
                  f"{C.BWHITE}{svc:<{col_svc}}{C.RESET}"
                  f"{C.BBLACK}{desc:<{col_desc}}{C.RESET}"
                  f"{rc_}{risk:<{col_risk}}{C.RESET}")

    separator()
    if 23 in open_ports:
        print(f"  {C.BRED}⚠  TELNET IS OPEN — Disable immediately! Credentials sent in plaintext.{C.RESET}")
    if 80 in open_ports and 443 not in open_ports:
        print(f"  {C.BYELLOW}⚠  HTTP admin panel open without HTTPS. Use HTTPS if available.{C.RESET}")

    print()
    _press_any_key()

def _parse_nmap_ports(raw):
    """Extract open port numbers from nmap output."""
    ports = []
    for line in raw.splitlines():
        m = re.match(r'(\d+)/tcp\s+open', line)
        if m:
            ports.append(int(m.group(1)))
    return ports

# =============================================================================
# FEATURE 5 — DNS INSPECTION
# =============================================================================

KNOWN_DNS = {
    '8.8.8.8':   'Google DNS',
    '8.8.4.4':   'Google DNS',
    '1.1.1.1':   'Cloudflare DNS',
    '1.0.0.1':   'Cloudflare DNS',
    '9.9.9.9':   'Quad9 DNS',
    '208.67.222.222': 'OpenDNS',
    '208.67.220.220': 'OpenDNS',
    '4.2.2.1':   'Level3 DNS',
    '4.2.2.2':   'Level3 DNS',
}

def dns_inspection():
    """Read and display DNS configuration."""
    section_header("DNS INSPECTION")

    print(f"  {C.BBLUE}Reading /etc/resolv.conf ...{C.RESET}")
    time.sleep(0.5)

    try:
        with open('/etc/resolv.conf', 'r') as f:
            content = f.read()
    except PermissionError:
        print(f"  {C.BRED}Permission denied reading /etc/resolv.conf{C.RESET}")
        _press_any_key()
        return
    except FileNotFoundError:
        print(f"  {C.BRED}/etc/resolv.conf not found.{C.RESET}")
        _press_any_key()
        return

    print()
    print(f"  {C.BCYAN}{C.BOLD}CONFIGURED DNS SERVERS{C.RESET}")
    separator()

    nameservers = re.findall(r'^\s*nameserver\s+(\S+)', content, re.MULTILINE)
    search_domains = re.findall(r'^\s*search\s+(.+)', content, re.MULTILINE)

    if not nameservers:
        print(f"  {C.BYELLOW}No nameservers found in resolv.conf{C.RESET}")
    else:
        for ns in nameservers:
            known = KNOWN_DNS.get(ns)
            if known:
                label = f"{C.BGREEN}✔  {known}{C.RESET}"
            else:
                label = f"{C.BYELLOW}⚠  Unrecognized provider{C.RESET}"
            print(f"  {C.BWHITE}{ns:<20}{C.RESET}  {label}")

    if search_domains:
        print()
        print(f"  {C.BCYAN}Search domains:{C.RESET}  {C.BWHITE}{', '.join(search_domains)}{C.RESET}")

    separator()
    print()
    print(f"  {C.BCYAN}{C.BOLD}DNS SECURITY GUIDANCE{C.RESET}")
    separator()
    notes = [
        "Use trusted DNS providers (Cloudflare 1.1.1.1, Google 8.8.8.8, Quad9 9.9.9.9).",
        "Avoid ISP default DNS if privacy is a concern — may log queries.",
        "Consider DNS-over-HTTPS (DoH) or DNS-over-TLS (DoT) for encrypted lookups.",
        "Unusual or unknown DNS servers may indicate DNS hijacking — investigate.",
    ]
    for note in notes:
        print(f"  {C.BBLACK}•{C.RESET}  {C.BWHITE}{note}{C.RESET}")

    print()
    _press_any_key()

# =============================================================================
# FEATURE 6 — WIFI SECURITY SCORE
# =============================================================================

def wifi_security_score():
    """Calculate and display a WiFi security score."""
    global security_score
    section_header("WIFI SECURITY SCORE")

    score  = 0
    total  = 10
    checks = []

    # ── Check 1: Connected network encryption ────────────────────────────────
    stdout, _, _ = run_cmd("nmcli -t -f active,security dev wifi list 2>/dev/null")
    active_sec = ''
    for line in stdout.splitlines():
        if line.startswith('yes:'):
            active_sec = line.split(':', 1)[-1].strip()
            break

    if 'WPA3' in active_sec.upper():
        score += 3
        checks.append((3, 3, 'Connected network uses WPA3 encryption'))
    elif 'WPA2' in active_sec.upper():
        score += 2
        checks.append((2, 3, 'Connected network uses WPA2 (WPA3 preferred)'))
    elif active_sec:
        score += 0
        checks.append((0, 3, f'Weak/no encryption on connected network ({active_sec})'))
    else:
        score += 1
        checks.append((1, 3, 'Could not determine active network encryption'))

    # ── Check 2: Gateway detected ─────────────────────────────────────────────
    gw = gateway_ip or _detect_gateway()
    if gw:
        score += 1
        checks.append((1, 1, f'Default gateway detected ({gw})'))
    else:
        checks.append((0, 1, 'Default gateway not detected'))

    # ── Check 3: DNS configured ───────────────────────────────────────────────
    try:
        with open('/etc/resolv.conf') as f:
            dns_raw = f.read()
        ns_list = re.findall(r'nameserver\s+(\S+)', dns_raw)
        known_count = sum(1 for ns in ns_list if ns in KNOWN_DNS)
        if known_count == len(ns_list) and ns_list:
            score += 2
            checks.append((2, 2, 'All DNS servers are known trusted providers'))
        elif known_count > 0:
            score += 1
            checks.append((1, 2, 'Some DNS servers are unrecognized'))
        else:
            checks.append((0, 2, 'No recognized DNS providers found'))
    except Exception:
        checks.append((0, 2, 'Could not read DNS configuration'))

    # ── Check 4: Open networks in vicinity ────────────────────────────────────
    if scanned_networks:
        open_nets = [n for n in scanned_networks
                     if not n['security'] or n['security'].upper() in ('OPEN','--','NONE','')]
        if len(open_nets) == 0:
            score += 2
            checks.append((2, 2, 'No open (unencrypted) networks in vicinity'))
        elif len(open_nets) <= 2:
            score += 1
            checks.append((1, 2, f'{len(open_nets)} open network(s) nearby — avoid connecting'))
        else:
            checks.append((0, 2, f'{len(open_nets)} open networks nearby — high-risk environment'))
    else:
        score += 1
        checks.append((1, 2, 'Network scan not run — partial score'))

    # ── Check 5: Nmap available ───────────────────────────────────────────────
    _, _, rc_nm = run_cmd("which nmap 2>/dev/null")
    if rc_nm == 0:
        score += 1
        checks.append((1, 1, 'nmap is available for port scanning'))
    else:
        checks.append((0, 1, 'nmap not installed — install for port scanning'))

    # ── Ensure score within bounds ────────────────────────────────────────────
    score = min(score, total)
    security_score = score

    # ── Display ───────────────────────────────────────────────────────────────
    print()
    for earned, possible, desc in checks:
        if earned == possible:
            icon  = f"{C.BGREEN}✔{C.RESET}"
            pts   = f"{C.BGREEN}+{earned}/{possible}{C.RESET}"
        elif earned > 0:
            icon  = f"{C.BYELLOW}◑{C.RESET}"
            pts   = f"{C.BYELLOW}+{earned}/{possible}{C.RESET}"
        else:
            icon  = f"{C.BRED}✘{C.RESET}"
            pts   = f"{C.BRED}+{earned}/{possible}{C.RESET}"
        print(f"  {icon}  {pts}  {C.BWHITE}{desc}{C.RESET}")

    separator()
    print()

    # Animated score reveal
    print(f"  {C.BCYAN}Calculating final score...{C.RESET}")
    time.sleep(0.3)
    for i in range(score + 1):
        bar_filled = int((i / total) * 30)
        bar = '█' * bar_filled + '░' * (30 - bar_filled)
        pct = int((i / total) * 100)
        if pct >= 70:   bc = C.BGREEN
        elif pct >= 40: bc = C.BYELLOW
        else:           bc = C.BRED
        print(f"\r  {C.BOLD}{C.BCYAN}WiFi Security Score: {bc}{i:>2} / {total}{C.RESET}  [{bc}{bar}{C.RESET}]  {bc}{pct}%{C.RESET}  ",
              end='', flush=True)
        time.sleep(0.12)
    print()
    print()

    if score >= 8:
        verdict = f"{C.BGREEN}SECURE — Good configuration.{C.RESET}"
    elif score >= 5:
        verdict = f"{C.BYELLOW}MODERATE — Improvements recommended.{C.RESET}"
    else:
        verdict = f"{C.BRED}VULNERABLE — Immediate action required!{C.RESET}"

    print(f"  Verdict: {verdict}")
    print()
    _press_any_key()

# =============================================================================
# FEATURE 7 — SECURITY RECOMMENDATIONS
# =============================================================================

RECOMMENDATIONS = [
    ("Use WPA3 encryption",               "WPA3 is the strongest WiFi standard. Upgrade router/devices if possible."),
    ("Use long WiFi passwords (14+ chars)","Short passwords are vulnerable to brute-force. Use a passphrase."),
    ("Disable WPS",                        "WiFi Protected Setup has known vulnerabilities. Disable in router settings."),
    ("Change default admin credentials",   "Default admin/admin credentials are widely known. Change immediately."),
    ("Update router firmware regularly",   "Firmware updates patch security vulnerabilities. Check monthly."),
    ("Monitor connected devices",          "Regularly audit devices on your network for unauthorized access."),
    ("Use a guest network for visitors",   "Isolate guest devices from your main network."),
    ("Disable remote management",          "Unless needed, turn off remote router access over the internet."),
    ("Use DNS-over-HTTPS or DNS-over-TLS", "Encrypts DNS queries to prevent eavesdropping and hijacking."),
    ("Enable router firewall",             "Ensure the router's built-in firewall is active."),
    ("Disable Telnet on router",           "Telnet sends credentials in plaintext. Use SSH or HTTPS admin panel only."),
    ("Place router centrally",             "Minimizes signal bleed outside your property."),
]

def security_recommendations():
    """Display security best-practice checklist."""
    section_header("SECURITY RECOMMENDATIONS")
    print(f"  {C.BCYAN}WiFi & Network Security Best Practices{C.RESET}")
    print()

    for i, (title, detail) in enumerate(RECOMMENDATIONS, 1):
        print(f"  {C.BGREEN}[{i:>2}]{C.RESET}  {C.BOLD}{C.BWHITE}{title}{C.RESET}")
        print(f"        {C.BBLACK}{detail}{C.RESET}")
        print()

    separator()
    print(f"  {C.BBLACK}For further reading: {C.BBLUE}https://www.cisa.gov/secure-our-world{C.RESET}")
    print()
    _press_any_key()

# =============================================================================
# UTILITY
# =============================================================================

def _press_any_key():
    """Pause until user presses Enter."""
    try:
        input(f"  {C.BBLACK}[ press ENTER to continue ]{C.RESET}  ")
    except (KeyboardInterrupt, EOFError):
        pass

# =============================================================================
# MAIN LOOP
# =============================================================================

DISPATCH = {
    '1': scan_wifi_networks,
    '2': analyze_network,
    '3': monitor_devices,
    '4': scan_router_ports,
    '5': dns_inspection,
    '6': wifi_security_score,
    '7': security_recommendations,
}

def main():
    """Entry point — main event loop."""
    print_banner()
    time.sleep(0.5)

    while True:
        print_banner()
        print_menu()

        choice = get_choice(
            "  Select option [1-8]: ",
            valid=[str(i) for i in range(1, 9)]
        )

        if choice == '8':
            clear()
            print()
            print(f"  {C.BGREEN}{C.BOLD}Session terminated.{C.RESET}  Stay secure.")
            print(f"  {C.BBLACK}developed by @ghvstprogrammer on x/twitter{C.RESET}")
            print()
            sys.exit(0)

        fn = DISPATCH.get(choice)
        if fn:
            clear()
            try:
                fn()
            except KeyboardInterrupt:
                print(f"\n  {C.BYELLOW}Interrupted.{C.RESET}")
                _press_any_key()

if __name__ == '__main__':
    main()
