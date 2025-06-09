#!/bin/bash

echo "📦 Running full test suite..."
pytest tests/ --html=test_reports/full_report.html --self-contained-html

echo "✅ Report generated: test_reports/full_report.html"
