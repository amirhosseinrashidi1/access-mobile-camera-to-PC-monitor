import requests
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
import socket
from concurrent.futures import ThreadPoolExecutor

def scan_ip(ip_range, port):
    """Scan the given IP range for devices with the specified port open."""
    active_ips = []

    def check_ip(ip):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex((ip, port)) == 0:
                    active_ips.append(ip)
        except Exception:
            pass

    
    with ThreadPoolExecutor(max_workers=50) as executor:
        for i in range(1, 255):
            executor.submit(check_ip, f"{ip_range}.{i}")

    return active_ips

def start_stream(selected_ip):
    """Start video stream from the selected IP."""
    url = f"http://{selected_ip}:8080/shot.jpg"

    while True:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                video = np.array(bytearray(response.content), dtype=np.uint8)
                render = cv2.imdecode(video, -1)

                cv2.imshow('Camera Stream', render)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print(f"Error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            break

    cv2.destroyAllWindows()

def on_scan():
    """Scan for available IPs and update the listbox."""
    scan_button.config(state=tk.DISABLED)
    ip_range = auto_detect_ip_range()
    if not ip_range:
        messagebox.showerror("Error", "Could not detect IP range.")
        scan_button.config(state=tk.NORMAL)
        return

    try:
        discovered_ips = scan_ip(ip_range, 8080)
        ip_listbox.delete(0, tk.END)  
        if discovered_ips:
            for ip in discovered_ips:
                ip_listbox.insert(tk.END, ip)  
            messagebox.showinfo("Scan Complete", f"Found {len(discovered_ips)} devices.")
        else:
            messagebox.showinfo("Scan Complete", "No devices found.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        scan_button.config(state=tk.NORMAL)

def on_start():
    """Start the stream for the selected IP."""
    selected_ip = ip_listbox.get(tk.ACTIVE)  
    if not selected_ip:
        messagebox.showerror("Error", "Please select an IP address.")
        return

    start_stream(selected_ip)

def auto_detect_ip_range():
    """Auto-detect the local IP range (e.g., 192.168.x.x)."""
    try:
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('10.254.254.254', 1))  
        local_ip = s.getsockname()[0]
        s.close()
        
        
        ip_parts = local_ip.split('.')[:3]
        return '.'.join(ip_parts)  
    
    except Exception:
        return None

def scan_public_ips():
    """Scan a wider range of public IPs and check for open ports."""
    active_ips = []

    
    public_ranges = [
        "21.250", "22.250", "23.250",  
        "24.250", "25.250", "26.250"
    ]

    
    for range_prefix in public_ranges:
        try:
            discovered_ips = scan_ip(range_prefix, 8080)
            active_ips.extend(discovered_ips)
        except Exception as e:
            print(f"Error scanning range {range_prefix}: {e}")
    
    return active_ips


root = tk.Tk()
root.title("IP Camera Viewer")
root.geometry("500x300")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))


ip_label = ttk.Label(frame, text="Scanning for IPs...")
ip_label.grid(row=0, column=0, sticky=tk.W, pady=5)

scan_button = ttk.Button(frame, text="Scan", command=on_scan)
scan_button.grid(row=1, column=1, pady=5)


ip_listbox = tk.Listbox(frame, height=10, width=50)
ip_listbox.grid(row=2, column=0, columnspan=3, pady=10)

start_button = ttk.Button(frame, text="Start Stream", command=on_start)
start_button.grid(row=3, column=1, pady=10)

root.mainloop()
