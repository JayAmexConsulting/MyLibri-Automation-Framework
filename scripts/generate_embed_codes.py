import csv
from pathlib import Path
from datetime import datetime

# List of book IDs to generate embed codes for
book_ids = [
    10, 20, 30, 43, 117, 156, 166, 194, 279, 328,
    561, 581, 600, 631, 996
]

# Timestamped output folder
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = Path("embed_reports")
output_dir.mkdir(exist_ok=True)

csv_path = output_dir / f"book_embed_codes_{timestamp}.csv"
html_path = output_dir / f"book_embed_preview_{timestamp}.html"

# Prepare data
embed_data = []
for book_id in book_ids:
    embed_code = f"""<iframe
  src="https://mylibribooks.com/home/books/{book_id}"
  width="100%"
  height="600"
  style="border:none; overflow:hidden;"
  allowfullscreen
  loading="lazy">
</iframe>"""
    embed_data.append({
        "book_id": book_id,
        "embed_code": embed_code
    })

# ✅ Save CSV
with open(csv_path, "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["book_id", "embed_code"])
    writer.writeheader()
    writer.writerows(embed_data)

# ✅ Save HTML
with open(html_path, "w", encoding="utf-8") as f:
    f.write("<html><head><title>MyLibriBooks Embed Preview</title></head><body>\n")
    f.write("<h1>📚 MyLibriBooks Embed Viewer</h1>\n")
    for entry in embed_data:
        f.write(f"<h3>Book ID: {entry['book_id']}</h3>\n")
        f.write(entry["embed_code"] + "\n<br><hr><br>\n")
    f.write("</body></html>")

# ✅ Summary
print(f"✅ Done! Generated {len(embed_data)} embed codes.")
print(f"📄 CSV:  {csv_path}")
print(f"🌐 HTML: {html_path}")
