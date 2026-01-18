import os
import sys
import configparser

def check_config():
    print("=== Config Verification Script ===")
    
    # 1. Check CWD
    cwd = os.getcwd()
    print(f"Current Working Directory: {cwd}")
    
    # 2. List files
    print("\nFiles in current directory:")
    try:
        files = os.listdir(cwd)
        for f in files:
            print(f" - {f}")
    except Exception as e:
        print(f"Error listing directory: {e}")
        
    config_path = os.path.join(cwd, 'config.ini')
    example_config_path = os.path.join(cwd, 'example_config.ini')
    
    # 3. Check specific file existence
    print(f"\nChecking for 'config.ini' at: {config_path}")
    if os.path.exists(config_path):
        print(" -> config.ini FOUND.")
    else:
        print(" -> config.ini NOT FOUND.")
        if os.path.exists(example_config_path):
             print(" -> 'example_config.ini' FOUND. Did you forget to rename/copy it?")
        else:
             print(" -> neither config.ini nor example_config.ini found.")
        return

    # 4. Attempt Parsing
    print("\nAttempting to parse config.ini...")
    config = configparser.ConfigParser()
    try:
        read_files = config.read(config_path)
        if not read_files:
            print(" -> ConfigParser returned empty list! File might be empty or unreadable.")
        else:
            print(f" -> Successfully read: {read_files}")
            
        print("\nSections found:")
        sections = config.sections()
        if not sections:
            print(" -> NO SECTIONS FOUND. Check file encoding or format.")
        for section in sections:
            print(f" [{section}]")
            
        # 5. Check for 'menu' section specifically
        if 'menu' in config:
            print("\n[menu] section content:")
            for key in config['menu']:
                print(f" {key} = {config['menu'][key]}")
        else:
            print("\n[ERROR] 'menu' section MISSING in config.ini")

    except Exception as e:
        print(f"\n[CRITICAL] Error parsing config: {e}")

if __name__ == "__main__":
    check_config()
