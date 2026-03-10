"""Inspect HDF5 file structure."""
import h5py
import sys

filename = sys.argv[1] if len(sys.argv) > 1 else 'tools/Prepared.hdf5'

with h5py.File(filename, 'r') as f:
    print(f"=== Inspecting {filename} ===\n")
    print(f"Top-level keys (total: {len(list(f.keys()))})")
    print(f"  {list(f.keys())[:5]}...\n")
    
    # Check first curve
    first_curve = list(f.keys())[0]
    print(f"=== Structure of {first_curve} ===")
    curve = f[first_curve]
    print(f"Keys: {list(curve.keys())}")
    print(f"Attributes: {dict(curve.attrs)}\n")
    
    # Check first segment
    if 'segment0' in curve:
        seg = curve['segment0']
        print(f"=== Structure of {first_curve}/segment0 ===")
        print(f"Keys: {list(seg.keys())}")
        print(f"Attributes: {dict(seg.attrs)}")
        
        # Check for datasets
        print("\nDatasets:")
        for key in seg.keys():
            item = seg[key]
            if hasattr(item, 'shape'):
                print(f"  {key}: shape={item.shape}, dtype={item.dtype}")
            else:
                print(f"  {key}: (group)")
    
    # Check tip
    if 'tip' in curve:
        tip = curve['tip']
        print(f"\n=== Structure of {first_curve}/tip ===")
        if hasattr(tip, 'attrs'):
            print(f"Attributes: {dict(tip.attrs)}")
        if hasattr(tip, 'keys'):
            print(f"Keys: {list(tip.keys())}")
    
    print("\n=== Expected format (from loaders.py) ===")
    print("curve0/")
    print("  ├── attributes: spring_constant, tip_geometry, tip_radius, etc.")
    print("  ├── segment0/")
    print("  │   ├── Force (dataset)")
    print("  │   └── Z (dataset)")
    print("  └── cp (optional dataset)")
