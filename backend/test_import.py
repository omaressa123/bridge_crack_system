#!/usr/bin/env python3
import sys
import os

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports exactly as main.py does...")
print("-" * 60)

# First, test exactly what admin.py tries to do
try:
    from schemas.admin import AdminUserOut
    print("✓ Successfully imported from schemas.admin")
except Exception as e:
    print(f"✗ FAILED importing from schemas.admin: {type(e).__name__}: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

print()

# Now test the other imports from other routers
try:
    from schemas import CrackBase, GoogleLoginRequest
    print("✓ Successfully imported from schemas")
except Exception as e:
    print(f"✗ FAILED importing from schemas: {type(e).__name__}: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

print()
print("✓ All imports test passed!")
