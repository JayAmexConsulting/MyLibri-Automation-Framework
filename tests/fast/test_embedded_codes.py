import pytest

book_ids = [
    10, 20, 30, 43, 117, 156, 166, 194, 279, 328,
    561, 581, 600, 631, 996, 1079, 1260, 1335, 1346, 1375,
    1384, 1442
]

@pytest.mark.fast
def test_generate_embed_codes():
    for book_id in book_ids:
        embed_code = f"""
<iframe
  src="https://mylibribooks.com/home/books/{book_id}"
  width="100%"
  height="600"
  style="border:none; overflow:hidden;"
  allowfullscreen
  loading="lazy">
</iframe>
"""
        print(embed_code)
