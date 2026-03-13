#!/usr/bin/env python3
"""
TESTING ONLY - Temporary payment bypass to test processing pipeline
This will be removed after testing is complete
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def temporarily_disable_payments():
    """Temporarily disable payments for testing purposes."""
    config_path = Path("src/config.py")
    
    # Read current config
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Backup original
    with open(f"{config_path}.backup", 'w') as f:
        f.write(content)
    
    # Comment out stripe keys to disable payments
    modified_content = content.replace(
        'stripe_secret_key: Optional[str] = None',
        'stripe_secret_key: Optional[str] = "" # Disabled for testing'
    ).replace(
        'stripe_publishable_key: Optional[str] = None',
        'stripe_publishable_key: Optional[str] = "" # Disabled for testing'
    )
    
    with open(config_path, 'w') as f:
        f.write(modified_content)
    
    print("✅ Payments temporarily disabled for testing")
    return True

def restore_payments():
    """Restore original payment configuration."""
    config_path = Path("src/config.py")
    backup_path = Path(f"{config_path}.backup")
    
    if backup_path.exists():
        with open(backup_path, 'r') as f:
            content = f.read()
        
        with open(config_path, 'w') as f:
            f.write(content)
        
        backup_path.unlink()  # Remove backup
        print("✅ Payment configuration restored")
        return True
    
    return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_payments()
    else:
        temporarily_disable_payments()