import importlib
import importlib.metadata
import os
import subprocess
import sys
from pathlib import Path


def test():
    print("Hello, World!")


def check_deps():
    # Map distribution/package names to import module names used in code
    deps = {
        "google-genai": "google.genai",
        "python-dotenv": "dotenv",
        "textual-dev": "textual",
        "fastmcp": "fastmcp",
        "streamlit": "streamlit",
        "httpx": "httpx",
        "uvicorn": "uvicorn",
        "gradio": "gradio",
    }

    missing = []
    versions = {}

    for dist_name, module_name in deps.items():
        try:
            importlib.import_module(module_name)
        except Exception:
            missing.append(f"{dist_name} (import '{module_name}')")
            continue

        try:
            versions[dist_name] = importlib.metadata.version(dist_name)
        except Exception:
            versions[dist_name] = "unknown"

    return missing, versions


def check_health() -> bool:
    print("Checking environment and dependencies...\n")

    print(f"Python Version: {sys.version}")

    missing, versions = check_deps()
    print("Dependencies:")
    if not versions:
        print("  - No dependencies detected (unexpected)")
    else:
        for dist, ver in sorted(versions.items()):
            print(f"  - {dist}: {ver}")

    try:
        from dotenv import find_dotenv, load_dotenv
    except Exception:
        print("\nCould not import python-dotenv. Skipping .env load.")

    env_file = find_dotenv()

    if env_file:
        print(f"\n.env file detected at: {env_file}")
    else:
        print("\nNo .env file detected.")

    load_dotenv()

    env_needed = ["GEMINI_API_KEY", "OPENWEATHER_API_KEY"]
    env_status = {
        k: (os.getenv(k) is not None and len(os.getenv(k) or "") > 0)
        for k in env_needed
    }

    if missing:
        print("\nMissing dependencies:")
        for item in missing:
            print(f"  - {item}")
        print("\nTo install missing packages with uv:")

        pkgs = " ".join([m.split(" ")[0] for m in missing])
        if pkgs:
            print(f"  uv add {pkgs}")
    else:
        print("\nAll required dependencies are installed.")

    print("\nEnvironment variables:")
    for k in env_needed:
        print(f"  - {k}: {'set' if env_status[k] else 'MISSING'}")

    if not all(env_status.values()):
        print("\nTo set environment variables in a .env file:")
        print('  echo "GEMINI_API_KEY=your_key" >> .env')
        print('  echo "OPENWEATHER_API_KEY=your_key" >> .env')

    ok = not missing and all(env_status.values())

    print("\nSummary: " + ("OK" if ok else "Issues found"))
    return ok


# Optional alias
def checkhealth():
    return check_health()


def run_llm_app():
    app_path = Path(__file__).parent / "level1" / "llm_call.py"
    cmds = ["textual", "run", str(app_path)]
    subprocess.run(cmds)


def run_pdf_reader():
    app_path = Path(__file__).parent / "level1" / "pdf_reader.py"
    cmds = [sys.executable or "python", str(app_path)]
    subprocess.run(cmds)


def run_weather_app():
    app_path = Path(__file__).parent / "level2" / "weather_app.py"
    cmds = ["streamlit", "run", str(app_path)]
    subprocess.run(cmds)
