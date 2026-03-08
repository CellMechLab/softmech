#!/usr/bin/env python
"""
Test elasticity with full pipeline like Designer does
"""
import sys
from pathlib import Path
import numpy as np
import logging

# Setup logging to show only warnings/errors
logging.basicConfig(level=logging.WARNING, format="%(name)s - %(levelname)s: %(message)s")

sys.path.insert(0, str(Path(__file__).parent))

from softmech.core.data import Curve, Dataset, TipGeometry
from softmech.core.io import loaders
from softmech.core.pipeline import PipelineDescriptor, PipelineStage, PipelineStep, PipelineMetadata
from softmech.core.pipeline import PipelineExecutor
from softmech.core.plugins import PluginRegistry

print("="*70)
print("FULL PIPELINE ELASTICITY TEST")
print("="*70)

# Load test data
print("\n1. Loading dataset...")
data = loaders.load("tools/synth.json")
dataset = Dataset(name="Test")

for i, curve_dict in enumerate(data.get("curves", [])[:1]):  # Just first curve
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

print(f"   ✓ Loaded {len(dataset)} curve(s)")

# Initialize registry
registry = PluginRegistry()
plugins_path = Path(__file__).parent / "softmech" / "plugins"
registry.discover(plugins_path / "filters", "softmech.plugins.filters", "filter")
registry.discover(plugins_path / "contact_point", "softmech.plugins.contact_point", "contact_point")

# Create full pipeline like Designer does
print("\n2. Creating full pipeline (Savgol → Autothresh → Elasticity)...")
metadata = PipelineMetadata(name="Full", description="Full test")
stage1 = PipelineStage(name="preprocessing", description="Filters + CP")
stage1.add_step(PipelineStep(type="filter", plugin_id="savgol", parameters={"window_size": 25.0, "polyorder": 3}))
stage1.add_step(PipelineStep(type="contact_point", plugin_id="autothresh", parameters={}))

stage2 = PipelineStage(name="analysis", description="Elasticity")
stage2.add_step(PipelineStep(type="elasticity_spectra", plugin_id="elasticity_spectra", parameters={}))

descriptor = PipelineDescriptor(metadata=metadata, stages=[stage1, stage2])
print("   ✓ Pipeline created")

# Run pipeline
print("\n3. Running full pipeline...")
for curve in dataset:
    curve.reset_to_raw()

executor = PipelineExecutor(registry)
executor.execute(descriptor, dataset)

# Check results
print("\n4. Checking results...")
for i, curve in enumerate(dataset):
    print(f"\n   Curve {i}:")
    
    # Check raw data
    Z, F = curve.get_current_data()
    print(f"     Current data: {len(Z)} points")
    
    # Check CP
    cp = curve.get_contact_point()
    if cp:
        print(f"     ✓ CP detected at Z={cp[0]*1e6:.4f} µm")
    else:
        print(f"     ✗ No CP detected")
    
    # Check indentation
    ind = curve.get_indentation_data()
    if ind[0] is not None:
        print(f"     ✓ Indentation: {len(ind[0])} points, range {ind[0].min()*1e6:.4f}-{ind[0].max()*1e6:.4f} µm")
    else:
        print(f"     ✗ No indentation")
    
    # Check elasticity
    elast = curve.get_elasticity_spectra()
    if elast[0] is not None:
        print(f"     ✓ Elasticity: {len(elast[0])} points, E={np.mean(elast[1]):.2e} Pa")
    else:
        print(f"     ✗ No elasticity spectra")

print("\n" + "="*70)
print("Pipeline test complete!")
print("="*70)
