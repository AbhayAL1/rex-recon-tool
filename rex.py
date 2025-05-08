#!/usr/bin/env python3

import os
import subprocess
from shutil import which
import platform
import shutil
import argparse
from datetime import datetime

def clear_terminal():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def banner():
    print(r"""
          __
         / ')
  .-^^^-/ /
 __/       /
<__.|_|_|_|
  _____  ______  __   __
 |  __ \|  ____| \ \ / /
 | |__) | |__     \ V / 
 |  _  /|  __|     > <  
 | | \ \| |____   / . \ 
 |_|  \_\______| /_/ \_\

         REX Recon Tool by ABHAY A L
    """)

# GitHub install paths for tools
GO_TOOLS = {
    "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    "assetfinder": "github.com/tomnomnom/assetfinder@latest",
    "httpx": "github.com/projectdiscovery/httpx/cmd/httpx@latest",
    "gau": "github.com/lc/gau@latest",
    "katana": "github.com/projectdiscovery/katana/cmd/katana@latest",
    "urlfinder": "github.com/projectdiscovery/urlfinder/cmd/urlfinder@latest",
    "hakrawler": "github.com/hakluke/hakrawler@latest",
    "uro": "github.com/s0md3v/uro@latest"
}

def is_tool_installed(tool):
    return shutil.which(tool) is not None

def install_tool(tool):
    print(f"[+] Installing {tool} using go...")
    try:
        subprocess.run(f"go install {GO_TOOLS[tool]}", shell=True, check=True)
        print(f"[i] Please ensure ~/go/bin is in your PATH to run {tool}.")
    except subprocess.CalledProcessError:
        print(f"[!] Failed to install {tool}. Please install manually.")

def check_and_install_tools(auto_install=False):
    if not is_tool_installed("go"):
        print("[!] Go is not installed. Please install Go first from https://golang.org/dl/")
        exit(1)

    for tool in GO_TOOLS:
        if is_tool_installed(tool):
            print(f"[+] {tool} is already installed.")
        else:
            print(f"[!] {tool} not found.")
            if auto_install:
                install_tool(tool)
            else:
                install = input(f"Do you want to install {tool}? [Y/n]: ").strip().lower()
                if install in ["", "y", "yes"]:
                    install_tool(tool)
                else:
                    print(f"[!] Skipping {tool}. This may cause errors if required.")

def get_output_directory(cli_dir=None):
    if cli_dir:
        directory = cli_dir
    else:
        directory = input("Enter the full path to store results: ").strip()
    if not os.path.exists(directory):
        os.makedirs(directory)
    os.chdir(directory)
    return os.getcwd()

def get_domains(domains_file=None):
    domains = []
    if domains_file:
        with open(domains_file) as f:
            domains = [line.strip() for line in f if line.strip()]
    else:
        print("Enter target domains (one per line). Enter an empty line to finish:")
        while True:
            d = input("> ").strip()
            if d == "":
                break
            domains.append(d)
    if not domains:
        print("No domains entered. Exiting.")
        exit(1)
    return domains

def run_command(command, verbose=True):
    print(f"[+] Running: {command}")
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE if not verbose else None)
    except subprocess.CalledProcessError as e:
        print(f"[!] Command failed: {e}")

def main():
    args = parse_args()
    clear_terminal()
    banner()
    check_and_install_tools(auto_install=args.auto_install)
    base_dir = get_output_directory(args.output_dir)
    domains = get_domains(args.domains_file)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_prefix = f"session_{timestamp}"
    os.makedirs(session_prefix, exist_ok=True)
    os.chdir(session_prefix)

    with open("subraw", "w") as f:
        for d in domains:
            f.write(f"{d}\n")

    with open("log.txt", "w") as log:
        log.write(f"Domains: {', '.join(domains)}\n")
        log.write(f"Base directory: {base_dir}\n")

    run_command("subfinder -dL subraw -o s1")
    sub_files = ["s1"]
    for i, domain in enumerate(domains, start=2):
        outfile = f"s{i}"
        run_command(f"assetfinder --subs-only {domain} > {outfile}")
        sub_files.append(outfile)

    sort_command = f"sort -u {' '.join(sub_files)} -o uniqsubs.txt"
    run_command(sort_command)
    run_command("cat uniqsubs.txt | httpx -o finallist.txt")
    run_command("cat finallist.txt | hakrawler > urls4.txt")
    run_command("cat finallist.txt | katana -d 2 -o urls2.txt")
    run_command("cat finallist.txt | gau --o urls1.txt")
    run_command("cat finallist.txt | urlfinder -o urls3.txt")
    run_command("cat urls1.txt urls2.txt urls3.txt urls4.txt | uro | sort -u | tee final.txt")

    print(f"[+] Recon complete. Final URLs saved to {os.path.join(base_dir, session_prefix, 'final.txt')}")

def parse_args():
    parser = argparse.ArgumentParser(description="REX Recon Tool by Abhay A L")
    parser.add_argument("-d", "--domains-file", help="File with domains (one per line)", required=False)
    parser.add_argument("-o", "--output-dir", help="Directory to store results", required=False)
    parser.add_argument("--auto-install", help="Auto-install missing tools without prompts", action="store_true")
    return parser.parse_args()

if __name__ == "__main__":
    main()
