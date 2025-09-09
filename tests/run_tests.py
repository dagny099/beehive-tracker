#!/usr/bin/env python3
"""
Test runner for Beehive Tracker storage abstraction layer.
Runs all tests and provides summary results.
"""

import sys
import os
import pytest
import subprocess

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_unit_tests():
    """Run unit tests that don't require external dependencies"""
    print("🧪 Running Unit Tests...")
    print("=" * 50)
    
    unit_test_files = [
        "test_storage_manager.py",
        "test_configuration.py",
        "test_data_migration.py",
        "test_exif_preservation.py"
    ]
    
    results = {}
    
    for test_file in unit_test_files:
        print(f"\n📋 Running {test_file}...")
        
        try:
            # Run pytest on specific file
            result = pytest.main([
                os.path.join(os.path.dirname(__file__), test_file),
                "-v", 
                "--tb=short",
                "-x"  # Stop on first failure
            ])
            
            results[test_file] = {
                "status": "PASSED" if result == 0 else "FAILED",
                "exit_code": result
            }
            
        except Exception as e:
            results[test_file] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    return results


def run_integration_tests():
    """Run integration tests (require AWS credentials)"""
    print("\n🌐 Running Integration Tests...")
    print("=" * 50)
    
    # Check if AWS credentials are available
    has_aws_creds = bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
    has_test_bucket = bool(os.getenv("TEST_S3_BUCKET_NAME"))
    
    if not has_aws_creds or not has_test_bucket:
        print("⚠️  S3 integration tests skipped - AWS credentials or test bucket not configured")
        print("   Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and TEST_S3_BUCKET_NAME to run S3 tests")
        return {"test_s3_integration.py": {"status": "SKIPPED", "reason": "AWS credentials not available"}}
    
    print("✅ AWS credentials found - running S3 integration tests...")
    
    try:
        result = pytest.main([
            os.path.join(os.path.dirname(__file__), "test_s3_integration.py"),
            "-v",
            "--tb=short",
            "-s"  # Don't capture output for integration tests
        ])
        
        return {
            "test_s3_integration.py": {
                "status": "PASSED" if result == 0 else "FAILED",
                "exit_code": result
            }
        }
        
    except Exception as e:
        return {
            "test_s3_integration.py": {
                "status": "ERROR", 
                "error": str(e)
            }
        }


def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking Dependencies...")
    print("=" * 50)
    
    dependencies = {
        "pytest": "Testing framework",
        "PIL": "Image processing",
        "boto3": "AWS S3 integration (optional)",
        "piexif": "EXIF processing (optional)"
    }
    
    available = {}
    
    for dep, description in dependencies.items():
        try:
            if dep == "PIL":
                import PIL
            elif dep == "piexif":
                import piexif
            elif dep == "boto3":
                import boto3
            else:
                __import__(dep)
            
            available[dep] = {"status": "✅ Available", "description": description}
            
        except ImportError:
            optional = "(optional)" in description
            status = "⚠️  Missing (optional)" if optional else "❌ Missing (required)"
            available[dep] = {"status": status, "description": description}
    
    for dep, info in available.items():
        print(f"{info['status']} {dep:12} - {info['description']}")
    
    return available


def print_summary(unit_results, integration_results, dependencies):
    """Print test execution summary"""
    print("\n📊 Test Execution Summary")
    print("=" * 50)
    
    # Count results
    total_tests = len(unit_results) + len(integration_results)
    passed_tests = sum(1 for r in {**unit_results, **integration_results}.values() if r["status"] == "PASSED")
    failed_tests = sum(1 for r in {**unit_results, **integration_results}.values() if r["status"] == "FAILED")
    skipped_tests = sum(1 for r in {**unit_results, **integration_results}.values() if r["status"] == "SKIPPED")
    error_tests = sum(1 for r in {**unit_results, **integration_results}.values() if r["status"] == "ERROR")
    
    print(f"Total Tests:    {total_tests}")
    print(f"✅ Passed:      {passed_tests}")
    print(f"❌ Failed:      {failed_tests}")
    print(f"⚠️  Skipped:     {skipped_tests}")
    print(f"💥 Errors:      {error_tests}")
    
    # Detailed results
    print("\n📋 Detailed Results:")
    
    all_results = {**unit_results, **integration_results}
    for test_name, result in all_results.items():
        status_emoji = {
            "PASSED": "✅",
            "FAILED": "❌", 
            "SKIPPED": "⚠️",
            "ERROR": "💥"
        }.get(result["status"], "❓")
        
        print(f"{status_emoji} {test_name:30} {result['status']}")
        
        if "reason" in result:
            print(f"   └─ {result['reason']}")
        elif "error" in result:
            print(f"   └─ {result['error']}")
    
    # Dependencies summary
    missing_required = [
        dep for dep, info in dependencies.items()
        if "Missing (required)" in info["status"]
    ]
    
    if missing_required:
        print(f"\n⚠️  Missing required dependencies: {', '.join(missing_required)}")
        print("   Install with: pip install " + " ".join(missing_required))
    
    # Overall result
    print("\n" + "=" * 50)
    if failed_tests == 0 and error_tests == 0:
        print("🎉 ALL TESTS PASSED! Storage abstraction layer is ready.")
        return True
    else:
        print("💔 Some tests failed. Review errors above before proceeding.")
        return False


def main():
    """Main test runner"""
    print("🚀 Beehive Tracker Storage Layer Test Suite")
    print("=" * 60)
    
    # Check dependencies first
    dependencies = check_dependencies()
    
    # Run tests
    unit_results = run_unit_tests()
    integration_results = run_integration_tests()
    
    # Print summary
    success = print_summary(unit_results, integration_results, dependencies)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()