"""
Monitor training progress by checking output directory for artifacts.
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime

def monitor_training(output_dir='./training_output', check_interval=30, max_checks=60):
    """Monitor training progress by checking for output files"""

    print(f"Monitoring training in {output_dir}/")
    print(f"Checking every {check_interval} seconds (max {max_checks} checks)")
    print("=" * 70)

    checks = 0
    while checks < max_checks:
        checks += 1
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Check #{checks}:")

        # Check for model files
        best_model = Path(output_dir) / 'best_model.pth'
        final_model = Path(output_dir) / 'final_model.pth'
        history_file = Path(output_dir) / 'training_history.json'

        if best_model.exists():
            size = best_model.stat().st_size / (1024 * 1024)
            mtime = best_model.stat().st_mtime
            print(f"  ✓ best_model.pth found ({size:.2f} MB, modified {time.ctime(mtime)})")
        else:
            print(f"  ✗ best_model.pth not found yet")

        if final_model.exists():
            size = final_model.stat().st_size / (1024 * 1024)
            mtime = final_model.stat().st_mtime
            print(f"  ✓ final_model.pth found ({size:.2f} MB, modified {time.ctime(mtime)})")
        else:
            print(f"  ✗ final_model.pth not found yet")

        if history_file.exists():
            print(f"  ✓ training_history.json found")
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
                    metadata = history.get('metadata', {})
                    epochs = metadata.get('completed_epochs', 0)
                    best_epoch = metadata.get('best_epoch', 0)
                    best_loss = metadata.get('best_val_loss', 0)
                    print(f"    Completed epochs: {epochs}")
                    print(f"    Best epoch: {best_epoch}, Best val_loss: {best_loss:.6f}")

                    if epochs > 0:
                        print("\n  Training has completed!")
                        return True
            except Exception as e:
                print(f"    Error reading history: {e}")
        else:
            print(f"  ✗ training_history.json not found yet")

        # Check if training is still running
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'train_fixed.py' in result.stdout:
            print("  Status: Training process is still running")
        else:
            print("  Status: Training process has finished")
            print("\n  Waiting for files to be written...")
            time.sleep(5)
            break

        if checks < max_checks:
            time.sleep(check_interval)

    print("\n" + "=" * 70)
    print("Monitoring complete.")
    return False

if __name__ == '__main__':
    monitor_training(check_interval=30, max_checks=60)
