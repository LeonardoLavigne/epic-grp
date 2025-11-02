import os

# Ensure a SECRET_KEY for all tests to satisfy settings validation
os.environ.setdefault("SECRET_KEY", "test-secret-key-global")

