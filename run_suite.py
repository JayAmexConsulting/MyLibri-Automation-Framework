import subprocess
import webbrowser
from pathlib import Path

# Define report path
report_path = Path("test_reports/full_report.html")
report_path.parent.mkdir(exist_ok=True)

print("📦 Running full test suite with HTML report...")
result = subprocess.run([
    "pytest",
    "tests/",
    f"--html={report_path}",
    "--self-contained-html"
])

# Open the report in default browser if tests ran
if report_path.exists():
    print(f"✅ Opening report: {report_path}")
    webbrowser.open(report_path.resolve().as_uri())
else:
    print("❌ Report was not generated.")
