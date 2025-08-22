import csv
from pathlib import Path
from itsdangerous import URLSafeTimedSerializer

BASE_URL = "https://mylibribooks.com"
SECRET_KEY = "super-secret-key"
BOOK_IDS = [10, 20, 30, 43, 117]

serializer = URLSafeTimedSerializer(SECRET_KEY)
iframe_codes = []

for book_id in BOOK_IDS:
    token = serializer.dumps({"book_id": book_id})
    iframe = f"""<iframe
  src="{BASE_URL}/home/books/{book_id}?token={token}"
  width="100%" height="600" style="border:none; overflow:hidden;"
  allowfullscreen loading="lazy">
</iframe>"""
    iframe_codes.append((book_id, iframe))

# Save to CSV
csv_path = Path("test_reports/embed_iframes.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["book_id", "embed_code"])
    writer.writerows(iframe_codes)

# Save to HTML
html_path = Path("test_reports/embed_iframes.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write("<html><body>\n")
    for _, iframe in iframe_codes:
        f.write(iframe + "\n\n")
    f.write("</body></html>")

print(f"✅ Embed codes saved to:\n- {csv_path}\n- {html_path}")
