# pytest.ini
[pytest]
minversion = 6.0
addopts = -ra -q
testpaths =
    tests
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    fast: marks tests as fast (included by default)
