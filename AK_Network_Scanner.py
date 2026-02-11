#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ===============================================================
#  AK Software License v1.0
#  Copyright (c) 2025 AK (ak404z)
#
#  This software is provided for educational and research purposes
#  only. You are NOT allowed to use this code for:
#      - Illegal activities
#      - Harming individuals or organizations
#      - Unauthorized access or data breaches
#
#  By using this software, you agree that:
#      - The author is not responsible for any misuse.
#      - The tool is provided "AS IS" without any warranty.
#      - You assume full responsibility for any consequences.
#
#  You may modify and redistribute this code ONLY with proper
#  credit to the original author (AK / ak404z).
#
#  Unauthorized commercial use is strictly prohibited.
# ===============================================================
from scapy.all import *
import time
import socket
import subprocess
from mac_vendor_lookup import MacLookup, BaseMacLookup
from prettytable import PrettyTable
import random
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import requests
import re

# Global variables
original_mac = None
interface = "eth0"

def show_banner():
    """Display the tool banner"""
    banner = """
     █████╗     ██╗  ██╗
    ██╔══██╗    ██║ ██╔╝
    ███████║    █████╔╝ 
    ██╔══██║    ██╔═██╗ 
    ██║  ██║    ██║  ██╗
    ╚═╝  ╚═╝    ╚═╝  ╚═╝
    
    ╔══════════════════════════════════╗
    ║   AK Network Scanner             ║
    ║   Advanced Recon & Analysis      ║
    ╚══════════════════════════════════╝
    """
    print(banner)


def activate_stealth_mode():
    """Change MAC address temporarily for stealth"""
    global original_mac
    
    print("🕵️  Enabling Stealth Mode...")
    
    try:
        subprocess.call(['ifconfig', interface, 'down'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        output = subprocess.check_output(['macchanger', '-s', interface], stderr=subprocess.DEVNULL).decode()
        original_mac = output.split('\n')[0].split()[-1]
        subprocess.call(['macchanger', '-r', interface], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        subprocess.call(['ifconfig', interface, 'up'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        print(f"✅ MAC changed temporarily on {interface}")
    except:
        print("⚠️  Stealth mode requires macchanger - continuing without it")


def restore_mac():
    """Restore original MAC address"""
    if original_mac:
        print("🔁 Restoring original MAC...")
        try:
            subprocess.call(['ifconfig', interface, 'down'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            subprocess.call(['macchanger', '-m', original_mac, interface], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            subprocess.call(['ifconfig', interface, 'up'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            print("✅ Original MAC restored.")
        except:
            pass


def menu():
    """Display main menu"""
    print("\n[1] Regular Scan")
    print("[2] Stealth Mode Scan")
    print("[3] Monitoring Mode")
    print("[4] Deep Scan (Aggressive)")
    choice = input("\n🔥 Select option: ")
    return choice


def get_mac_vendor_online(mac):
    """Get MAC vendor from online API"""
    try:
        mac_clean = mac.replace(':', '').replace('-', '').upper()[:6]
        
        # Try macvendors.com API
        url = f"https://api.macvendors.com/{mac}"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    try:
        # Try maclookup.app API
        url = f"https://api.maclookup.app/v2/macs/{mac}"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('found') and data.get('company'):
                return data['company']
    except:
        pass
    
    return None


def get_mac_vendor(mac):
    """Enhanced MAC vendor lookup with multiple methods"""
    # Method 1: Local database
    try:
        lookup = MacLookup()
        lookup.load_vendors()
        vendor = lookup.lookup(mac)
        if vendor and vendor != 'Unknown':
            return vendor
    except:
        pass
    
    # Method 2: Update and retry
    try:
        BaseMacLookup.update_vendors()
        lookup = MacLookup()
        vendor = lookup.lookup(mac)
        if vendor and vendor != 'Unknown':
            return vendor
    except:
        pass
    
    # Method 3: Online API
    online_vendor = get_mac_vendor_online(mac)
    if online_vendor:
        return online_vendor
    
    # Method 4: IEEE OUI lookup using system
    try:
        output = subprocess.check_output(['ieee-oui', mac[:8]], timeout=2, stderr=subprocess.DEVNULL).decode()
        if output and 'not found' not in output.lower():
            vendor = output.strip().split('\n')[0]
            if vendor:
                return vendor
    except:
        pass
    
    # Method 5: Manual OUI database (common vendors)
    mac_prefix = mac[:8].upper().replace(':', '-')
    
    oui_database = {
        '00-50-56': 'VMware',
        '00-0C-29': 'VMware',
        '00-05-69': 'VMware',
        '00-1C-42': 'Parallels',
        '08-00-27': 'Oracle VirtualBox',
        '52-54-00': 'QEMU/KVM',
        'DC-A6-32': 'Raspberry Pi Foundation',
        'B8-27-EB': 'Raspberry Pi Foundation',
        'E4-5F-01': 'Raspberry Pi Trading',
        '00-15-5D': 'Microsoft Hyper-V',
        '00-25-90': 'Super Micro',
        '00-1B-21': 'Intel',
        '00-1A-A0': 'Dell',
        'D0-50-99': 'Micro-Star International (MSI)',
        '00-23-24': 'Freescale Semiconductor',
        '00-22-19': 'Cisco Systems',
        '00-0D-B9': 'D-Link',
        '00-C0-CA': 'ALFA Network',
        '00-1F-3C': 'Hewlett Packard',
        '3C-A9-F4': 'Hewlett Packard Enterprise',
        '00-50-B6': 'Hon Hai Precision (Foxconn)',
        '00-1E-C9': 'BUFFALO.INC',
        '00-24-D7': 'Cisco-Linksys',
        '00-E0-4C': 'Realtek',
        '70-85-C2': 'Realtek',
        'AC-22-0B': 'Realtek',
        '00-E0-4B': 'Nokia',
        '38-D5-47': 'Nokia',
        '00-1B-63': 'Apple',
        '00-03-93': 'Apple',
        '00-0A-27': 'Apple',
        '00-0D-93': 'Apple',
        '00-14-51': 'Apple',
        '00-16-CB': 'Apple',
        '00-17-F2': 'Apple',
        '00-19-E3': 'Apple',
        '00-1B-63': 'Apple',
        '00-1C-B3': 'Apple',
        '00-1D-4F': 'Apple',
        '00-1E-52': 'Apple',
        '00-1E-C2': 'Apple',
        '00-1F-5B': 'Apple',
        '00-1F-F3': 'Apple',
        '00-21-E9': 'Apple',
        '00-22-41': 'Apple',
        '00-23-12': 'Apple',
        '00-23-32': 'Apple',
        '00-23-6C': 'Apple',
        '00-23-DF': 'Apple',
        '00-24-36': 'Apple',
        '00-25-00': 'Apple',
        '00-25-4B': 'Apple',
        '00-25-BC': 'Apple',
        '00-26-08': 'Apple',
        '00-26-4A': 'Apple',
        '00-26-B0': 'Apple',
        '00-26-BB': 'Apple',
        '04-0C-CE': 'Apple',
        '04-15-52': 'Apple',
        '04-26-65': 'Apple',
        '04-48-9A': 'Apple',
        '04-54-53': 'Apple',
        '08-66-98': 'Apple',
        '08-70-45': 'Apple',
        '0C-3E-9F': 'Apple',
        '0C-4D-E9': 'Apple',
        '0C-74-C2': 'Apple',
        '10-93-E9': 'Apple',
        '10-9A-DD': 'Apple',
        '10-DD-B1': 'Apple',
        '14-10-9F': 'Apple',
        '14-8F-C6': 'Apple',
        '14-BD-61': 'Apple',
        '18-34-51': 'Apple',
        '18-3D-A2': 'Apple',
        '18-AF-61': 'Apple',
        '18-E7-F4': 'Apple',
        '1C-AB-A7': 'Apple',
        '20-C9-D0': 'Apple',
        '24-A0-74': 'Apple',
        '24-AB-81': 'Apple',
        '28-37-37': 'Apple',
        '28-CF-E9': 'Apple',
        '28-E1-4C': 'Apple',
        '2C-1F-23': 'Apple',
        '2C-33-61': 'Apple',
        '2C-BE-08': 'Apple',
        '30-63-6B': 'Apple',
        '30-90-AB': 'Apple',
        '30-F7-C5': 'Apple',
        '34-15-9E': 'Apple',
        '34-36-3B': 'Apple',
        '34-51-C9': 'Apple',
        '34-A3-95': 'Apple',
        '38-0F-4A': 'Apple',
        '38-C9-86': 'Apple',
        '3C-15-C2': 'Apple',
        '40-30-04': 'Apple',
        '40-33-1A': 'Apple',
        '40-4D-7F': 'Apple',
        '40-6C-8F': 'Apple',
        '40-A6-D9': 'Apple',
        '40-B3-95': 'Apple',
        '44-2A-60': 'Apple',
        '44-4C-0C': 'Apple',
        '44-D8-84': 'Apple',
        '48-43-7C': 'Apple',
        '48-60-BC': 'Apple',
        '48-A1-95': 'Apple',
        '4C-74-BF': 'Apple',
        '4C-B1-99': 'Apple',
        '50-EA-D6': 'Apple',
        '54-26-96': 'Apple',
        '54-72-4F': 'Apple',
        '54-E4-3A': 'Apple',
        '58-40-4E': 'Apple',
        '5C-59-48': 'Apple',
        '5C-95-AE': 'Apple',
        '5C-97-F3': 'Apple',
        '60-33-4B': 'Apple',
        '60-69-44': 'Apple',
        '60-C5-47': 'Apple',
        '60-F8-1D': 'Apple',
        '60-FA-CD': 'Apple',
        '60-FB-42': 'Apple',
        '64-20-0C': 'Apple',
        '64-76-BA': 'Apple',
        '64-A3-CB': 'Apple',
        '64-B9-E8': 'Apple',
        '68-5B-35': 'Apple',
        '68-9C-70': 'Apple',
        '68-A8-6D': 'Apple',
        '68-D9-3C': 'Apple',
        '68-FE-F7': 'Apple',
        '6C-3E-6D': 'Apple',
        '6C-40-08': 'Apple',
        '6C-4D-73': 'Apple',
        '6C-70-9F': 'Apple',
        '6C-72-E7': 'Apple',
        '6C-94-F8': 'Apple',
        '70-11-24': 'Apple',
        '70-48-0F': 'Apple',
        '70-56-81': 'Apple',
        '70-73-CB': 'Apple',
        '70-CD-60': 'Apple',
        '70-DE-E2': 'Apple',
        '70-EC-E4': 'Apple',
        '74-1B-B2': 'Apple',
        '74-E1-B6': 'Apple',
        '74-E2-F5': 'Apple',
        '78-31-C1': 'Apple',
        '78-67-D7': 'Apple',
        '78-7B-8A': 'Apple',
        '78-A3-E4': 'Apple',
        '78-CA-39': 'Apple',
        '78-D7-5F': 'Apple',
        '78-FD-94': 'Apple',
        '7C-01-91': 'Apple',
        '7C-11-BE': 'Apple',
        '7C-5C-F8': 'Apple',
        '7C-6D-62': 'Apple',
        '7C-C3-A1': 'Apple',
        '7C-D1-C3': 'Apple',
        '7C-F0-5F': 'Apple',
        '80-49-71': 'Apple',
        '80-92-9F': 'Apple',
        '80-E6-50': 'Apple',
        '84-38-35': 'Apple',
        '84-85-06': 'Apple',
        '84-8E-0C': 'Apple',
        '84-FC-FE': 'Apple',
        '88-1F-A1': 'Apple',
        '88-53-95': 'Apple',
        '88-63-DF': 'Apple',
        '88-66-5A': 'Apple',
        '88-C6-63': 'Apple',
        '8C-29-37': 'Apple',
        '8C-2D-AA': 'Apple',
        '8C-7C-92': 'Apple',
        '8C-85-90': 'Apple',
        '8C-FA-BA': 'Apple',
        '90-27-E4': 'Apple',
        '90-72-40': 'Apple',
        '90-8D-6C': 'Apple',
        '90-B0-ED': 'Apple',
        '90-B9-31': 'Apple',
        '94-E9-6A': 'Apple',
        '98-03-D8': 'Apple',
        '98-5A-EB': 'Apple',
        '98-B8-E3': 'Apple',
        '98-CA-33': 'Apple',
        '98-D6-BB': 'Apple',
        '98-E0-D9': 'Apple',
        '98-F0-AB': 'Apple',
        '98-FE-94': 'Apple',
        '9C-20-7B': 'Apple',
        '9C-35-EB': 'Apple',
        '9C-84-BF': 'Apple',
        '9C-F4-8E': 'Apple',
        '9C-FC-E8': 'Apple',
        'A0-99-9B': 'Apple',
        'A0-D7-95': 'Apple',
        'A0-ED-CD': 'Apple',
        'A4-5E-60': 'Apple',
        'A4-67-06': 'Apple',
        'A4-83-E7': 'Apple',
        'A4-B1-97': 'Apple',
        'A4-C3-61': 'Apple',
        'A4-D1-8C': 'Apple',
        'A8-20-66': 'Apple',
        'A8-60-B6': 'Apple',
        'A8-66-7F': 'Apple',
        'A8-86-DD': 'Apple',
        'A8-88-08': 'Apple',
        'A8-96-75': 'Apple',
        'A8-BE-27': 'Apple',
        'A8-FA-D8': 'Apple',
        'AC-29-3A': 'Apple',
        'AC-3C-0B': 'Apple',
        'AC-61-EA': 'Apple',
        'AC-87-A3': 'Apple',
        'AC-BC-32': 'Apple',
        'AC-CF-5C': 'Apple',
        'B0-34-95': 'Apple',
        'B0-65-BD': 'Apple',
        'B0-CA-68': 'Apple',
        'B4-18-D1': 'Apple',
        'B4-8B-19': 'Apple',
        'B4-F0-AB': 'Apple',
        'B4-F6-1C': 'Apple',
        'B8-17-C2': 'Apple',
        'B8-41-A4': 'Apple',
        'B8-53-AC': 'Apple',
        'B8-63-4D': 'Apple',
        'B8-78-2E': 'Apple',
        'B8-C7-5D': 'Apple',
        'B8-E8-56': 'Apple',
        'B8-F6-B1': 'Apple',
        'BC-3B-AF': 'Apple',
        'BC-52-B7': 'Apple',
        'BC-6C-21': 'Apple',
        'BC-92-6B': 'Apple',
        'BC-9F-EF': 'Apple',
        'C0-1A-DA': 'Apple',
        'C0-2F-2D': 'Google Nest/Chromecast',
        'C4-2C-03': 'Apple',
        'C8-2A-14': 'Apple',
        'C8-33-4B': 'Apple',
        'C8-69-CD': 'Apple',
        'C8-85-50': 'Apple',
        'C8-B5-B7': 'Apple',
        'C8-BC-C8': 'Apple',
        'CC-08-8D': 'Apple',
        'CC-25-EF': 'Apple',
        'CC-29-F5': 'Apple',
        'CC-44-63': 'Apple',
        'CC-78-5F': 'Apple',
        'D0-03-4B': 'Apple',
        'D0-23-DB': 'Apple',
        'D0-33-11': 'Apple',
        'D0-7E-35': 'Apple',
        'D0-81-7A': 'Apple',
        'D0-A6-37': 'Apple',
        'D0-C5-F3': 'Apple',
        'D0-D2-B0': 'Apple',
        'D0-E1-40': 'Apple',
        'D4-9A-20': 'Apple',
        'D4-A3-3D': 'Apple',
        'D4-DC-CD': 'Apple',
        'D4-F4-6F': 'Apple',
        'D8-00-4D': 'Apple',
        'D8-30-62': 'Apple',
        'D8-96-95': 'Apple',
        'D8-9E-3F': 'Apple',
        'D8-A2-5E': 'Apple',
        'D8-BB-2C': 'Apple',
        'D8-CF-9C': 'Apple',
        'DC-2B-2A': 'Apple',
        'DC-2B-61': 'Apple',
        'DC-56-E7': 'Apple',
        'DC-86-D8': 'Apple',
        'DC-9B-9C': 'Apple',
        'E0-5F-45': 'Apple',
        'E0-66-78': 'Apple',
        'E0-AC-CB': 'Apple',
        'E0-B5-2D': 'Apple',
        'E0-B9-E5': 'Apple',
        'E0-C9-7A': 'Apple',
        'E0-F5-C6': 'Apple',
        'E0-F8-47': 'Apple',
        'E4-25-E7': 'Apple',
        'E4-8B-7F': 'Apple',
        'E4-98-D6': 'Apple',
        'E4-9A-79': 'Apple',
        'E4-CE-8F': 'Apple',
        'E8-04-0B': 'Apple',
        'E8-06-88': 'Apple',
        'E8-80-2E': 'Apple',
        'E8-B2-AC': 'Apple',
        'EC-35-86': 'Apple',
        'EC-85-2F': 'Apple',
        'F0-18-98': 'Apple',
        'F0-24-75': 'Apple',
        'F0-98-9D': 'Apple',
        'F0-B4-79': 'Apple',
        'F0-C1-F1': 'Apple',
        'F0-CB-A1': 'Apple',
        'F0-D1-A9': 'Apple',
        'F0-DB-E2': 'Apple',
        'F0-DC-E2': 'Apple',
        'F0-F6-1C': 'Apple',
        'F4-0F-24': 'Apple',
        'F4-1B-A1': 'Apple',
        'F4-37-B7': 'Apple',
        'F4-5C-89': 'Apple',
        'F4-F1-5A': 'Apple',
        'F4-F9-51': 'Apple',
        'F8-1E-DF': 'Apple',
        'F8-27-93': 'Apple',
        'F8-2D-7C': 'Apple',
        'F8-95-C7': 'Apple',
        'FC-25-3F': 'Apple',
        'FC-E9-98': 'Apple',
        'FC-FC-48': 'Apple',
        '00-1D-C0': 'TP-Link',
        '00-27-19': 'TP-Link',
        '14-CF-92': 'TP-Link',
        '50-C7-BF': 'TP-Link',
        '74-DA-88': 'TP-Link',
        '84-16-F9': 'TP-Link',
        'A0-F3-C1': 'TP-Link',
        'C0-4A-00': 'TP-Link',
        'EC-08-6B': 'TP-Link',
        'F4-F2-6D': 'TP-Link',
        '00-18-E7': 'Netgear',
        '00-14-6C': 'Netgear',
        '00-26-F2': 'Netgear',
        '2C-30-33': 'Netgear',
        '84-1B-5E': 'Netgear',
        'A0-63-91': 'Netgear',
        'B0-7F-B9': 'Netgear',
        'C4-04-15': 'Netgear',
        'E0-46-9A': 'Netgear',
        '00-04-20': 'ASUS',
        '00-1E-8C': 'ASUS',
        '00-22-15': 'ASUS',
        '04-D9-F5': 'ASUS',
        '08-60-6E': 'ASUS',
        '10-BF-48': 'ASUS',
        '14-DD-A9': 'ASUS',
        '1C-B7-2C': 'ASUS',
        '2C-FD-A1': 'ASUS',
        '30-5A-3A': 'ASUS',
        '38-D5-47': 'ASUS',
        '50-46-5D': 'ASUS',
        '54-A0-50': 'ASUS',
        '70-4D-7B': 'ASUS',
        '74-D0-2B': 'ASUS',
        '9C-5C-8E': 'ASUS',
        'AC-9E-17': 'ASUS',
        'D8-50-E6': 'ASUS',
        'F4-6D-04': 'ASUS',
        '00-07-32': 'Belkin',
        '00-11-50': 'Belkin',
        '00-17-3F': 'Belkin',
        '00-1C-DF': 'Belkin',
        '08-86-3B': 'Belkin',
        '14-91-82': 'Belkin',
        '94-10-3E': 'Belkin',
        'C0-56-27': 'Belkin',
        'EC-1A-59': 'Belkin',
        '00-13-10': 'Linksys (Cisco)',
        '00-14-BF': 'Linksys (Cisco)',
        '00-18-39': 'Linksys (Cisco)',
        '00-1A-70': 'Linksys (Cisco)',
        '00-1D-7E': 'Linksys (Cisco)',
        '00-21-29': 'Linksys (Cisco)',
        '00-22-6B': 'Linksys (Cisco)',
        '00-23-69': 'Linksys (Cisco)',
        '00-25-9C': 'Linksys (Cisco)',
        '10-BF-48': 'Linksys (Cisco)',
        '20-AA-4B': 'Linksys (Cisco)',
        '48-F8-B3': 'Linksys (Cisco)',
        '58-6D-8F': 'Linksys (Cisco)',
        'C0-C1-C0': 'Linksys (Cisco)',
        'E8-9F-80': 'Linksys (Cisco)',
        '00-0F-B5': 'Samsung',
        '00-12-FB': 'Samsung',
        '00-13-77': 'Samsung',
        '00-15-99': 'Samsung',
        '00-16-32': 'Samsung',
        '00-16-6C': 'Samsung',
        '00-17-C9': 'Samsung',
        '00-18-AF': 'Samsung',
        '00-1A-8A': 'Samsung',
        '00-1B-98': 'Samsung',
        '00-1C-43': 'Samsung',
        '00-1D-25': 'Samsung',
        '00-1E-7D': 'Samsung',
        '00-1F-CC': 'Samsung',
        '00-21-19': 'Samsung',
        '00-21-4C': 'Samsung',
        '00-21-D1': 'Samsung',
        '00-21-D2': 'Samsung',
        '00-23-39': 'Samsung',
        '00-23-C2': 'Samsung',
        '00-23-D6': 'Samsung',
        '00-23-D7': 'Samsung',
        '00-24-54': 'Samsung',
        '00-24-90': 'Samsung',
        '00-24-91': 'Samsung',
        '00-24-E9': 'Samsung',
        '00-25-38': 'Samsung',
        '00-25-66': 'Samsung',
        '00-25-67': 'Samsung',
        '00-26-37': 'Samsung',
        '00-26-5D': 'Samsung',
        '00-26-5F': 'Samsung',
        '04-18-0F': 'Samsung',
        '04-FE-31': 'Samsung',
        '08-08-C2': 'Samsung',
        '08-37-3D': 'Samsung',
        '08-D4-2B': 'Samsung',
        '08-EE-8B': 'Samsung',
        '0C-14-20': 'Samsung',
        '0C-89-10': 'Samsung',
        '10-30-47': 'Samsung',
        '10-77-B1': 'Samsung',
        '14-7D-C5': 'Samsung',
        '14-A5-1A': 'Samsung',
        '18-3A-2D': 'Samsung',
        '18-3F-47': 'Samsung',
        '18-46-17': 'Samsung',
        '18-4F-32': 'Samsung',
        '1C-62-B8': 'Samsung',
        '1C-66-AA': 'Samsung',
        '1C-AF-05': 'Samsung',
        '20-13-E0': 'Samsung',
        '20-64-32': 'Samsung',
        '20-A6-CD': 'Samsung',
        '24-4B-03': 'Samsung',
        '28-3D-C2': 'Samsung',
        '28-63-36': 'Samsung',
        '28-BA-B5': 'Samsung',
        '2C-44-01': 'Samsung',
        '2C-44-FD': 'Samsung',
        '30-07-4D': 'Samsung',
        '30-19-66': 'Samsung',
        '34-08-BC': 'Samsung',
        '34-23-87': 'Samsung',
        '34-AA-8B': 'Samsung',
        '38-01-97': 'Samsung',
        '38-0A-94': 'Samsung',
        '38-16-D1': 'Samsung',
        '38-AA-3C': 'Samsung',
        '3C-5A-37': 'Samsung',
        '3C-8B-FE': 'Samsung',
        '40-0E-85': 'Samsung',
        '40-0E-DE': 'Samsung',
        '40-23-43': 'Samsung',
        '40-5B-D8': 'Samsung',
        '40-B8-9A': 'Samsung',
        '44-78-3E': 'Samsung',
        '44-87-FC': 'Samsung',
        '44-D6-E2': 'Samsung',
        '48-5A-3F': 'Samsung',
        '4C-3C-16': 'Samsung',
        '4C-BC-A5': 'Samsung',
        '50-01-BB': 'Samsung',
        '50-32-37': 'Samsung',
        '50-78-B3': 'Samsung',
        '50-A7-2B': 'Samsung',
        '50-B7-C3': 'Samsung',
        '50-CC-F8': 'Samsung',
        '54-88-0E': 'Samsung',
        '54-92-BE': 'Samsung',
        '5C-0A-5B': 'Samsung',
        '5C-0E-8B': 'Samsung',
        '5C-3C-27': 'Samsung',
        '5C-51-4F': 'Samsung',
        '5C-F6-DC': 'Samsung',
        '5C-F7-E6': 'Samsung',
        '60-6B-BD': 'Samsung',
        '60-D0-A9': 'Samsung',
        '60-F4-45': 'Samsung',
        '64-6E-97': 'Samsung',
        '64-77-91': 'Samsung',
        '64-B8-53': 'Samsung',
        '68-27-37': 'Samsung',
        '68-DF-DD': 'Samsung',
        '6C-2F-2C': 'Samsung',
        '6C-40-D9': 'Samsung',
        '70-5A-0F': 'Samsung',
        '70-F9-27': 'Samsung',
        '74-45-8A': 'Samsung',
        '74-5F-00': 'Samsung',
        '78-1F-DB': 'Samsung',
        '78-25-AD': 'Samsung',
        '78-47-1D': 'Samsung',
        '78-59-5E': 'Samsung',
        '78-9E-D0': 'Samsung',
        '78-A8-73': 'Samsung',
        '78-D6-F0': 'Samsung',
        '7C-11-CB': 'Samsung',
        '7C-61-66': 'Samsung',
        '7C-7A-91': 'Samsung',
        '7C-B0-C2': 'Samsung',
        '7C-F8-54': 'Samsung',
        '80-18-A7': 'Samsung',
        '80-57-19': 'Samsung',
        '80-65-6D': 'Samsung',
        '80-7A-BF': 'Samsung',
        '84-00-D2': 'Samsung',
        '84-25-DB': 'Samsung',
        '84-38-38': 'Samsung',
        '84-51-81': 'Samsung',
        '88-32-9B': 'Samsung',
        '88-36-6C': 'Samsung',
        '88-BD-45': 'Samsung',
        '8C-77-12': 'Samsung',
        '8C-79-F5': 'Samsung',
        '8C-DE-F9': 'Samsung',
        '90-18-7C': 'Samsung',
        '90-61-AE': 'Samsung',
        '94-35-0A': 'Samsung',
        '94-51-03': 'Samsung',
        '94-63-D1': 'Samsung',
        '94-D7-29': 'Samsung',
        '98-0C-A5': 'Samsung',
        '98-52-B1': 'Samsung',
        '98-E8-FA': 'Samsung',
        '9C-02-98': 'Samsung',
        '9C-3A-AF': 'Samsung',
        '9C-E6-E7': 'Samsung',
        'A0-0B-BA': 'Samsung',
        'A0-21-95': 'Samsung',
        'A0-75-91': 'Samsung',
        'A0-82-1F': 'Samsung',
        'A4-EB-D3': 'Samsung',
        'A8-F2-74': 'Samsung',
        'AC-36-13': 'Samsung',
        'AC-5A-14': 'Samsung',
        'AC-5F-3E': 'Samsung',
        'AC-7F-3E': 'Samsung',
        'B0-72-BF': 'Samsung',
        'B0-EC-71': 'Samsung',
        'B4-07-F9': 'Samsung',
        'B4-79-A7': 'Samsung',
        'B8-5E-7B': 'Samsung',
        'BC-20-BA': 'Samsung',
        'BC-44-86': 'Samsung',
        'BC-72-B1': 'Samsung',
        'BC-76-70': 'Samsung',
        'BC-8C-CD': 'Samsung',
        'BC-B1-F3': 'Samsung',
        'C0-65-99': 'Samsung',
        'C0-BD-D1': 'Samsung',
        'C4-42-02': 'Samsung',
        'C4-57-6E': 'Samsung',
        'C4-73-1E': 'Samsung',
        'C8-19-F7': 'Samsung',
        'C8-3D-FC': 'Samsung',
        'C8-A8-23': 'Samsung',
        'C8-BA-94': 'Samsung',
        'CC-07-AB': 'Samsung',
        'CC-3A-61': 'Samsung',
        'CC-C7-60': 'Samsung',
        'CC-FE-3C': 'Samsung',
        'D0-22-BE': 'Samsung',
        'D0-25-98': 'Samsung',
        'D0-59-E4': 'Samsung',
        'D0-66-7B': 'Samsung',
        'D0-87-E2': 'Samsung',
        'D4-6A-6A': 'Samsung',
        'D4-87-D8': 'Samsung',
        'D4-88-90': 'Samsung',
        'D4-E8-B2': 'Samsung',
        'D8-31-CF': 'Samsung',
        'D8-57-EF': 'Samsung',
        'D8-90-E8': 'Samsung',
        'DC-71-44': 'Samsung',
        'E0-99-71': 'Samsung',
        'E4-12-1D': 'Samsung',
        'E4-32-CB': 'Samsung',
        'E4-3E-D7': 'Samsung',
        'E4-40-E2': 'Samsung',
        'E4-92-FB': 'Samsung',
        'E4-B0-21': 'Samsung',
        'E8-03-9A': 'Samsung',
        'E8-11-32': 'Samsung',
        'E8-50-8B': 'Samsung',
        'E8-E5-D6': 'Samsung',
        'EC-1D-8B': 'Samsung',
        'EC-9B-F3': 'Samsung',
        'F0-08-F1': 'Samsung',
        'F0-25-B7': 'Samsung',
        'F0-5A-09': 'Samsung',
        'F0-72-8C': 'Samsung',
        'F4-0E-01': 'Samsung',
        'F4-7B-5E': 'Samsung',
        'F4-90-EA': 'Samsung',
        'F8-04-2E': 'Samsung',
        'F8-D0-BD': 'Samsung',
        'FC-00-12': 'Samsung',
        'FC-03-9F': 'Samsung',
        'FC-A1-3E': 'Samsung',
        '00-0C-76': 'Hon Hai (Foxconn)',
        '00-16-B8': 'Hon Hai (Foxconn)',
        '00-1B-FC': 'Hon Hai (Foxconn)',
        '00-22-43': 'Hon Hai (Foxconn)',
        '00-24-1D': 'Hon Hai (Foxconn)',
        '00-90-26': 'Technicolor',
        '00-14-7D': 'Technicolor',
        '00-17-EE': 'Technicolor',
        '00-1F-1F': 'Technicolor',
        '00-24-17': 'Technicolor',
        '14-0C-76': 'Technicolor',
        '30-D9-D9': 'Technicolor',
        '44-00-10': 'Technicolor',
        '5C-F4-AB': 'Technicolor',
        '64-31-50': 'Technicolor',
        '68-A3-78': 'Technicolor',
        '84-1E-0D': 'Technicolor',
        '90-8D-78': 'Technicolor',
        'A4-42-3B': 'Technicolor',
        'B8-A3-86': 'Technicolor',
        'C4-71-54': 'Technicolor',
        'CC-05-2D': 'Technicolor',
        'E0-B9-4D': 'Technicolor',
        'E4-48-C7': 'Technicolor',
        '00-1A-79': 'Huawei',
        '00-25-9E': 'Huawei',
        '00-46-4B': 'Huawei',
        '00-66-4B': 'Huawei',
        '00-9A-CD': 'Huawei',
        '00-E0-FC': 'Huawei',
        '04-02-1F': 'Huawei',
        '04-6D-6C': 'Huawei',
        '0C-37-DC': 'Huawei',
        '0C-96-BF': 'Huawei',
        '10-51-72': 'Huawei',
        '10-C6-1F': 'Huawei',
        '18-0F-76': 'Huawei',
        '18-54-CF': 'Huawei',
        '1C-1D-67': 'Huawei',
        '1C-48-CE': 'Huawei',
        '1C-FA-68': 'Huawei',
        '20-08-ED': 'Huawei',
        '20-2B-C1': 'Huawei',
        '20-F3-A3': 'Huawei',
        '24-09-95': 'Huawei',
        '24-69-A5': 'Huawei',
        '28-31-52': 'Huawei',
        '28-6E-D4': 'Huawei',
        '2C-AB-25': 'Huawei',
        '30-3A-64': 'Huawei',
        '34-6B-D3': 'Huawei',
        '34-CD-BE': 'Huawei',
        '38-BC-01': 'Huawei',
        '3C-DF-BD': 'Huawei',
        '40-4D-8E': 'Huawei',
        '40-CB-A8': 'Huawei',
        '44-6E-E5': 'Huawei',
        '48-46-FB': 'Huawei',
        '48-DB-50': 'Huawei',
        '4C-54-99': 'Huawei',
        '50-2E-5C': 'Huawei',
        '54-25-EA': 'Huawei',
        '58-1F-28': 'Huawei',
        '58-2A-F7': 'Huawei',
        '5C-63-BF': 'Huawei',
        '60-DE-44': 'Huawei',
        '64-3E-8C': 'Huawei',
        '64-A6-51': 'Huawei',
        '68-3E-34': 'Huawei',
        '6C-4A-85': 'Huawei',
        '6C-96-CF': 'Huawei',
        '70-72-3C': 'Huawei',
        '74-A5-28': 'Huawei',
        '78-D7-52': 'Huawei',
        '7C-60-97': 'Huawei',
        '80-26-89': 'Huawei',
        '80-71-7A': 'Huawei',
        '80-FB-06': 'Huawei',
        '84-A8-E4': 'Huawei',
        '88-28-B3': 'Huawei',
        '88-CF-98': 'Huawei',
        '8C-34-FD': 'Huawei',
        '90-2E-16': 'Huawei',
        '90-67-1C': 'Huawei',
        '94-04-9C': 'Huawei',
        '98-52-3D': 'Huawei',
        '9C-28-EF': 'Huawei',
        'A0-C5-89': 'Huawei',
        'A4-C4-94': 'Huawei',
        'A8-16-B2': 'Huawei',
        'AC-4E-91': 'Huawei',
        'AC-85-3D': 'Huawei',
        'AC-E2-15': 'Huawei',
        'B4-CD-27': 'Huawei',
        'B8-08-CF': 'Huawei',
        'BC-25-E0': 'Huawei',
        'BC-76-5E': 'Huawei',
        'C0-18-50': 'Huawei',
        'C4-0B-CB': 'Huawei',
        'C8-14-79': 'Huawei',
        'C8-3A-35': 'Huawei',
        'C8-65-8F': 'Huawei',
        'CC-0E-DA': 'Huawei',
        'CC-B1-1A': 'Huawei',
        'D0-74-C2': 'Huawei',
        'D0-7E-35': 'Huawei',
        'D4-6E-0E': 'Huawei',
        'D4-F6-FC': 'Huawei',
        'D8-49-0B': 'Huawei',
        'D8-C7-71': 'Huawei',
        'DC-2C-26': 'Huawei',
        'DC-D9-16': 'Huawei',
        'E0-19-1D': 'Huawei',
        'E0-28-6D': 'Huawei',
        'E0-97-96': 'Huawei',
        'E4-36-14': 'Huawei',
        'E4-C1-46': 'Huawei',
        'E8-CD-2D': 'Huawei',
        'EC-23-3D': 'Huawei',
        'EC-38-8F': 'Huawei',
        'F0-B4-29': 'Huawei',
        'F4-4E-FC': 'Huawei',
        'F8-7B-8C': 'Huawei',
        'F8-E7-1E': 'Huawei',
        'FC-48-EF': 'Huawei',
        '18-A9-05': 'Google',
        '3C-5A-B4': 'Google',
        '54-60-09': 'Google',
        '6C-AD-F8': 'Google',
        '84-F5-A7': 'Google',
        'AC-CF-85': 'Google',
        'B4-F6-1C': 'Google',
        'C0-2F-2D': 'Google',
        'CC-C0-79': 'Google',
        'D0-2D-B3': 'Google',
        'DC-4F-22': 'Google',
        'F0-B0-E7': 'Google',
        'F4-F5-A5': 'Google',
        'F4-F5-D8': 'Google',
    }
    
    for prefix, vendor in oui_database.items():
        if mac_prefix.startswith(prefix):
            return vendor
    
    # Method 6: Extract from system OUI database file
    try:
        if os.path.exists('/usr/share/ieee-data/oui.txt'):
            with open('/usr/share/ieee-data/oui.txt', 'r') as f:
                content = f.read()
                mac_search = mac[:8].upper().replace(':', '-')
                if mac_search in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if mac_search in line and i + 2 < len(lines):
                            vendor = lines[i + 2].strip()
                            if vendor:
                                return vendor
    except:
        pass
    
    return 'Unknown'


def get_hostname_advanced(ip):
    """Advanced hostname detection using multiple methods"""
    hostname = "Unknown"
    
    # Method 1: DNS Reverse Lookup (fastest)
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        if hostname and hostname != ip and '.' in hostname:
            return hostname.split('.')[0]
    except:
        pass
    
    # Method 2: NBT-NS (NetBIOS Name Service) - nmblookup
    try:
        output = subprocess.check_output(['nmblookup', '-A', ip], timeout=2, stderr=subprocess.DEVNULL).decode()
        for line in output.split('\n'):
            if '<00>' in line and '<GROUP>' not in line and 'Looking up' not in line:
                parts = line.split()
                if len(parts) > 0:
                    name = parts[0].strip()
                    if name and name != ip and not name.startswith('..'):
                        return name
    except:
        pass
    
    # Method 3: nbtscan (faster NetBIOS scanner)
    try:
        output = subprocess.check_output(['nbtscan', '-r', ip], timeout=2, stderr=subprocess.DEVNULL).decode()
        for line in output.split('\n'):
            if ip in line:
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[1].strip()
                    if name and name != 'Sendto' and name != ip:
                        return name
    except:
        pass
    
    # Method 4: Direct NetBIOS query on port 137
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        
        # NetBIOS name query packet
        query = b'\xA2\x48\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x20'
        query += b'CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\x00\x00\x21\x00\x01'
        
        sock.sendto(query, (ip, 137))
        response = sock.recvfrom(1024)[0]
        sock.close()
        
        if len(response) > 56:
            name_data = response[56:72]
            name = name_data.decode('ascii', errors='ignore').strip()
            if name and len(name) > 0:
                return name.split('\x00')[0].strip()
    except:
        pass
    
    # Method 5: SMB/CIFS hostname
    try:
        output = subprocess.check_output(['smbclient', '-L', ip, '-N'], timeout=3, stderr=subprocess.DEVNULL).decode()
        for line in output.split('\n'):
            if 'Server=' in line or 'Workgroup=' in line:
                if 'Server=' in line:
                    parts = line.split('Server=')
                    if len(parts) > 1:
                        name = parts[1].split()[0].strip()
                        if name and name != ip:
                            return name
    except:
        pass
    
    # Method 6: SNMP system name
    try:
        output = subprocess.check_output(['snmpget', '-v2c', '-c', 'public', ip, 'sysName.0'], 
                                       timeout=2, stderr=subprocess.DEVNULL).decode()
        if 'STRING:' in output:
            name = output.split('STRING:')[1].strip().strip('"').strip()
            if name and name != ip:
                return name
    except:
        pass
    
    # Method 7: mDNS/Avahi (for local network devices)
    try:
        output = subprocess.check_output(['avahi-resolve', '-a', ip], timeout=2, stderr=subprocess.DEVNULL).decode()
        parts = output.strip().split()
        if len(parts) >= 2:
            name = parts[1].replace('.local', '').strip()
            if name and name != ip:
                return name
    except:
        pass
    
    # Method 8: Ping hostname resolution (Windows style)
    try:
        if sys.platform.startswith('win'):
            output = subprocess.check_output(['ping', '-a', '-n', '1', ip], 
                                           timeout=2, stderr=subprocess.DEVNULL).decode()
        else:
            output = subprocess.check_output(['ping', '-c', '1', ip], 
                                           timeout=2, stderr=subprocess.DEVNULL).decode()
        
        # Extract hostname from ping output
        for line in output.split('\n'):
            if ip in line and '[' not in line:
                match = re.search(r'from ([a-zA-Z0-9\-\_\.]+)', line)
                if match:
                    name = match.group(1)
                    if name and name != ip:
                        return name.split('.')[0]
    except:
        pass
    
    return hostname


def scan_ports_fast(ip):
    """Fast port scanning using multiple techniques"""
    common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306, 3389, 5432, 5900, 8080, 8443]
    open_ports = []
    
    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                return port
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_port, port) for port in common_ports]
        for future in as_completed(futures):
            result = future.result()
            if result:
                open_ports.append(str(result))
    
    return ', '.join(sorted(open_ports, key=int)) if open_ports else 'None'


def scan_ports_aggressive(ip):
    """Aggressive port scan (1-1024)"""
    open_ports = []
    
    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.2)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                return port
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_port, port) for port in range(1, 1025)]
        for future in as_completed(futures):
            result = future.result()
            if result:
                open_ports.append(str(result))
    
    return ', '.join(sorted(open_ports, key=int)) if open_ports else 'None'


def guess_os(ip):
    """Enhanced OS detection"""
    try:
        if sys.platform.startswith('win'):
            output = subprocess.check_output(['ping', '-n', '1', ip], timeout=2, stderr=subprocess.DEVNULL).decode().lower()
        else:
            output = subprocess.check_output(['ping', '-c', '1', ip], timeout=2, stderr=subprocess.DEVNULL).decode().lower()
        
        if 'ttl=128' in output or 'ttl=127' in output:
            return 'Windows'
        elif 'ttl=64' in output or 'ttl=63' in output:
            return 'Linux/Unix'
        elif 'ttl=255' in output or 'ttl=254' in output:
            return 'Router/Network Device'
        
        try:
            output = subprocess.check_output(['nmap', '-O', '--osscan-guess', ip], timeout=10, stderr=subprocess.DEVNULL).decode()
            if 'Running:' in output:
                os_line = [line for line in output.split('\n') if 'Running:' in line][0]
                return os_line.split('Running:')[1].strip()[:30]
        except:
            pass
            
        return 'Unknown'
    except:
        return 'Unknown'


def get_device_info(ip):
    """Get comprehensive device information"""
    info = {
        'manufacturer': 'Unknown',
        'device_type': 'Unknown',
        'services': []
    }
    
    try:
        ports_output = subprocess.check_output(['nmap', '-sV', '--version-intensity', '5', ip], 
                                               timeout=15, stderr=subprocess.DEVNULL).decode()
        
        for line in ports_output.split('\n'):
            if '/tcp' in line and 'open' in line:
                parts = line.split()
                if len(parts) >= 3:
                    service = ' '.join(parts[2:])
                    info['services'].append(service[:40])
        
        if 'printer' in ports_output.lower():
            info['device_type'] = 'Printer'
        elif 'router' in ports_output.lower() or 'gateway' in ports_output.lower():
            info['device_type'] = 'Router/Gateway'
        elif 'camera' in ports_output.lower() or 'rtsp' in ports_output.lower():
            info['device_type'] = 'IP Camera'
        elif 'nas' in ports_output.lower() or 'storage' in ports_output.lower():
            info['device_type'] = 'NAS/Storage'
        
    except:
        pass
    
    return info


def ai_analysis(ip, ports, os_type):
    """Enhanced AI vulnerability analysis"""
    insights = []
    risk_level = "🟢 Low"
    
    if '445' in ports or '139' in ports:
        insights.append("🛑 SMB/NetBIOS open — EternalBlue/SMBGhost risk")
        risk_level = "🔴 Critical"
    
    if '3389' in ports:
        insights.append("🔴 RDP exposed — brute force target")
        if risk_level == "🟢 Low":
            risk_level = "🟠 High"
    
    if '22' in ports:
        insights.append("⚠️  SSH open — ensure key-based auth")
    
    if '23' in ports:
        insights.append("🔴 Telnet detected — unencrypted protocol!")
        risk_level = "🔴 Critical"
    
    if '21' in ports:
        insights.append("⚠️  FTP open — check for anonymous access")
    
    if '3306' in ports:
        insights.append("⚠️  MySQL exposed — restrict access")
    
    if '5432' in ports:
        insights.append("⚠️  PostgreSQL open — verify permissions")
    
    if '80' in ports and '443' not in ports:
        insights.append("⚠️  HTTP only — no HTTPS encryption")
    
    if '8080' in ports or '8443' in ports:
        insights.append("ℹ️  Alt web port detected — admin panel?")
    
    if '5900' in ports:
        insights.append("🔴 VNC exposed — screen sharing vulnerability")
        risk_level = "🔴 Critical"
    
    if os_type == 'Windows':
        if '135' in ports:
            insights.append("⚠️  RPC open — potential attack vector")
        if '5985' in ports or '5986' in ports:
            insights.append("ℹ️  WinRM detected — PowerShell remoting")
    
    if ports == 'None':
        insights.append("🟢 No open ports — firewall active or offline")
        risk_level = "🟢 Low"
    
    if not insights:
        insights.append("🔍 No major vulnerabilities detected")
    
    return f"{risk_level} | " + ' | '.join(insights)


def scan(ip_range, delay=0, aggressive=False):
    """Enhanced network scan with parallel processing"""
    devices = []
    print(f"\n🔍 Scanning {ip_range}...")
    
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp
    
    print("📡 Sending ARP requests...")
    answered, _ = srp(packet, timeout=3, verbose=0, retry=2)
    
    total = len(answered)
    print(f"✅ Found {total} active device(s)\n")
    
    if total == 0:
        return devices
    
    def process_device(sent, received):
        ip = received.psrc
        mac = received.hwsrc
        
        print(f"🔎 Analyzing {ip}...")
        
        hostname = get_hostname_advanced(ip)
        vendor = get_mac_vendor(mac)
        
        if aggressive:
            ports = scan_ports_aggressive(ip)
        else:
            ports = scan_ports_fast(ip)
        
        os_type = guess_os(ip)
        ai_recon = ai_analysis(ip, ports, os_type)
        
        device_info = get_device_info(ip)
        
        if delay > 0:
            time.sleep(delay)
        
        return {
            'ip': ip,
            'mac': mac,
            'hostname': hostname,
            'vendor': vendor,
            'ports': ports,
            'os': os_type,
            'ai': ai_recon,
            'device_type': device_info['device_type'],
            'services': ', '.join(device_info['services'][:3]) if device_info['services'] else 'N/A'
        }
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_device, sent, received) for sent, received in answered]
        for future in as_completed(futures):
            try:
                device = future.result()
                devices.append(device)
            except Exception as e:
                print(f"⚠️  Error processing device: {e}")
    
    return devices


def monitor(ip_range):
    """Enhanced monitoring mode"""
    print("🛰️  Monitoring mode activated. Press Ctrl+C to stop.")
    known = {}
    scan_count = 0
    
    try:
        while True:
            scan_count += 1
            print(f"\n📊 Scan #{scan_count} - {time.strftime('%H:%M:%S')}")
            
            devices = scan(ip_range)
            current = {d['ip']: d for d in devices}
            
            new_ips = set(current.keys()) - set(known.keys())
            for ip in new_ips:
                device = current[ip]
                print(f"🆕 NEW: {ip} | {device['hostname']} | {device['mac']} | {device['vendor']}")
            
            gone_ips = set(known.keys()) - set(current.keys())
            for ip in gone_ips:
                device = known[ip]
                print(f"❌ LEFT: {ip} | {device['hostname']} | {device['mac']}")
            
            for ip in set(current.keys()) & set(known.keys()):
                if current[ip]['mac'] != known[ip]['mac']:
                    print(f"⚠️  MAC CHANGED: {ip} | {known[ip]['mac']} → {current[ip]['mac']}")
            
            known = current
            
            print(f"\n💤 Sleeping 15 seconds... (Total devices: {len(known)})")
            time.sleep(15)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped.")
        print(f"📊 Total scans: {scan_count} | Final device count: {len(known)}")


def display(devices, scan_time):
    """Enhanced display with more information"""
    table = PrettyTable()
    table.field_names = ['IP', 'MAC', 'Hostname', 'Vendor', 'Ports', 'OS', 'AI Security Analysis']
    table.max_width = 150
    table.align = 'l'
    
    for d in devices:
        table.add_row([
            d['ip'],
            d['mac'],
            d['hostname'][:20],
            d['vendor'][:25],
            d['ports'][:30],
            d['os'][:15],
            d['ai'][:60]
        ])
    
    print("\n" + "="*150)
    print("📡 SCAN RESULTS")
    print("="*150)
    print(table)
    print("\n" + "="*150)
    print(f"🟢 Total Devices: {len(devices)}")
    print(f"⏱️  Scan Time: {round(scan_time, 2)} seconds")
    print(f"⚡ Speed: {round(len(devices)/scan_time, 2)} devices/sec")
    
    critical = sum(1 for d in devices if '🔴 Critical' in d['ai'])
    high = sum(1 for d in devices if '🟠 High' in d['ai'])
    
    if critical > 0:
        print(f"🔴 CRITICAL RISKS: {critical} device(s)")
    if high > 0:
        print(f"🟠 HIGH RISKS: {high} device(s)")
    
    print("="*150 + "\n")


def save_results(devices, filename="scan_results.json"):
    """Save scan results to JSON file"""
    try:
        import json
        with open(filename, 'w') as f:
            json.dump(devices, f, indent=4)
        print(f"💾 Results saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")


def main():
    """Main execution function"""
    show_banner()
    
    choice = menu()
    
    if choice == '1':
        target = input("🌐 Enter Target IP Range (e.g., 192.168.1.1/24): ")
        start = time.time()
        results = scan(target)
        end = time.time()
        display(results, end - start)
        
        save = input("\n💾 Save results? (y/n): ")
        if save.lower() == 'y':
            save_results(results)
        
    elif choice == '2':
        activate_stealth_mode()
        target = input("🌐 Enter Target IP Range: ")
        start = time.time()
        results = scan(target, delay=0.5)
        end = time.time()
        display(results, end - start)
        restore_mac()
        
        save = input("\n💾 Save results? (y/n): ")
        if save.lower() == 'y':
            save_results(results)
        
    elif choice == '3':
        target = input("🌐 Enter Target IP Range: ")
        monitor(target)
        
    elif choice == '4':
        print("\n⚠️  AGGRESSIVE MODE - This will scan 1-1024 ports per device")
        confirm = input("Continue? (y/n): ")
        if confirm.lower() == 'y':
            target = input("🌐 Enter Target IP Range: ")
            start = time.time()
            results = scan(target, aggressive=True)
            end = time.time()
            display(results, end - start)
            
            save = input("\n💾 Save results? (y/n): ")
            if save.lower() == 'y':
                save_results(results)
    else:
        print("❌ Invalid option.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Scan interrupted by user")
        restore_mac()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        restore_mac()
