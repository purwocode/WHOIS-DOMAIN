import whois
import socket
import requests
import os
import concurrent.futures
import signal
import time

stop_requested = False

# Handle CTRL+C
def signal_handler(sig, frame):
    global stop_requested
    print("\n[CTRL+C] Apakah anda ingin menghentikan proses? (Y/N): ", end="")
    choice = input().strip().lower()
    if choice == 'y':
        print("Menghentikan proses...")
        stop_requested = True
    else:
        print("Lanjutkan proses...")

signal.signal(signal.SIGINT, signal_handler)

# Baca file list domain
file_name = input("Masukkan file list: ").strip()

# Function proses 1 domain
def process_domain(domain_name):
    global stop_requested
    if stop_requested:
        return

    try:
        socket.setdefaulttimeout(10)  # Timeout DNS lookup
        ip_address = socket.gethostbyname(domain_name)

        # IP Location pakai ip-api.com
        resp = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=10)
        ip_data = resp.json()

        country = ip_data.get('country', 'Unknown')

        # Output ke layar (optional, kalau mau tetap lihat WHOIS bisa ditambahin)
        print(f"{domain_name} => {country}")

        # Simpan ke per-negara .txt (isi: domain => country)
        result_file = os.path.join('result', f"{country}.txt")
        with open(result_file, 'a', encoding='utf-8') as out_file:
            out_file.write(f"{domain_name} => {country}\n")

        # Delay supaya aman
        time.sleep(1.5)

    except socket.timeout:
        print(f"{domain_name} => [ Dead Site ]")

    except requests.exceptions.Timeout:
        print(f"{domain_name} => [ Dead Site ]")

    except socket.gaierror as e:
        if e.errno == 11001:
            print(f"{domain_name} => [ Dead Site ]")
        else:
            if 'label empty or too long' in str(e):
                print(f"{domain_name} => [ Format Salah ]")
            else:
                print(f"{domain_name} => Error: {e}")

    except Exception as e:
        if 'label empty or too long' in str(e):
            print(f"{domain_name} => [ Format Salah ]")
        else:
            print(f"{domain_name} => Error: {e}")

try:
    with open(file_name, 'r') as file:
        domain_list = [line.strip() for line in file if line.strip()]

    if not os.path.exists('result'):
        os.makedirs('result')

    print(f"\nMemproses {len(domain_list)} domain (save: domain => country)...\n")

    max_threads = 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_domain, domain) for domain in domain_list]

        for future in concurrent.futures.as_completed(futures):
            if stop_requested:
                break

except FileNotFoundError:
    print(f"File '{file_name}' tidak ditemukan.")
except Exception as e:
    print(f"Terjadi error: {e}")
