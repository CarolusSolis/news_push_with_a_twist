#!/usr/bin/env python3
"""Validation script to check if the testing setup is working correctly."""

import sys
from pathlib import Path

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def check_file_exists(filepath, description):
    """Check if a file exists and print result."""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_import(module_name, description):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name}")
        print(f"   Error: {e}")
        return False

def main():
    """Run validation checks."""
    print("\n🔍 Validating Testing Setup for Agentic Morning Digest")

    all_checks_passed = True

    # Check file structure
    print_section("File Structure")
    files_to_check = [
        ("app/services.py", "Backend services module"),
        ("app/app.py", "Streamlit app"),
        ("tests/__init__.py", "Tests package"),
        ("tests/test_services.py", "Service unit tests"),
        ("tests/test_app.py", "Streamlit AppTests"),
        ("tests/CLAUDE.md", "Testing context"),
        ("app/agent/CLAUDE.md", "Agent context"),
        ("app/voiceover/CLAUDE.md", "Voiceover context"),
        ("pytest.ini", "Pytest configuration"),
        ("requirements.txt", "Dependencies"),
        ("CLAUDE.md", "Main context file"),
    ]

    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_checks_passed = False

    # Check Python dependencies
    print_section("Python Dependencies")
    dependencies = [
        ("pytest", "Testing framework"),
        ("streamlit", "Streamlit framework"),
    ]

    for module, description in dependencies:
        if not check_import(module, description):
            all_checks_passed = False
            if module == "pytest":
                print("   Install with: pip install -r requirements.txt")

    # Check services can be imported
    print_section("Backend Services")
    sys.path.insert(0, str(Path(__file__).parent / 'app'))

    try:
        from services import DigestService, VoiceoverService
        print("✅ DigestService can be imported")
        print("✅ VoiceoverService can be imported")

        # Test basic instantiation
        digest_service = DigestService()
        voiceover_service = VoiceoverService()
        print("✅ Services can be instantiated")
    except Exception as e:
        print(f"❌ Services import failed: {e}")
        all_checks_passed = False

    # Count tests
    print_section("Test Discovery")
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Parse output to count tests
        output = result.stdout + result.stderr
        if "test" in output:
            # Extract test count from pytest output
            lines = output.split('\n')
            for line in lines:
                if 'collected' in line.lower():
                    print(f"✅ {line.strip()}")
        else:
            print("⚠️  Could not determine test count")

    except subprocess.TimeoutExpired:
        print("⚠️  Test collection timed out (dependencies may not be installed)")
    except Exception as e:
        print(f"⚠️  Could not run pytest: {e}")
        print("   This is OK if dependencies aren't installed yet")

    # Summary
    print_section("Summary")

    if all_checks_passed:
        print("✅ All structural checks passed!")
        print("\n📋 Next Steps:")
        print("   1. Activate environment: conda activate news_push")
        print("   2. Install dependencies: pip install -r requirements.txt")
        print("   3. Run tests: pytest -v")
        print("   4. Check coverage: pytest --cov=app --cov-report=html")
    else:
        print("❌ Some checks failed. Please review the output above.")
        return 1

    print("\n📚 Hierarchical Documentation:")
    print("   - Main Context: CLAUDE.md")
    print("   - Testing Context: tests/CLAUDE.md")
    print("   - Agent Context: app/agent/CLAUDE.md")
    print("   - Voiceover Context: app/voiceover/CLAUDE.md")

    print("\n✨ Testing setup complete! Happy testing! 🧪\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
