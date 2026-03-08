#!/usr/bin/env python
"""
Test the complete workflow: load data -> apply savgol -> switch to none -> check visualization
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from softmech.core.data import Curve, Dataset, TipGeometry
from softmech.core.io import loaders
from softmech.core.pipeline import PipelineDescriptor, PipelineStage, PipelineStep, PipelineMetadata
from softmech.core.pipeline import PipelineExecutor
from softmech.core.plugins import PluginRegistry

print("="*70)
print("WORKFLOW TEST: Load Data -> Savgol -> None -> Verify")
print("="*70)

# Load test data
test_file = "tools/synth.json"
if not Path(test_file).exists():
    print(f"✗ Test file {test_file} not found")
    sys.exit(1)

print(f"\n1. Loading test data from {test_file}...")
try:
    data = loaders.load(test_file)
    dataset = Dataset(name="SynthTest")
    
    curve_count = 0
    for i, curve_dict in enumerate(data.get("curves", [])[:3]):  # Load first 3 curves
        Z = np.array(curve_dict.get("data", {}).get("Z", []))
        F = np.array(curve_dict.get("data", {}).get("F", []))
        k = float(curve_dict.get("spring_constant", 0.032))
        
        tip_dict = curve_dict.get("tip", {})
        tip_geom = TipGeometry(
            geometry_type=tip_dict.get("geometry", "sphere"),
            radius=float(tip_dict.get("radius", 1e-6))
        )
        
        curve = Curve(Z, F, spring_constant=k, tip_geometry=tip_geom, index=i)
        dataset.append(curve)
        curve_count += 1
    
    print(f"   ✓ Loaded {curve_count} curves, {len(Z)} points each")
    
    # Store initial data for comparison
    initial_Z = []
    initial_F = []
    for curve in dataset:
        Z, F = curve.get_current_data()
        initial_Z.append(Z.copy())
        initial_F.append(F.copy())
    
except Exception as e:
    print(f"   ✗ Failed to load: {e}")
    sys.exit(1)

# Initialize registry
print("\n2. Discovering plugins...")
registry = PluginRegistry()
plugins_path = Path(__file__).parent / "softmech" / "plugins"
try:
    if (plugins_path / "filters").exists():
        registry.discover(plugins_path / "filters", "softmech.plugins.filters", "filter")
        filters = registry.list("filter")
        print(f"   ✓ Discovered filters: {list(filters.keys()) if isinstance(filters, dict) else filters}")
    
    if (plugins_path / "contact_point").exists():
        registry.discover(plugins_path / "contact_point", "softmech.plugins.contact_point", "contact_point")
        cps = registry.list("contact_point")
        print(f"   ✓ Discovered contact point methods: {list(cps.keys()) if isinstance(cps, dict) else cps}")
except Exception as e:
    print(f"   ⚠ Plugin discovery failed: {e}")

# Create pipeline with savgol
print("\n3. Creating pipeline with Savgol filter...")
metadata = PipelineMetadata(name="Test", description="Test workflow")
stage = PipelineStage(name="preprocessing", description="Testing")
stage.add_step(PipelineStep(type="filter", plugin_id="savgol", parameters={"window_size": 25.0, "polyorder": 3}))
stage.add_step(PipelineStep(type="contact_point", plugin_id="none", parameters={}))
descriptor = PipelineDescriptor(metadata=metadata, stages=[stage])

print("   ✓ Pipeline created with savgol filter")

# Run pipeline with savgol
print("\n4. Running pipeline with Savgol filter...")
try:
    # Reset all curves to raw first
    for curve in dataset:
        curve.reset_to_raw()
    
    executor = PipelineExecutor(registry)
    executor.execute(descriptor, dataset)
    
    # Check data after savgol
    savgol_Z = []
    savgol_F = []
    valid_curves = 0
    for curve in dataset:
        Z, F = curve.get_current_data()
        savgol_Z.append(Z.copy())
        savgol_F.append(F.copy())
        if len(Z) > 0 and len(F) > 0:
            valid_curves += 1
    
    print(f"   ✓ Pipeline completed: {valid_curves}/{len(dataset)} curves have data")
    print(f"      First curve: {len(savgol_Z[0])} points")
except Exception as e:
    print(f"   ✗ Pipeline failed: {e}")
    import traceback
    traceback.print_exc()

# Switch filter to "none"
print("\n5. Switching filter to 'none'...")
descriptor.stages[0].steps[0].plugin_id = "none"
descriptor.stages[0].steps[0].parameters = {}  
print("   ✓ Filter changed to 'none'")

# Run pipeline again
print("\n6. Running pipeline with 'none' filter...")
try:
    # Reset all curves to raw first
    for curve in dataset:
        curve.reset_to_raw()
    
    executor = PipelineExecutor(registry)
    executor.execute(descriptor, dataset)
    
    # Check data after reset
    final_Z = []
    final_F = []
    valid_curves = 0
    for curve in dataset:
        Z, F = curve.get_current_data()
        final_Z.append(Z.copy())
        final_F.append(F.copy())
        if len(Z) > 0 and len(F) > 0:
            valid_curves += 1
    
    print(f"   ✓ Pipeline completed: {valid_curves}/{len(dataset)} curves have data")
    print(f"      First curve: {len(final_Z[0])} points")
    
    # Verify data is back to original
    print("\n7. Verifying data integrity...")
    all_match = True
    for i in range(len(dataset)):
        Z_match = np.allclose(final_Z[i], initial_Z[i])
        F_match = np.allclose(final_F[i], initial_F[i])
        if Z_match and F_match:
            print(f"   ✓ Curve {i}: Data matches original raw data")
        else:
            print(f"   ✗ Curve {i}: Data mismatch!")
            all_match = False
    
    if all_match:
        print("\n✓ ✓ ✓ SUCCESS: All curves correctly reset to raw data ✓ ✓ ✓")
    else:
        print("\n✗ Some curves don't match - check output above")
        
except Exception as e:
    print(f"   ✗ Pipeline failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("Workflow test completed!")
print("="*70)
