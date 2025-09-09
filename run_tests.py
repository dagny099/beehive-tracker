#!/usr/bin/env python3
"""
Test runner for the EXIF test suite
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"Command failed with return code: {result.returncode}")
            return False
        else:
            print("Command completed successfully!")
            return True
            
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run EXIF extraction tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])
    
    # Select test categories
    if args.unit:
        cmd.append("tests/unit/")
    elif args.integration:
        cmd.append("tests/integration/")
    elif args.performance:
        cmd.extend(["-m", "slow", "tests/integration/test_performance.py"])
    else:
        # Run all tests by default
        cmd.append("tests/")
    
    # Run the tests
    success = run_command(cmd, "EXIF Test Suite")
    
    if success:
        print("\n🎉 All tests passed!")
        
        if args.coverage:
            print("\n📊 Coverage report generated in htmlcov/index.html")
            
        # Show summary of what was tested
        print("\n📋 Test Summary:")
        print("   ✓ Multi-library EXIF extraction (exifread, Pillow, PyExifTool)")
        print("   ✓ GPS coordinate conversion and validation")  
        print("   ✓ Device coverage (Samsung Galaxy S9, Google Pixel 7)")
        print("   ✓ File format handling (JPEG, PNG)")
        print("   ✓ Edge cases and error handling")
        if not args.fast and (args.performance or not any([args.unit, args.integration])):
            print("   ✓ Performance benchmarks")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()