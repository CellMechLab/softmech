#!/usr/bin/env python
"""
Debug script for elasticity spectra calculation issues
"""
import sys
from pathlib import Path
import numpy as np
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

sys.path.insert(0, str(Path(__file__).parent))

from softmech.core.data import Curve, Dataset, TipGeometry
from softmech.core.io import loaders
from softmech.core.pipeline import PipelineDescriptor, PipelineStage, PipelineStep, PipelineMetadata
from softmech.core.pipeline import PipelineExecutor
from softmech.core.plugins import PluginRegistry
from softmech.core.algorithms import spectral

print("="*70)
print("ELASTICITY SPECTRA DEBUG")
print("="*70)

# Load test data
test_file = "tools/synth.json"
print(f"\n1. Loading test data from {test_file}...")
try:
    data = loaders.load(test_file)
    dataset = Dataset(name="Debug")
    
    # Load first curve
    curve_dict = data.get("curves", [])[0]
    Z = np.array(curve_dict.get("data", {}).get("Z", []))
    F = np.array(curve_dict.get("data", {}).get("F", []))
    k = float(curve_dict.get("spring_constant", 0.032))
    
    tip_dict = curve_dict.get("tip", {})
    tip_geom = TipGeometry(
        geometry_type=tip_dict.get("geometry", "sphere"),
        radius=float(tip_dict.get("radius", 1e-6))
    )
    
    curve = Curve(Z, F, spring_constant=k, tip_geometry=tip_geom, index=0)
    dataset.append(curve)
    
    print(f"   ✓ Loaded curve with {len(Z)} points")
    print(f"     Z range: {Z.min()*1e6:.2f} - {Z.max()*1e6:.2f} µm")
    print(f"     F range: {F.min()*1e9:.2f} - {F.max()*1e9:.2f} nN")
    print(f"     Tip geometry: {tip_geom.geometry_type} (radius: {tip_geom.radius*1e6:.2f} µm)")
    
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Initialize registry
print("\n2. Discovering plugins...")
registry = PluginRegistry()
plugins_path = Path(__file__).parent / "softmech" / "plugins"
try:
    if (plugins_path / "filters").exists():
        registry.discover(plugins_path / "filters", "softmech.plugins.filters", "filter")
    if (plugins_path / "contact_point").exists():
        registry.discover(plugins_path / "contact_point", "softmech.plugins.contact_point", "contact_point")
    print(f"   ✓ Plugins discovered")
except Exception as e:
    print(f"   ⚠ Plugin discovery warning: {e}")

# Step 1: Check raw data
print("\n3. CHECK: Raw curve data")
Z, F = curve.get_current_data()
print(f"   ✓ Raw data: {len(Z)} points")

# Step 2: Apply filter
print("\n4. STEP 1: Apply filter (savgol)...")
curve.reset_to_raw()
plugin = registry.get("savgol")
plugin.set_parameters_dict({"window_size": 25.0, "polyorder": 3})
x, y = curve.get_current_data()
result = plugin.calculate(x, y, curve=curve)
if result:
    Z_f, F_f = result
    curve.set_filtered_data(Z_f, F_f)
    Z, F = curve.get_current_data()
    print(f"   ✓ Filtered: {len(Z)} points")
else:
    print(f"   ✗ Filter failed")

# Step 3: Apply contact point detection
print("\n5. STEP 2: Contact point detection (autothresh)...")
plugin_cp = registry.get("autothresh")
x, y = curve.get_current_data()
result_cp = plugin_cp.calculate(x, y, curve=curve)
if result_cp and result_cp is not False:
    z_cp, f_cp = result_cp
    curve.set_contact_point(z_cp, f_cp)
    print(f"   ✓ Contact point detected at:")
    print(f"     Z_cp = {z_cp*1e6:.4f} µm")
    print(f"     F_cp = {f_cp*1e9:.4f} nN")
else:
    print(f"   ✗ Contact point detection failed or returned None")
    print(f"   Result was: {result_cp}")

# Step 4: Calculate indentation
print("\n6. STEP 3: Calculate indentation...")
try:
    spectral.calculate_indentation(curve, zero_force=True)
    delta, f_ind = curve.get_indentation_data()
    if delta is not None:
        print(f"   ✓ Indentation calculated: {len(delta)} points")
        print(f"     δ range: {delta.min()*1e6:.4f} - {delta.max()*1e6:.4f} µm")
        print(f"     F_ind range: {f_ind.min()*1e9:.4f} - {f_ind.max()*1e9:.4f} nN")
    else:
        print(f"   ✗ Indentation data is None")
except Exception as e:
    print(f"   ✗ Indentation calculation failed: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Calculate elasticity spectra
print("\n7. STEP 4: Calculate elasticity spectra...")
try:
    spectral.calculate_elasticity_spectra(curve, window_size=5, order=3, interpolate=True)
    depth, modulus = curve.get_elasticity_spectra()
    if depth is not None:
        print(f"   ✓ Elasticity spectra calculated: {len(depth)} points")
        print(f"     δ_e range: {depth.min()*1e6:.4f} - {depth.max()*1e6:.4f} µm")
        print(f"     E range: {modulus.min():.2e} - {modulus.max():.2e} Pa")
        print(f"     E median: {np.median(modulus):.2e} Pa")
    else:
        print(f"   ✗ Elasticity spectra is None")
except Exception as e:
    print(f"   ✗ Elasticity calculation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("Debug report complete. Check output above for issues.")
print("="*70)
