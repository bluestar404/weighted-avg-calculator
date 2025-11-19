import psutil
import subprocess
import time

TARGET_PROCESS = "WhatsApp.exe"
CHECK_INTERVAL = 5  # seconds

def kill_process_by_name(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(proc.info['pid'])], check=True)
                print(f"Killed {process_name} (PID: {proc.info['pid']})")
            except subprocess.CalledProcessError as e:
                print(f"Failed to kill {process_name}: {e}")

def main():
    print(f"Monitoring for {TARGET_PROCESS}... (Press Ctrl+C to stop)")
    while True:
        kill_process_by_name(TARGET_PROCESS)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
