"""Check segment structure in HDF5 file."""
import h5py

with h5py.File('tools/Prepared.hdf5', 'r') as f:
    curve0 = f['curve0']
    
    print("=== curve0 attributes ===")
    print(f"  selectedSegment: {curve0.attrs.get('selectedSegment')}")
    print(f"  segments: {curve0.attrs.get('segments')}")
    
    print("\n=== Available segments ===")
    segments = [k for k in curve0.keys() if k.startswith('segment')]
    print(f"  {segments}")
    
    print("\n=== Segment data shapes ===")
    for seg in segments:
        seg_group = curve0[seg]
        print(f"  {seg}:")
        print(f"    Z: {seg_group['Z'].shape}")
        print(f"    Force: {seg_group['Force'].shape}")
    
    print("\n=== Current loader behavior ===")
    print("The loader finds the FIRST segment alphabetically,")
    print("but the file specifies selectedSegment=1")
    print(f"This means segment1 should be used, not segment0!")
