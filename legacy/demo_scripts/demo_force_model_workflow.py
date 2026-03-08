"""
Quick demonstration of force model fitting workflow.

This script demonstrates the updated pipeline with force model fitting:
1. Discover plugins (including force_models)
2. Create default pipeline with force_model step
3. Load synthetic data
4. Execute pipeline with hertz model
5. Display results
"""

from pathlib import Path
import numpy as np
from softmech.core.plugins import PluginRegistry
from softmech.core.pipeline import PipelineDescriptor, PipelineMetadata, PipelineStage, PipelineStep, PipelineExecutor
from softmech.core.data import Dataset, Curve, TipGeometry


def main():
    print("="*70)
    print("SoftMech Designer - Force Model Fitting Demo")
    print("="*70)
    
    # 1. Setup plugin registry (simulates _init_plugin_registry)
    print("\n1. Discovering plugins...")
    registry = PluginRegistry()
    plugins_path = Path('softmech/plugins')
    
    registry.discover(plugins_path / "filters", "softmech.plugins.filters", "filter")
    registry.discover(plugins_path / "contact_point", "softmech.plugins.contact_point", "contact_point")
    registry.discover(plugins_path / "force_models", "softmech.plugins.force_models", "force_model")
    
    print(f"   Filters: {list(registry.list('filter').keys())}")
    print(f"   Contact Point: {list(registry.list('contact_point').keys())[:3]}...")
    print(f"   Force Models: {list(registry.list('force_model').keys())}")
    
    # 2. Create default pipeline (simulates _create_default_pipeline)
    print("\n2. Creating default pipeline...")
    
    def make_step(step_type, plugin_id):
        plugin_info = registry.get_info(plugin_id)
        return PipelineStep(
            type=step_type,
            plugin_id=plugin_id,
            plugin_version=plugin_info.get("version", "1.0.0"),
            parameters={},
        )
    
    metadata = PipelineMetadata(
        name="Default Pipeline",
        description="Default pipeline with none placeholders",
    )
    
    preprocessing = PipelineStage(name="preprocessing", description="Filtering and contact point")
    preprocessing.add_step(make_step("filter", "none"))
    preprocessing.add_step(make_step("contact_point", "none"))
    
    analysis = PipelineStage(name="analysis", description="Model fitting")
    analysis.add_step(make_step("force_model", "none"))
    
    pipeline = PipelineDescriptor(metadata=metadata, stages=[preprocessing, analysis])
    
    print("   Default pipeline structure:")
    for i, step in enumerate(pipeline.get_all_steps(), 1):
        print(f"     {i}. {step.type:20s} -> {step.plugin_id}")
    
    # 3. Load data (simulates open_curve)
    print("\n3. Loading synthetic AFM data...")
    
    Z = np.linspace(-1e-6, 1e-6, 500)
    Z_cp = 0.0
    delta = np.maximum(0, Z - Z_cp)
    R = 1e-6  # 1 micron radius
    E_true = 1.5e3   # 1.5 kPa
    nu = 0.5
    F = (4.0/3.0) * (E_true / (1 - nu**2)) * np.sqrt(R * delta**3)
    F += np.random.normal(0, 1e-12, len(F))
    
    tip = TipGeometry(geometry_type="sphere", radius=R)
    curve = Curve(Z, F, spring_constant=0.032, tip_geometry=tip, index=0)
    dataset = Dataset(name="synthetic_demo")
    dataset.append(curve)
    
    print(f"   Loaded: {len(dataset)} curve with {len(Z)} data points")
    print(f"   Tip: {tip.geometry_type} with R={tip.radius*1e6:.1f} µm")
    print(f"   True E = {E_true:.1f} Pa")
    
    # 4. Configure pipeline (user would do this via UI)
    print("\n4. Configuring pipeline steps...")
    
    # User changes contact_point from "none" to "autothresh"
    cp_step = pipeline.get_all_steps()[1]
    cp_step.plugin_id = "autothresh"
    print(f"   Contact point: {cp_step.plugin_id}")
    
    # User changes force_model from "none" to "hertz"
    fm_step = pipeline.get_all_steps()[2]
    fm_step.plugin_id = "hertz"
    fm_step.parameters = {"poisson": 0.5}
    print(f"   Force model: {fm_step.plugin_id} with ν={fm_step.parameters['poisson']}")
    
    # 5. Execute pipeline (simulates run_pipeline)
    print("\n5. Running pipeline...")
    
    executor = PipelineExecutor(registry)
    
    def progress_callback(msg, val):
        print(f"   [{val*100:5.1f}%] {msg}")
    
    result = executor.execute(pipeline, dataset, progress_callback)
    
    # 6. Display results
    print("\n6. Results:")
    print("-" * 70)
    
    cp = curve.get_contact_point()
    if cp:
        print(f"   Contact Point: Z_cp = {cp[0]*1e9:.2f} nm, F_cp = {cp[1]*1e9:.2f} nN")
    
    indent_data = curve.get_indentation_data()
    if indent_data:
        delta_arr, f_ind = indent_data
        print(f"   Indentation: {len(delta_arr)} points, max δ = {np.max(delta_arr)*1e9:.2f} nm")
    
    force_params = curve.get_force_model_params()
    if force_params:
        E_fit = force_params[0]
        error = abs(E_fit - E_true) / E_true * 100
        print(f"   Fitted E = {E_fit:.1f} Pa")
        print(f"   Expected E = {E_true:.1f} Pa")
        print(f"   Error: {error:.1f}%")
        
        if error < 10:
            print("   ✓ Fitting successful!")
        else:
            print("   ⚠ Fitting has significant error")
    else:
        print("   ✗ No force model parameters calculated")
    
    print("\n" + "="*70)
    print("Demo complete!")
    print("="*70)


if __name__ == "__main__":
    main()
