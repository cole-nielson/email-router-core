#!/usr/bin/env python3
"""
Code Quality Metrics Dashboard
🔍 Generates comprehensive code quality report for the Email Router project.
"""

import subprocess
from pathlib import Path
from typing import Dict, Tuple


def run_command(command: str) -> Tuple[str, int]:
    """Run shell command and return output with exit 
    code."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60
        )
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "Command timed out", 1
    except Exception as e:
        return f"Command failed: {e}", 1


def count_lines_of_code() -> Dict[str, int]:
    """Count lines of code by file type."""
    metrics = {"python": 0, "yaml": 0, "markdown": 0, "total_files": 0}
    
    python_files = list(Path("app").rglob("*.py")) + list(Path("tests").rglob("*.py"))
    yaml_files = list(Path("clients").rglob("*.yaml")) + list(Path(".").glob("*.yaml"))
    md_files = list(Path(".").rglob("*.md"))
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = len([line for line in f if line.strip() and not line.strip().startswith('#')])
                metrics["python"] += lines
        except Exception:
            pass
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                lines = len([line for line in f if line.strip() and not line.strip().startswith('#')])
                metrics["yaml"] += lines
        except Exception:
            pass
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                lines = len([line for line in f if line.strip()])
                metrics["markdown"] += lines
        except Exception:
            pass
    
    metrics["total_files"] = len(python_files) + len(yaml_files) + len(md_files)
    return metrics


def run_mypy_analysis() -> Dict[str, int]:
    """Run mypy analysis and parse results."""
    output, _ = run_command("python3 -m mypy app/ --ignore-missing-imports --show-error-codes")
    
    if "Success: no issues found" in output:
        return {"errors": 0, "warnings": 0, "files_checked": 0}
    
    errors = output.count("error:")
    warnings = output.count("warning:")
    files_mentioned = len(set(line.split(":")[0] for line in output.split("\n") if ":" in line and ".py" in line))
    
    return {"errors": errors, "warnings": warnings, "files_checked": files_mentioned}


def run_tests() -> Dict[str, int]:
    """Run pytest and parse results."""
    output, exit_code = run_command("python3 -m pytest tests/ -v --tb=short")
    
    if exit_code == 0:
        # Parse successful test output
        lines = output.split("\n")
        passed = sum(1 for line in lines if " PASSED " in line)
        failed = sum(1 for line in lines if " FAILED " in line)
        skipped = sum(1 for line in lines if " SKIPPED " in line)
    else:
        # Parse failed test output
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        skipped = output.count(" SKIPPED")
    
    return {"passed": passed, "failed": failed, "skipped": skipped, "total": passed + failed + skipped}


def check_code_formatting() -> Dict[str, bool]:
    """Check if code is properly formatted."""
    black_output, black_exit = run_command("python3 -m black --check app/ tests/")
    isort_output, isort_exit = run_command("python3 -m isort --check-only app/ tests/")
    
    return {
        "black_formatted": black_exit == 0,
        "isort_formatted": isort_exit == 0,
        "fully_formatted": black_exit == 0 and isort_exit == 0
    }


def generate_quality_score(metrics: Dict) -> float:
    """Calculate overall quality score (0-100)."""
    score = 100.0
    
    # Type checking score (30% weight)
    mypy_score = max(0, 100 - metrics["mypy"]["errors"] * 2)
    score = score * 0.7 + mypy_score * 0.3
    
    # Test coverage score (40% weight)
    if metrics["tests"]["total"] > 0:
        test_score = (metrics["tests"]["passed"] / metrics["tests"]["total"]) * 100
    else:
        test_score = 0
    score = score * 0.6 + test_score * 0.4
    
    # Code formatting score (30% weight)
    format_score = 100 if metrics["formatting"]["fully_formatted"] else 50
    score = score * 0.7 + format_score * 0.3
    
    return round(score, 1)


def print_report(metrics: Dict) -> None:
    """Print comprehensive quality report."""
    print("=" * 80)
    print("📊 EMAIL ROUTER - CODE QUALITY DASHBOARD")
    print("=" * 80)
    print()
    
    # Overview
    print("🏗️  PROJECT OVERVIEW")
    print("-" * 40)
    print(f"📁 Total Files: {metrics['loc']['total_files']}")
    print(f"🐍 Python Code: {metrics['loc']['python']:,} lines")
    print(f"📄 YAML Config: {metrics['loc']['yaml']:,} lines")
    print(f"📖 Documentation: {metrics['loc']['markdown']:,} lines")
    print()
    
    # Code Quality Score
    quality_score = metrics["quality_score"]
    score_emoji = "🏆" if quality_score >= 90 else "✅" if quality_score >= 80 else "⚠️" if quality_score >= 70 else "❌"
    print(f"🎯 OVERALL QUALITY SCORE: {score_emoji} {quality_score}/100")
    print()
    
    # Type Checking
    print("🔍 TYPE CHECKING (MyPy)")
    print("-" * 40)
    mypy = metrics["mypy"]
    if mypy["errors"] == 0:
        print("✅ No type errors found!")
    else:
        print(f"❌ Type Errors: {mypy['errors']}")
        print(f"⚠️  Warnings: {mypy['warnings']}")
    print(f"📁 Files Checked: {mypy['files_checked']}")
    print()
    
    # Test Results
    print("🧪 TEST RESULTS")
    print("-" * 40)
    tests = metrics["tests"]
    if tests["failed"] == 0 and tests["total"] > 0:
        print(f"✅ All {tests['passed']} tests passing!")
    elif tests["total"] == 0:
        print("⚠️  No tests found")
    else:
        print(f"✅ Passed: {tests['passed']}")
        print(f"❌ Failed: {tests['failed']}")
        print(f"⏭️  Skipped: {tests['skipped']}")
    
    if tests["total"] > 0:
        success_rate = (tests["passed"] / tests["total"]) * 100
        print(f"📊 Success Rate: {success_rate:.1f}%")
    print()
    
    # Code Formatting
    print("🎨 CODE FORMATTING")
    print("-" * 40)
    formatting = metrics["formatting"]
    if formatting["fully_formatted"]:
        print("✅ All code properly formatted!")
    else:
        if not formatting["black_formatted"]:
            print("❌ Black formatting issues found")
        if not formatting["isort_formatted"]:
            print("❌ Import sorting issues found")
        print("💡 Run 'python3 -m black app/ tests/' and 'python3 -m isort app/ tests/' to fix")
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 40)
    recommendations = []
    
    if mypy["errors"] > 0:
        recommendations.append("🔧 Fix type checking errors to improve code reliability")
    
    if tests["total"] == 0:
        recommendations.append("🧪 Add comprehensive test suite")
    elif tests["failed"] > 0:
        recommendations.append("🧪 Fix failing tests")
    
    if not formatting["fully_formatted"]:
        recommendations.append("🎨 Set up pre-commit hooks for automatic formatting")
    
    if quality_score < 80:
        recommendations.append("📈 Focus on improving overall code quality")
    
    if not recommendations:
        recommendations.append("🎉 Excellent code quality! Keep up the good work!")
    
    for rec in recommendations:
        print(f"• {rec}")
    
    print()
    print("=" * 80)
    print("Report generated by Code Quality Dashboard")
    print("=" * 80)


def main() -> None:
    """Generate and display code quality report."""
    print("Generating code quality report...")
    print()
    
    # Collect metrics
    metrics = {
        "loc": count_lines_of_code(),
        "mypy": run_mypy_analysis(),
        "tests": run_tests(),
        "formatting": check_code_formatting(),
    }
    
    # Calculate quality score
    metrics["quality_score"] = generate_quality_score(metrics)
    
    # Display report
    print_report(metrics)


if __name__ == "__main__":
    main()
