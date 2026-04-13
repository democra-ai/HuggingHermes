import subprocess
import sys

if __name__ == "__main__":
    print("Starting HuggingHermes Sync Wrapper...")
    subprocess.run([sys.executable, "scripts/sync_hf.py"], check=True)
