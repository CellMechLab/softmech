"""Quick test to verify filter functionality"""
import sys
from pathlib import Path
import numpy as np

# Add softmech to path
sys.path.insert(0, str(Path(__file__).parent))

from softmech.core.data import Curve, Dataset
from softmech.core.pipeline import PipelineDescriptor, PipelineStage, PipelineStep, PipelineMetadata
from softmech.core.pipeline import PipelineExecutor
from softmech.core.plugins import PluginRegistry

# Create sample data
np.random.seed(42)
Z = np.linspace(0, 10e-6, 100)
F = 1e-9 * np.sin(Z / 1e-6) + 1e-9 * np.random.normal(0, 0.1, 100)  # Noisy sine wave

print("="*60)
print("Filter Test: Savgol -> None -> Savgol")
print("="*60)

# Create a simple curve
curve = Curve(Z, F, spring_constant=0.032, index=0)
dataset = Dataset(name="Test")
dataset.append(curve)

print(f"\n1. Initial data: {len(Z)} points")
Z0, F0 = curve.get_current_data()
print(f"   Z range: {Z0.min()*1e6:.2f} - {Z0.max()*1e6:.2f} µm")
print(f"   F range: {F0.min()*1e9:.2f} - {F0.max()*1e9:.2f} nN")

# Create pipeline with savgol
registry = PluginRegistry()
metadata = PipelineMetadata(name="Test", description="Test pipeline")
stage = PipelineStage(name="preprocessing", description="Test")
stage.add_step(PipelineStep(type="filter", plugin_id="savgol", parameters={"window_size": 25.0, "polyorder": 3}))
stage.add_step(PipelineStep(type="contact_point", plugin_id="none", parameters={}))
descriptor = PipelineDescriptor(metadata=metadata, stages=[stage])

print("\n2. Applying Savgol filter...")
try:
    executor = PipelineExecutor(registry)
    executor.execute(descriptor, dataset)
    Z1, F1 = curve.get_current_data()
    print(f"   ✓ Filter succeeded: {len(Z1)} points")
    print(f"   Z range: {Z1.min()*1e6:.2f} - {Z1.max()*1e6:.2f} µm")
    print(f"   F range: {F1.min()*1e9:.2f} - {F1.max()*1e9:.2f} nN")
    savgol_worked = True
except Exception as e:
    print(f"   ✗ Filter failed: {e}")
    savgol_worked = False
    Z1, F1 = None, None

if savgol_worked:
    # Now switch to "none"
    print("\n3. Switching filter to 'none'...")
    descriptor.stages[0].steps[0].plugin_id = "none"
    descriptor.stages[0].steps[0].parameters = {}
    
    try:
        executor = PipelineExecutor(registry)
        executor.execute(descriptor, dataset)
        Z2, F2 = curve.get_current_data()
        print(f"   ✓ Reset succeeded: {len(Z2)} points")
        print(f"   Z range: {Z2.min()*1e6:.2f} - {Z2.max()*1e6:.2f} µm")
        print(f"   F range: {F2.min()*1e9:.2f} - {F2.max()*1e9:.2f} nN")
        
        # Check if we got back to raw data
        if np.allclose(Z2, Z0) and np.allclose(F2, F0):
            print("   ✓ Data correctly reset to raw values")
        else:
            print("   ⚠ Data differs from raw values")
    except Exception as e:
        print(f"   ✗ Reset failed: {e}")

print("\n" + "="*60)
print("Test completed. Check console output above for any errors.")
print("="*60)
