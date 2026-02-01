#!/usr/bin/env python3
"""
Security Validation Test Suite for Dental Agent API

This script validates all security fixes are working correctly:
1. JWT secret validation (check it meets requirements)
2. Environment variables are set correctly
3. Encryption is working
4. Input validation is working
5. Audit logging is configured
6. Security headers are present

Usage:
    python tests/security_validation.py
    python tests/security_validation.py --verbose

Exit codes:
    0 = All security checks passed
    1 = One or more security checks failed
"""

import os
import sys
import re
import argparse
import tempfile
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestResult(Enum):
    """Test result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARN = "WARN"


@dataclass
class SecurityCheck:
    """Represents a security check result."""
    name: str
    result: TestResult
    message: str
    details: Optional[str] = None


class SecurityValidator:
    """Validates security configurations and implementations."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.checks: List[SecurityCheck] = []
        self.original_env = dict(os.environ)
        
    def log(self, message: str, level: str = "INFO"):
        """Print verbose output."""
        if self.verbose:
            print(f"  [{level}] {message}")
    
    def add_check(self, name: str, result: TestResult, message: str, details: Optional[str] = None):
        """Add a check result."""
        self.checks.append(SecurityCheck(name, result, message, details))
        status_color = {
            TestResult.PASS: "\033[92m",  # Green
            TestResult.FAIL: "\033[91m",  # Red
            TestResult.SKIP: "\033[93m",  # Yellow
            TestResult.WARN: "\033[93m",  # Yellow
        }.get(result, "")
        reset_color = "\033[0m"
        print(f"  [{status_color}{result.value}{reset_color}] {name}: {message}")
        if details and self.verbose:
            print(f"         {details}")
    
    # ==========================================================================
    # 1. JWT Secret Validation
    # ==========================================================================
    
    def test_jwt_secret_validation(self) -> None:
        """Test JWT secret meets security requirements."""
        print("\n[1/6] JWT Secret Validation")
        
        jwt_secret = os.getenv("JWT_SECRET", "")
        
        if not jwt_secret:
            self.add_check(
                "JWT_SECRET Set",
                TestResult.FAIL,
                "JWT_SECRET environment variable is not set",
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
            return
        
        self.add_check("JWT_SECRET Set", TestResult.PASS, "Environment variable is set")
        
        # Check minimum length (32 characters)
        if len(jwt_secret) < 32:
            self.add_check(
                "JWT Length",
                TestResult.FAIL,
                f"JWT_SECRET must be at least 32 characters (current: {len(jwt_secret)})",
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        else:
            self.add_check("JWT Length", TestResult.PASS, f"Length: {len(jwt_secret)} chars (>= 32)")
        
        # Check for weak secrets
        weak_secrets = [
            "changeme", "changeme-insecure-secret", "password", "secret",
            "admin", "123456", "qwerty", "letmein", "welcome", "default"
        ]
        jwt_lower = jwt_secret.lower()
        is_weak = jwt_lower in weak_secrets or any(ws in jwt_lower for ws in weak_secrets)
        
        if is_weak:
            self.add_check(
                "JWT Weak Secret Check",
                TestResult.FAIL,
                "JWT_SECRET appears to be a commonly used weak secret",
                "Generate a secure one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        else:
            self.add_check("JWT Weak Secret Check", TestResult.PASS, "Secret is not in common weak list")
        
        # Check complexity requirements
        has_upper = bool(re.search(r'[A-Z]', jwt_secret))
        has_lower = bool(re.search(r'[a-z]', jwt_secret))
        has_digit = bool(re.search(r'\d', jwt_secret))
        has_special = bool(re.search(r'[!@#$%^&*()\-_=+{}\[\]:;|\'",.<>/?`~\\]', jwt_secret))
        
        complexity_checks = [
            ("Uppercase", has_upper),
            ("Lowercase", has_lower),
            ("Digit", has_digit),
            ("Special Char", has_special),
        ]
        
        for name, present in complexity_checks:
            if present:
                self.add_check(f"JWT {name}", TestResult.PASS, "Present")
            else:
                self.add_check(
                    f"JWT {name}",
                    TestResult.FAIL,
                    f"Missing {name.lower()} character",
                    "JWT_SECRET must contain at least one of each character type"
                )
    
    # ==========================================================================
    # 2. Environment Variables Validation
    # ==========================================================================
    
    def test_environment_variables(self) -> None:
        """Test required environment variables are set correctly."""
        print("\n[2/6] Environment Variables")
        
        required_vars = [
            ("JWT_SECRET", True),
            ("ENCRYPTION_KEY", True),
            ("DATABASE_URL", True),
            ("REDIS_URL", False),  # Optional for basic operation
            ("DEEPGRAM_API_KEY", False),
            ("OPENAI_API_KEY", False),
            ("SESSION_SECRET", True),
        ]
        
        for var_name, required in required_vars:
            value = os.getenv(var_name, "")
            if value and not value.startswith("changeme") and not value.startswith("your-"):
                self.add_check(f"Env: {var_name}", TestResult.PASS, "Set and not placeholder")
            elif value and (value.startswith("changeme") or value.startswith("your-")):
                if required:
                    self.add_check(
                        f"Env: {var_name}",
                        TestResult.FAIL,
                        "Still using placeholder value",
                        f"Current value: {value[:30]}..."
                    )
                else:
                    self.add_check(
                        f"Env: {var_name}",
                        TestResult.WARN,
                        "Using placeholder value",
                        f"Current value: {value[:30]}..."
                    )
            elif required:
                self.add_check(
                    f"Env: {var_name}",
                    TestResult.FAIL,
                    "Required variable is not set"
                )
            else:
                self.add_check(
                    f"Env: {var_name}",
                    TestResult.SKIP,
                    "Optional variable not set"
                )
        
        # Check environment mode
        env_mode = os.getenv("ENVIRONMENT", "development")
        if env_mode == "production":
            self.add_check("Environment Mode", TestResult.PASS, "Running in production mode")
            
            # In production, check for specific settings
            if os.getenv("ALLOWED_ORIGINS"):
                self.add_check("CORS Origins", TestResult.PASS, "ALLOWED_ORIGINS is set for production")
            else:
                self.add_check("CORS Origins", TestResult.WARN, "ALLOWED_ORIGINS should be explicitly set in production")
        else:
            self.add_check("Environment Mode", TestResult.WARN, f"Running in {env_mode} mode (not production)")
    
    # ==========================================================================
    # 3. Encryption Validation
    # ==========================================================================
    
    def test_encryption(self) -> None:
        """Test encryption is working correctly."""
        print("\n[3/6] Encryption")
        
        try:
            from encryption import (
                encrypt_field, decrypt_field, generate_encryption_key,
                EncryptionNotConfiguredError, ENCRYPTION_KEY
            )
            
            # Test 1: Check encryption key is set
            if not ENCRYPTION_KEY or ENCRYPTION_KEY.startswith("changeme"):
                self.add_check(
                    "Encryption Key Set",
                    TestResult.FAIL,
                    "ENCRYPTION_KEY is not configured",
                    "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )
                return
            
            self.add_check("Encryption Key Set", TestResult.PASS, "Key is configured")
            
            # Test 2: Encrypt and decrypt a test value
            test_value = "Test PII Data: (555) 123-4567"
            try:
                encrypted = encrypt_field(test_value)
                decrypted = decrypt_field(encrypted)
                
                if decrypted == test_value:
                    self.add_check("Encrypt/Decrypt Roundtrip", TestResult.PASS, "Encryption working correctly")
                else:
                    self.add_check(
                        "Encrypt/Decrypt Roundtrip",
                        TestResult.FAIL,
                        "Decrypted value doesn't match original",
                        f"Original: {test_value}, Decrypted: {decrypted}"
                    )
                
                # Verify encrypted value is different from plaintext
                if encrypted != test_value:
                    self.add_check("Encryption Obfuscation", TestResult.PASS, "Encrypted value differs from plaintext")
                else:
                    self.add_check("Encryption Obfuscation", TestResult.FAIL, "Value not encrypted")
                
            except Exception as e:
                self.add_check(
                    "Encrypt/Decrypt Roundtrip",
                    TestResult.FAIL,
                    f"Encryption test failed: {str(e)}"
                )
            
            # Test 3: Generate key works
            try:
                new_key = generate_encryption_key()
                if len(new_key) > 20:  # Fernet keys are 44 chars
                    self.add_check("Key Generation", TestResult.PASS, "Can generate new encryption keys")
                else:
                    self.add_check("Key Generation", TestResult.FAIL, "Generated key appears invalid")
            except Exception as e:
                self.add_check("Key Generation", TestResult.FAIL, f"Key generation failed: {str(e)}")
                
        except ImportError as e:
            self.add_check(
                "Encryption Module",
                TestResult.FAIL,
                f"Could not import encryption module: {str(e)}"
            )
        except Exception as e:
            self.add_check(
                "Encryption Test",
                TestResult.FAIL,
                f"Unexpected error: {str(e)}"
            )
    
    # ==========================================================================
    # 4. Input Validation
    # ==========================================================================
    
    def test_input_validation(self) -> None:
        """Test input validation functions."""
        print("\n[4/6] Input Validation")
        
        try:
            from validators import (
                validate_no_xss, validate_no_sqli, validate_no_path_traversal,
                validate_no_cmd_injection, validate_no_nosqli,
                validate_clinic_name, validate_phone_number,
                validate_safe_string, sanitize_input
            )
            
            # Test 1: XSS Detection
            xss_tests = [
                ("<script>alert('xss')</script>", False, "Script tag"),
                ("<img src=x onerror=alert('xss')>", False, "Image onerror"),
                ("javascript:alert('xss')", False, "JavaScript protocol"),
                ("Safe Clinic Name", True, "Safe text"),
            ]
            
            xss_passed = 0
            for test_input, should_pass, description in xss_tests:
                result = validate_no_xss(test_input)
                if result == should_pass:
                    xss_passed += 1
            
            if xss_passed == len(xss_tests):
                self.add_check("XSS Detection", TestResult.PASS, f"All {len(xss_tests)} test cases passed")
            else:
                self.add_check("XSS Detection", TestResult.FAIL, f"{len(xss_tests) - xss_passed}/{len(xss_tests)} test cases failed")
            
            # Test 2: SQL Injection Detection
            sqli_tests = [
                ("'; DROP TABLE users; --", False, "Drop table"),
                ("' OR 1=1 --", False, "OR condition"),
                ("1 UNION SELECT * FROM passwords", False, "Union select"),
                ("Normal clinic name", True, "Safe text"),
            ]
            
            sqli_passed = 0
            for test_input, should_pass, description in sqli_tests:
                result = validate_no_sqli(test_input)
                if result == should_pass:
                    sqli_passed += 1
            
            if sqli_passed == len(sqli_tests):
                self.add_check("SQL Injection Detection", TestResult.PASS, f"All {len(sqli_tests)} test cases passed")
            else:
                self.add_check("SQL Injection Detection", TestResult.FAIL, f"{len(sqli_tests) - sqli_passed}/{len(sqli_tests)} test cases failed")
            
            # Test 3: Path Traversal Detection
            path_tests = [
                ("../../../etc/passwd", False, "Unix traversal"),
                ("..\\..\\windows\\system32", False, "Windows traversal"),
                ("valid_filename.txt", True, "Safe filename"),
            ]
            
            path_passed = 0
            for test_input, should_pass, description in path_tests:
                result = validate_no_path_traversal(test_input)
                if result == should_pass:
                    path_passed += 1
            
            if path_passed == len(path_tests):
                self.add_check("Path Traversal Detection", TestResult.PASS, f"All {len(path_tests)} test cases passed")
            else:
                self.add_check("Path Traversal Detection", TestResult.FAIL, f"{len(path_tests) - path_passed}/{len(path_tests)} test cases failed")
            
            # Test 4: Command Injection Detection
            cmd_tests = [
                ("; cat /etc/passwd", False, "Semicolon injection"),
                ("| whoami", False, "Pipe injection"),
                ("$(rm -rf /)", False, "Command substitution"),
                ("Safe parameter", True, "Safe text"),
            ]
            
            cmd_passed = 0
            for test_input, should_pass, description in cmd_tests:
                result = validate_no_cmd_injection(test_input)
                if result == should_pass:
                    cmd_passed += 1
            
            if cmd_passed == len(cmd_tests):
                self.add_check("Command Injection Detection", TestResult.PASS, f"All {len(cmd_tests)} test cases passed")
            else:
                self.add_check("Command Injection Detection", TestResult.FAIL, f"{len(cmd_tests) - cmd_passed}/{len(cmd_tests)} test cases failed")
            
            # Test 5: Clinic Name Validation
            clinic_tests = [
                ("A", False, "Too short"),
                ("Valid Clinic Name", True, "Valid name"),
                ("<script>", False, "XSS in name"),
                ("Clinic' OR '1'='1", False, "SQL injection in name"),
            ]
            
            clinic_passed = 0
            for test_input, should_pass, description in clinic_tests:
                result = validate_clinic_name(test_input)
                if result == should_pass:
                    clinic_passed += 1
            
            if clinic_passed == len(clinic_tests):
                self.add_check("Clinic Name Validation", TestResult.PASS, f"All {len(clinic_tests)} test cases passed")
            else:
                self.add_check("Clinic Name Validation", TestResult.FAIL, f"{len(clinic_tests) - clinic_passed}/{len(clinic_tests)} test cases failed")
            
            # Test 6: Phone Number Validation
            phone_tests = [
                ("(555) 123-4567", True, "Standard format"),
                ("555-123-4567", True, "Hyphen format"),
                ("5551234567", True, "Digits only"),
                ("+15551234567", True, "With country code"),
                ("123", False, "Too short"),
                ("<script>", False, "XSS in phone"),
            ]
            
            phone_passed = 0
            for test_input, should_pass, description in phone_tests:
                result = validate_phone_number(test_input)
                if result == should_pass:
                    phone_passed += 1
            
            if phone_passed == len(phone_tests):
                self.add_check("Phone Validation", TestResult.PASS, f"All {len(phone_tests)} test cases passed")
            else:
                self.add_check("Phone Validation", TestResult.FAIL, f"{len(phone_tests) - phone_passed}/{len(phone_tests)} test cases failed")
            
            # Test 7: Sanitization
            dirty_input = "Test\x00null\x01\x02\x03bytes\nnewline"
            sanitized = sanitize_input(dirty_input)
            if "\x00" not in sanitized and len(sanitized) <= 1000:
                self.add_check("Input Sanitization", TestResult.PASS, "Null bytes and control chars removed")
            else:
                self.add_check("Input Sanitization", TestResult.FAIL, "Sanitization not working properly")
                
        except ImportError as e:
            self.add_check(
                "Validators Module",
                TestResult.FAIL,
                f"Could not import validators module: {str(e)}"
            )
        except Exception as e:
            self.add_check(
                "Input Validation Test",
                TestResult.FAIL,
                f"Unexpected error: {str(e)}"
            )
    
    # ==========================================================================
    # 5. Audit Logging
    # ==========================================================================
    
    def test_audit_logging(self) -> None:
        """Test audit logging is configured."""
        print("\n[5/6] Audit Logging")
        
        try:
            from audit_logger import (
                audit_logger, log_admin_action, log_auth_event,
                log_data_access, AuditEventType, AuthEvent, AdminAction
            )
            
            # Test 1: Audit logger exists and is configured
            if audit_logger:
                self.add_check("Audit Logger Exists", TestResult.PASS, "Audit logger is initialized")
            else:
                self.add_check("Audit Logger Exists", TestResult.FAIL, "Audit logger is None")
            
            # Test 2: Check audit log file is configured
            import logging
            file_handlers = [h for h in audit_logger.handlers if isinstance(h, logging.FileHandler)]
            if file_handlers:
                self.add_check("Audit Log File Handler", TestResult.PASS, f"File handler configured ({len(file_handlers)} handler(s))")
            else:
                self.add_check("Audit Log File Handler", TestResult.WARN, "No file handler configured")
            
            # Test 3: Check audit log directory exists
            audit_log_file = os.getenv("AUDIT_LOG_FILE", "logs/audit.log")
            audit_dir = os.path.dirname(audit_log_file) if os.path.dirname(audit_log_file) else "logs"
            
            if os.path.exists(audit_dir):
                self.add_check("Audit Log Directory", TestResult.PASS, f"Directory exists: {audit_dir}")
            else:
                self.add_check("Audit Log Directory", TestResult.FAIL, f"Directory does not exist: {audit_dir}")
            
            # Test 4: Test log functions work
            try:
                # Create a test log entry
                log_admin_action(
                    user="security_test@example.com",
                    action=AdminAction.CLINIC_VIEW,
                    details={"test": True, "password": "should_be_masked"},
                    ip_address="127.0.0.1"
                )
                self.add_check("Admin Action Logging", TestResult.PASS, "Can log admin actions")
            except Exception as e:
                self.add_check("Admin Action Logging", TestResult.FAIL, f"Failed to log: {str(e)}")
            
            try:
                log_auth_event(
                    user="security_test@example.com",
                    event=AuthEvent.LOGIN_SUCCESS,
                    ip_address="127.0.0.1"
                )
                self.add_check("Auth Event Logging", TestResult.PASS, "Can log auth events")
            except Exception as e:
                self.add_check("Auth Event Logging", TestResult.FAIL, f"Failed to log: {str(e)}")
            
            # Test 5: Check log file was written
            if os.path.exists(audit_log_file):
                self.add_check("Audit Log File", TestResult.PASS, f"Log file exists: {audit_log_file}")
                
                # Check file size
                size = os.path.getsize(audit_log_file)
                if size > 0:
                    self.add_check("Audit Log Content", TestResult.PASS, f"Log file has content ({size} bytes)")
                else:
                    self.add_check("Audit Log Content", TestResult.WARN, "Log file is empty")
            else:
                self.add_check("Audit Log File", TestResult.WARN, f"Log file not yet created: {audit_log_file}")
                
        except ImportError as e:
            self.add_check(
                "Audit Logger Module",
                TestResult.FAIL,
                f"Could not import audit_logger module: {str(e)}"
            )
        except Exception as e:
            self.add_check(
                "Audit Logging Test",
                TestResult.FAIL,
                f"Unexpected error: {str(e)}"
            )
    
    # ==========================================================================
    # 6. Security Headers
    # ==========================================================================
    
    def test_security_headers(self) -> None:
        """Test security headers configuration."""
        print("\n[6/6] Security Headers")
        
        try:
            # Import the middleware to check it exists
            from api_main import SecurityHeadersMiddleware
            self.add_check("SecurityHeadersMiddleware", TestResult.PASS, "Middleware class exists")
            
            # Check if we can make a request to test headers
            # This requires the server to be running
            try:
                import requests
                
                # Try localhost
                response = requests.get("http://localhost:8000/health", timeout=5)
                headers = response.headers
                
                required_headers = {
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "X-XSS-Protection": "1; mode=block",
                    "Referrer-Policy": "strict-origin-when-cross-origin",
                }
                
                for header, expected_value in required_headers.items():
                    if header in headers:
                        if expected_value.lower() in headers[header].lower():
                            self.add_check(
                                f"Header: {header}",
                                TestResult.PASS,
                                f"Present with correct value: {headers[header]}"
                            )
                        else:
                            self.add_check(
                                f"Header: {header}",
                                TestResult.WARN,
                                f"Present but unexpected value: {headers[header]} (expected: {expected_value})"
                            )
                    else:
                        self.add_check(
                            f"Header: {header}",
                            TestResult.FAIL,
                            f"Missing security header (expected: {expected_value})"
                        )
                
                # Check for HSTS in production
                if os.getenv("ENVIRONMENT") == "production":
                    if "Strict-Transport-Security" in headers:
                        self.add_check(
                            "Header: HSTS",
                            TestResult.PASS,
                            f"HSTS header present: {headers['Strict-Transport-Security']}"
                        )
                    else:
                        self.add_check(
                            "Header: HSTS",
                            TestResult.FAIL,
                            "HSTS header missing in production"
                        )
                else:
                    self.add_check("Header: HSTS", TestResult.SKIP, "Not checked (not in production mode)")
                
                # Check CSP
                if "Content-Security-Policy" in headers:
                    csp = headers["Content-Security-Policy"]
                    if "frame-ancestors 'none'" in csp:
                        self.add_check("CSP Frame Ancestors", TestResult.PASS, "Clickjacking protection enabled")
                    else:
                        self.add_check("CSP Frame Ancestors", TestResult.WARN, "Frame ancestors policy may be weak")
                else:
                    self.add_check("Header: CSP", TestResult.FAIL, "Content-Security-Policy header missing")
                
                # Check Permissions-Policy
                if "Permissions-Policy" in headers:
                    self.add_check("Permissions-Policy", TestResult.PASS, "Permissions-Policy header present")
                else:
                    self.add_check("Permissions-Policy", TestResult.WARN, "Permissions-Policy header not set")
                    
            except ImportError:
                self.add_check(
                    "HTTP Header Test",
                    TestResult.SKIP,
                    "requests library not installed, cannot test live headers"
                )
            except requests.exceptions.ConnectionError:
                self.add_check(
                    "HTTP Header Test",
                    TestResult.SKIP,
                    "Server not running on localhost:8000, cannot test live headers"
                )
            except Exception as e:
                self.add_check(
                    "HTTP Header Test",
                    TestResult.SKIP,
                    f"Could not test live headers: {str(e)}"
                )
                
        except ImportError as e:
            self.add_check(
                "Security Headers Module",
                TestResult.FAIL,
                f"Could not import SecurityHeadersMiddleware: {str(e)}"
            )
        except Exception as e:
            self.add_check(
                "Security Headers Test",
                TestResult.FAIL,
                f"Unexpected error: {str(e)}"
            )
    
    # ==========================================================================
    # Summary
    # ==========================================================================
    
    def print_summary(self) -> int:
        """Print test summary and return exit code."""
        print("\n" + "=" * 70)
        print("SECURITY VALIDATION SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for c in self.checks if c.result == TestResult.PASS)
        failed = sum(1 for c in self.checks if c.result == TestResult.FAIL)
        warnings = sum(1 for c in self.checks if c.result == TestResult.WARN)
        skipped = sum(1 for c in self.checks if c.result == TestResult.SKIP)
        total = len(self.checks)
        
        print(f"\nTotal checks: {total}")
        print(f"  \033[92mPASSED:   {passed}\033[0m")
        if failed > 0:
            print(f"  \033[91mFAILED:   {failed}\033[0m")
        if warnings > 0:
            print(f"  \033[93mWARNINGS: {warnings}\033[0m")
        if skipped > 0:
            print(f"  SKIPPED:  {skipped}")
        
        print("\n" + "-" * 70)
        
        if failed > 0:
            print("\n\033[91mFAILED CHECKS:\033[0m")
            for check in self.checks:
                if check.result == TestResult.FAIL:
                    print(f"  - {check.name}: {check.message}")
                    if check.details:
                        print(f"    Details: {check.details}")
        
        if warnings > 0 and self.verbose:
            print("\n\033[93mWARNINGS:\033[0m")
            for check in self.checks:
                if check.result == TestResult.WARN:
                    print(f"  - {check.name}: {check.message}")
        
        print("\n" + "=" * 70)
        
        if failed == 0:
            print("\n\033[92m[OK] All security checks passed!\033[0m")
            return 0
        else:
            print(f"\n\033[91m[FAIL] {failed} security check(s) failed. Please review and fix.\033[0m")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Security Validation Test Suite for Dental Agent API"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("DENTAL AGENT SECURITY VALIDATION")
    print("=" * 70)
    print("\nValidating security configurations and implementations...")
    
    # Load environment variables
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        if args.verbose:
            print(f"\nLoaded environment from: {env_path}")
    
    validator = SecurityValidator(verbose=args.verbose)
    
    # Run all tests
    validator.test_jwt_secret_validation()
    validator.test_environment_variables()
    validator.test_encryption()
    validator.test_input_validation()
    validator.test_audit_logging()
    validator.test_security_headers()
    
    # Print summary and exit
    exit_code = validator.print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
