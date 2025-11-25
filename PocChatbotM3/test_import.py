import sys
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")
try:
    import truststore
    print("Truststore imported successfully!")
    print(f"Truststore file: {truststore.__file__}")
except ImportError as e:
    print(f"Failed to import truststore: {e}")
