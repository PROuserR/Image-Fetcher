#!/usr/bin/env python3
"""One-click local launcher: installs missing packages, starts the server, opens your browser."""
import importlib
import os
import socket
import subprocess
import sys
import threading
import webbrowser


def ensure_dependencies():
    needed = [("flask", "flask"), ("requests", "requests"), ("bs4", "beautifulsoup4")]
    missing = []
    for module, package in needed:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)
    if missing:
        print("Installing required packages: " + ", ".join(missing))
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        except subprocess.CalledProcessError:
            print("\nCould not install packages automatically. Run this manually:")
            print("  {} -m pip install {}".format(sys.executable, " ".join(missing)))
            sys.exit(1)


def find_port(preferred=5000):
    for port in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    ensure_dependencies()
    from imagefetcher import create_app

    app = create_app()
    settings = app.extensions["imagefetcher"].settings
    if settings.hosted:
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), threaded=True)
        return
    port = find_port()
    url = "http://127.0.0.1:{}".format(port)
    print("\n  Image Fetcher is running at {}".format(url))
    print("  (opening your browser - press Ctrl+C here to quit)\n")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
