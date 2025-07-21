#!/usr/bin/env python3

"""
Simple test script for QRate package functionality
"""

import subprocess
import os
import sys

def test_qrate_help():
    """Test that qrate command shows help"""
    try:
        result = subprocess.run(['qrate', '--help'], capture_output=True, text=True)
        if result.returncode == 0 and 'QRate' in result.stdout:
            print("✓ qrate --help works correctly")
            return True
        else:
            print("✗ qrate --help failed")
            return False
    except FileNotFoundError:
        print("✗ qrate command not found")
        return False

def test_qrate_version():
    """Test package import"""
    try:
        import qrate
        print(f"✓ Package import successful - version {qrate.__version__}")
        return True
    except ImportError as e:
        print(f"✗ Package import failed: {e}")
        return False

def test_sample_processing():
    """Test processing a sample file if available"""
    sample_file = "standard_bacteria_qc_fail.csv"
    if os.path.exists(sample_file):
        try:
            result = subprocess.run(['qrate', sample_file], capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Sample file processing successful")
                output_file = sample_file.replace('.csv', '.curated.csv')
                if os.path.exists(output_file):
                    print(f"✓ Output file created: {output_file}")
                return True
            else:
                print(f"✗ Sample file processing failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"✗ Sample file processing failed: {e}")
            return False
    else:
        print("ℹ Sample file not found, skipping processing test")
        return True

def main():
    """Run all tests"""
    print("Testing QRate Package Installation...\n")
    
    tests = [
        test_qrate_version,
        test_qrate_help,
        test_sample_processing
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! QRate is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
