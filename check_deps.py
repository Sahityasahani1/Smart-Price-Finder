"""
Run this to check if all required packages are installed.
Usage: venv\Scripts\python.exe check_deps.py
"""
missing = []
packages = ["fastapi", "uvicorn", "httpx", "bs4", "lxml"]

for pkg in packages:
    try:
        __import__(pkg)
        print(f"  [OK]  {pkg}")
    except ImportError:
        print(f"  [MISSING]  {pkg}")
        missing.append(pkg)

if missing:
    print(f"\nMissing packages: {', '.join(missing)}")
    print("Run:  pip install fastapi uvicorn httpx beautifulsoup4 lxml")
else:
    print("\nAll packages OK! You can start the server.")
