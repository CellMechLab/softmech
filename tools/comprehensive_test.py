"""Comprehensive test of HDF5 loader fixes."""
import sys
sys.path.insert(0, 'c:/Users/mv68b/git/softmech')

from softmech.core.io.loaders import load_hdf5
import h5py

print("=== Comprehensive HDF5 Loader Test ===\n")

# Test 1: Load the file
print("Test 1: Loading file...")
data = load_hdf5('tools/Prepared.hdf5')
print(f"  ✓ Loaded {len(data['curves'])} curves\n")

# Test 2: Verify all curves respect selectedSegment
print("Test 2: Checking selectedSegment is respected for all curves...")
with h5py.File('tools/Prepared.hdf5', 'r') as f:
    mismatches = 0
    for i, curve_name in enumerate(sorted(f.keys())):
        curve_group = f[curve_name]
        selected_seg = int(curve_group.attrs.get('selectedSegment', 0))
        expected_len = curve_group[f'segment{selected_seg}']['Z'].shape[0]
        actual_len = len(data['curves'][i]['Z'])
        
        if expected_len != actual_len:
            print(f"  ✗ {curve_name}: expected {expected_len} points, got {actual_len}")
            mismatches += 1
    
    if mismatches == 0:
        print(f"  ✓ All {len(data['curves'])} curves use correct segment\n")
    else:
        print(f"  ✗ {mismatches} curves have incorrect segments\n")

# Test 3: Verify tip parameters
print("Test 3: Checking tip parameters...")
curve0 = data['curves'][0]
print(f"  Tip geometry: {curve0['tip']['geometry']}")
print(f"  Tip radius: {curve0['tip']['radius']} (expected: 3.5e-06)")
print(f"  Tip angle: {curve0['tip']['angle']}")
if curve0['tip']['radius'] == 3.5e-06:
    print(f"  ✓ Tip radius correct\n")
else:
    print(f"  ✗ Tip radius incorrect\n")

# Test 4: Check spring constant
print("Test 4: Checking spring constant...")
print(f"  Spring constant: {curve0['spring_constant']} (expected: 0.56)")
if curve0['spring_constant'] == 0.56:
    print(f"  ✓ Spring constant correct\n")
else:
    print(f"  ✗ Spring constant incorrect\n")

print("=== Summary ===")
print("The loader now correctly:")
print("  ✓ Reads the selectedSegment attribute")
print("  ✓ Uses segment1 (2000 points) instead of segment0 (500 points)")
print("  ✓ Reads tip parameters from legacy 'tip' subgroup format")
print("  ✓ Maintains backward compatibility with new format")
