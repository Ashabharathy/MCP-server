"""
security_audit.py — Security audit script for Phase 6.

Scans source files for credential patterns and performs security checks.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Credential patterns to scan for
CREDENTIAL_PATTERNS = [
    (r'sk_[a-zA-Z0-9]{20,}', 'OpenAI API key'),
    (r'gsk_[a-zA-Z0-9]{20,}', 'Groq API key'),
    (r'ya29\.[a-zA-Z0-9_-]{100,}', 'Google OAuth token'),
    (r'1/[a-zA-Z0-9_-]{20,}', 'Google refresh token'),
    (r'AIza[a-zA-Z0-9_-]{35}', 'Google API key'),
    (r'AKIA[0-9A-Z]{16}', 'AWS access key'),
    (r'[a-zA-Z0-9_-]{32}:[a-zA-Z0-9_-]{32}', 'Client ID:Secret pair'),
    (r'Bearer [a-zA-Z0-9_-]{20,}', 'Bearer token'),
]


def scan_file_for_credentials(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scan a file for credential patterns.

    Args:
        file_path: Path to the file to scan.

    Returns:
        List of tuples (line_number, pattern_name, matched_text).
    """
    findings = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            for pattern, name in CREDENTIAL_PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    findings.append((line_num, name, match.group()))

    except Exception as e:
        print(f"Error scanning {file_path}: {e}")

    return findings


def scan_directory(root_dir: Path, exclude_dirs: List[str] = None) -> dict:
    """
    Scan all Python files in a directory for credentials.

    Args:
        root_dir: Root directory to scan.
        exclude_dirs: Directories to exclude from scanning.

    Returns:
        Dictionary with file paths as keys and lists of findings as values.
    """
    if exclude_dirs is None:
        exclude_dirs = ['.git', '__pycache__', '.pytest_cache', 'venv', 'env', 'logs', 'output']

    findings = {}

    for file_path in root_dir.rglob('*.py'):
        # Skip excluded directories
        if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
            continue

        # Skip the security audit script itself
        if file_path.name == 'security_audit.py':
            continue

        file_findings = scan_file_for_credentials(file_path)
        if file_findings:
            findings[str(file_path)] = file_findings

    return findings


def check_gitignore(root_dir: Path) -> List[str]:
    """
    Check if sensitive files are properly excluded from git.

    Args:
        root_dir: Root directory of the project.

    Returns:
        List of warnings about potentially exposed files.
    """
    warnings = []

    gitignore_path = root_dir / '.gitignore'
    if not gitignore_path.exists():
        warnings.append('.gitignore file not found')
        return warnings

    with open(gitignore_path, 'r', encoding='utf-8') as f:
        gitignore_content = f.read()

    # Check for common sensitive file patterns
    sensitive_patterns = [
        '*.json',
        'credentials.json',
        'token.json',
        '.env',
        'config/mcp-config.json',
    ]

    for pattern in sensitive_patterns:
        if pattern not in gitignore_content:
            warnings.append(f'Pattern "{pattern}" not found in .gitignore')

    return warnings


def main():
    """Run security audit."""
    root_dir = Path(__file__).parent.parent

    print("=" * 60)
    print("SECURITY AUDIT")
    print("=" * 60)
    print(f"Scanning directory: {root_dir}")
    print()

    # Scan for credentials
    print("Scanning for credential patterns...")
    findings = scan_directory(root_dir)

    if findings:
        print(f"\n⚠️  Found {sum(len(f) for f in findings.values())} potential credential(s):")
        for file_path, file_findings in findings.items():
            print(f"\n  {file_path}:")
            for line_num, pattern_name, matched_text in file_findings:
                # Truncate long matches for display
                display_text = matched_text[:50] + "..." if len(matched_text) > 50 else matched_text
                print(f"    Line {line_num}: {pattern_name} -> {display_text}")
    else:
        print("✓ No credentials found in source files")

    # Check .gitignore
    print("\n" + "=" * 60)
    print("Checking .gitignore...")
    gitignore_warnings = check_gitignore(root_dir)

    if gitignore_warnings:
        print("\n⚠️  .gitignore warnings:")
        for warning in gitignore_warnings:
            print(f"  - {warning}")
    else:
        print("✓ .gitignore properly configured")

    # Check for credential files in repository
    print("\n" + "=" * 60)
    print("Checking for credential files in repository...")
    credential_files = list(root_dir.rglob('credentials.json')) + list(root_dir.rglob('token.json')) + list(root_dir.rglob('.env'))

    if credential_files:
        print("\n⚠️  Found credential files:")
        for file_path in credential_files:
            print(f"  - {file_path}")
    else:
        print("✓ No credential files found in repository")

    # Summary
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)

    total_issues = len(findings) + len(gitignore_warnings) + len(credential_files)

    if total_issues == 0:
        print("✓ Security audit passed - no issues found")
        sys.exit(0)
    else:
        print(f"⚠️  Security audit found {total_issues} issue(s)")
        print("Please review and fix the issues above before deploying to production")
        sys.exit(1)


if __name__ == "__main__":
    main()
