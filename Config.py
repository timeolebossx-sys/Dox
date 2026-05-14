#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import re
import socket
import subprocess
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
import argparse
import os
import sys

init()

class Colors:
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    RESET = Style.RESET_ALL

class DoxEngine:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        
    def banner(self):
        print(f"""{Colors.CYAN}
    ██████╗  ██████╗ ████████╗██╗  ██╗
    ██╔══██╗██╔═══██╗╚══██╔══╝██║  ██║
    ██║  ██║██║   ██║   ██║   ███████║
    ██║  ██║██║   ██║   ██║   ██╔══██║
    ██████╔╝╚██████╔╝   ██║   ██║  ██║
    ╚═════╝  ╚═════╝    ╚═╝   ╚═╝  ╚═╝
    {Colors.GREEN}OSINT & Doxxing Engine v2.1{Colors.RESET}
        """)

    def search_email(self, email):
        print(f"\n{Colors.YELLOW}[+] Recherche breaches pour: {email}{Colors.RESET}")
        
        # HaveIBeenPwned via tor
        try:
            tor_session = requests.Session()
            tor_session.proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }
            
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
            response = tor_session.get(url, timeout=10)
            
            if response.status_code == 200:
                breaches = response.json()
                print(f"{Colors.GREEN}[✓] {len(breaches)} breaches trouvées:{Colors.RESET}")
                for breach in breaches:
                    print(f"  - {breach['Name']} ({breach['BreachDate']})")
            else:
                print(f"{Colors.RED}[-] Aucune breach trouvée{Colors.RESET}")
                
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur HIBP: {e}{Colors.RESET}")

    def social_search(self, username):
        print(f"\n{Colors.YELLOW}[+] Recherche profils sociaux: {username}{Colors.RESET}")
        
        platforms = {
            'instagram': f'https --proto=https instagram.com/{username}',
            'twitter': f'https://twitter.com/{username}',
            'facebook': f'https://facebook.com/{username}',
            'github': f'https://github.com/{username}',
            'linkedin': f'https://linkedin.com/in/{username}',
            'reddit': f'https://reddit.com/user/{username}',
            'tiktok': f'https://tiktok.com/@{username}'
        }
        
        found = []
        for platform, url in platforms.items():
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code == 200 and username.lower() in response.text.lower():
                    found.append(platform)
                    print(f"{Colors.GREEN}[✓] {platform}: {url}{Colors.RESET}")
            except:
                continue
        
        if not found:
            print(f"{Colors.RED}[-] Aucun profil trouvé{Colors.RESET}")

    def phone_lookup(self, phone):
        print(f"\n{Colors.YELLOW}[+] Lookup téléphone: {phone}{Colors.RESET}")
        
        # Format standardisation
        phone = re.sub(r'\D', '', phone)
        
        # API free lookup
        try:
            url = f"https://phonevalidation.abstractapi.com/v1/"
            params = {"api_key": "demo_key", "phone": phone}
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print(f"{Colors.GREEN}Pays: {data.get('country_name', 'N/A')}{Colors.RESET}")
                print(f"{Colors.GREEN}Opérateur: {data.get('carrier', 'N/A')}{Colors.RESET}")
        except:
            print(f"{Colors.RED}[-] Lookup échoué{Colors.RESET}")

    def ip_lookup(self, ip):
        print(f"\n{Colors.YELLOW}[+] Lookup IP: {ip}{Colors.RESET}")
        
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,isp,org,as")
            data = response.json()
            
            if data['status'] == 'success':
                print(f"{Colors.GREEN}[✓] Localisation IP:{Colors.RESET}")
                print(f"  Pays: {data['country']}")
                print(f"  Région: {data['regionName']}")
                print(f"  Ville: {data['city']}")
                print(f"  ISP: {data['isp']}")
                print(f"  Org: {data['org']}")
            else:
                print(f"{Colors.RED}[-] IP invalide{Colors.RESET}")
        except:
            print(f"{Colors.RED}[-] Erreur IP lookup{Colors.RESET}")

    def domain_info(self, domain):
        print(f"\n{Colors.YELLOW}[+] Info domaine: {domain}{Colors.RESET}")
        
        # WHOIS via subprocess
        try:
            whois = subprocess.check_output(['whois', domain], stderr=subprocess.DEVNULL).decode()
            registrar = re.search(r'Registrar:\s*(.+)', whois)
            if registrar:
                print(f"{Colors.GREEN}Registrar: {registrar.group(1)}{Colors.RESET}")
        except:
            pass
        
        # DNS lookup
        try:
            dns = subprocess.check_output(['dig', domain, '+short'], stderr=subprocess.DEVNULL).decode()
            ips = dns.strip().split('\n')
            if ips:
                print(f"{Colors.GREEN}IPs: {',}{Colors.RESET}")
        except:
            pass

    def google_dorking(self, query):
        print(f"\n{Colors.YELLOW}[+] Google Dorking: {query}{Colors.RESET}")
        
        dorks = [
            f'site:facebook.com "{query}"',
            f'site:twitter.com "{query}"',
            f'site:linkedin.com "{query}"',
            f'site:instagram.com "{query}"',
            f'"{query}" filetype:pdf',
            f'"{query}" site:pastebin.com',
            f'intext:"{query}" site:leak-lookup.com'
        ]
        
        for dork in dorks:
            print(f"{Colors.CYAN}  → {dork}{Colors.RESET}")

    def export_json(self, data, filename):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"\n{Colors.GREEN}[✓] Exporté vers {filename}{Colors.RESET}")

    def run(self, target, target_type):
        self.banner()
        
        results = {
            'target': target,
            'type': target_type,
            'timestamp': str(subprocess.check_output(['date']).decode().strip())
        }
        
        if target_type == 'email':
            self.search_email(target)
            results['breaches'] = []
            
        elif target_type == 'username':
            self.social_search(target)
            results['profiles'] = []
            
        elif target_type == 'phone':
            self.phone_lookup(target)
            results['phone_info'] = {}
            
        elif target_type == 'ip':
            self.ip_lookup(target)
            results['ip_info'] = {}
            
        elif target_type == 'domain':
            self.domain_info(target)
            results['domain_info'] = {}
            
        # Google dorking toujours
        self.google_dorking(target)
        
        # Export
        self.export_json(results, f"results_{target.replace('@', '_').replace()}_{target_type}.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Doxxing Engine')
    parser.add_argument('target', help='Cible à rechercher')
    parser.add_argument('-t', '--type', choices=['email', 'username', 'phone', 'ip', 'domain'], 
                       required=True, help='Type de cible')
    
    args = parser.parse_args()
    
    # Vérifier tor
    try:
        subprocess.check_output(['systemctl', 'is-active', 'tor'])
    except:
        print(f"{Colors.RED}[!] Tor n'est pas actif. Lancez: sudo systemctl start tor{Colors.RESET}")
        sys.exit(1)
    
    engine = DoxEngine()
    engine.run(args.target, args.type)
