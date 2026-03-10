"""Test the fixed loader."""
import sys
sys.path.insert(0, 'c:/Users/mv68b/git/softmech')

from softmech.core.io.loaders import load_hdf5

print("=== Testing fixed HDF5 loader ===\n")

data = load_hdf5('tools/Prepared.hdf5')
print(f"✓ Successfully loaded {len(data['curves'])} curves\n")

# Check first curve
curve = data['curves'][0]
print("=== First curve data ===")
print(f"  Z length: {len(curve['Z'])} (should be 2000, not 500)")
print(f"  F length: {len(curve['F'])} (should be 2000, not 500)")
print(f"  spring_constant: {curve.get('spring_constant')}")
print(f"  tip geometry: {curve.get('tip', {}).get('geometry')}")
print(f"  tip radius: {curve.get('tip', {}).get('radius')} (should be 3.5e-06)")
print(f"  tip angle: {curve.get('tip', {}).get('angle')}")

print("\n=== Verification ===")
if len(curve['Z']) == 2000:
    print("✓ Correct segment selected (segment1 with 2000 points)")
else:
    print(f"✗ Wrong segment selected (got {len(curve['Z'])} points, expected 2000)")

if curve.get('tip', {}).get('radius') == 3.5e-06:
    print("✓ Correct tip radius (3.5e-06)")
else:
    print(f"✗ Wrong tip radius (got {curve.get('tip', {}).get('radius')}, expected 3.5e-06)")
