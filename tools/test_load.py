"""Test loading the Prepared.hdf5 file."""
import sys
sys.path.insert(0, 'c:/Users/mv68b/git/softmech')

from softmech.core.io.loaders import load_hdf5

try:
    data = load_hdf5('tools/Prepared.hdf5')
    print(f"✓ Successfully loaded {len(data['curves'])} curves")
    
    # Check first curve
    if data['curves']:
        curve = data['curves'][0]
        print(f"\nFirst curve data:")
        print(f"  Z length: {len(curve['Z'])}")
        print(f"  F length: {len(curve['F'])}")
        print(f"  spring_constant: {curve.get('spring_constant')}")
        print(f"  tip geometry: {curve.get('tip', {}).get('geometry')}")
        print(f"  tip radius: {curve.get('tip', {}).get('radius')}")
except Exception as e:
    print(f"✗ Failed to load file:")
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()
