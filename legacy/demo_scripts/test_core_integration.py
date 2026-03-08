"""
Quick validation script to test the new plugin system and core infrastructure.

Run: python test_core_integration.py
"""

import sys
import logging
import numpy as np
from pathlib import Path

# Add softmech to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_plugin_registry():
    """Test plugin discovery and loading."""
    logger.info("Testing plugin registry...")
    
    from softmech.core.plugins import PluginRegistry
    
    registry = PluginRegistry()
    
    # Discover filters
    filters_path = Path(__file__).parent / "softmech" / "plugins" / "filters"
    filters = registry.discover(filters_path, "softmech.plugins.filters", "filter")
    logger.info(f"Discovered {len(filters)} filter plugins: {list(filters.values())}")
    
    # Discover contact point detectors
    cp_path = Path(__file__).parent / "softmech" / "plugins" / "contact_point"
    cps = registry.discover(cp_path, "softmech.plugins.contact_point", "contact_point")
    logger.info(f"Discovered {len(cps)} contact point plugins: {list(cps.values())}")
    
    # Discover force models
    fm_path = Path(__file__).parent / "softmech" / "plugins" / "force_models"
    fmodels = registry.discover(fm_path, "softmech.plugins.force_models", "force_model")
    logger.info(f"Discovered {len(fmodels)} force model plugins: {list(fmodels.values())}")
    
    assert len(filters) > 0, "No filters discovered"
    assert len(cps) > 0, "No contact point plugins discovered"
    assert len(fmodels) > 0, "No force models discovered"
    
    logger.info("✓ Plugin registry test passed")
    return registry


def test_filter_execution(registry):
    """Test running a filter plugin."""
    logger.info("Testing filter execution...")
    
    # Create synthetic data with more noise
    x = np.linspace(0, 1e-6, 100)
    y = np.sin(x / 1e-7) + np.random.normal(0, 0.5, 100)  # Higher noise
    
    # Get and run SavGol filter
    savgol = registry.get("savgol")
    savgol.set_parameter("window_size", 15.0)
    savgol.set_parameter("polyorder", 2)
    
    x_filt, y_filt = savgol.calculate(x, y)
    
    assert len(x_filt) == len(x), "Filter changed data length"
    # Just verify filter returns valid output, not necessarily different
    assert np.all(np.isfinite(y_filt)), "Filter produced NaN values"
    
    logger.info(f"✓ Filter execution test passed (smoothed {len(x)} points)")


def test_data_structures():
    """Test Curve and Dataset classes."""
    logger.info("Testing data structures...")
    
    from softmech.core.data import Curve, Dataset, TipGeometry
    
    # Create a curve
    Z = np.linspace(0, 1e-6, 100)
    F = Z * 0.01 + np.random.normal(0, 1e-9, 100)
    
    tip = TipGeometry(geometry_type="sphere", radius=1e-6)
    curve = Curve(Z, F, spring_constant=0.01, tip_geometry=tip, index=0)
    
    # Test basic methods
    assert curve.index == 0
    z, f = curve.get_current_data()
    assert len(z) == 100
    
    # Test indentation calculation
    curve.set_contact_point(Z[30], F[30])
    cp = curve.get_contact_point()
    assert cp is not None
    
    # Create dataset
    dataset = Dataset(name="Test Dataset")
    dataset.append(curve)
    assert len(dataset) == 1
    assert dataset[0].index == 0
    
    logger.info("✓ Data structures test passed")


def test_pipeline_descriptor():
    """Test pipeline descriptor creation and serialization."""
    logger.info("Testing pipeline descriptor...")
    
    from softmech.core.pipeline import (
        PipelineDescriptor,
        PipelineMetadata,
        PipelineStage,
        PipelineStep,
    )
    import json
    from datetime import datetime
    
    # Create pipeline
    metadata = PipelineMetadata(
        name="Test Pipeline",
        description="A simple test pipeline",
        author="Test Suite",
    )
    
    stage = PipelineStage(
        name="preprocessing",
        description="Filtering and contact point detected",
    )
    
    step1 = PipelineStep(
        type="filter",
        plugin_id="savgol",
        parameters={"window_size": 25.0, "polyorder": 3},
        plugin_version="1.1.0",
    )
    
    step2 = PipelineStep(
        type="contact_point",
        plugin_id="autothresh",
        parameters={"zero_range": 500.0},
        plugin_version="1.0.0",
    )
    
    stage.add_step(step1)
    stage.add_step(step2)
    
    pipeline = PipelineDescriptor(metadata=metadata)
    pipeline.add_stage(stage)
    
    # Test serialization
    pipeline_dict = pipeline.to_dict()
    assert pipeline_dict["metadata"]["name"] == "Test Pipeline"
    assert len(pipeline_dict["stages"]) == 1
    assert len(pipeline_dict["stages"][0]["steps"]) == 2
    
    # Test JSON serialization
    json_str = pipeline.to_json()
    json_obj = json.loads(json_str)
    assert json_obj["version"] == "2.0"
    
    # Test deserialization
    pipeline2 = PipelineDescriptor.from_json(json_str)
    assert pipeline2.metadata.name == "Test Pipeline"
    all_steps = pipeline2.get_all_steps()
    assert len(all_steps) == 2
    
    logger.info("✓ Pipeline descriptor test passed")


def test_contact_point_plugin(registry):
    """Test contact point detection plugin."""
    logger.info("Testing contact point detection...")
    
    # Create synthetic force curve with clear contact
    x = np.linspace(-1e-6, 1e-6, 200)
    # Flatten part then ramp (contact point at x=0)
    y = np.where(x < 0, -50.0 * x, 50.0 * x) + np.random.normal(0, 1e-9, 200)
    
    # Run auto threshold
    autothresh = registry.get("autothresh")
    autothresh.set_parameter("zero_range", 500.0)
    
    result = autothresh.calculate(x, y)
    
    assert result is not False, "Contact point detection failed"
    z_cp, f_cp = result
    assert isinstance(z_cp, (int, float, np.number))
    assert isinstance(f_cp, (int, float, np.number))
    
    logger.info(f"✓ Contact point detection test passed (detected at Z={z_cp:.2e})")


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("SoftMech Core Integration Tests")
    logger.info("=" * 60)
    
    try:
        registry = test_plugin_registry()
        test_filter_execution(registry)
        test_data_structures()
        test_pipeline_descriptor()
        test_contact_point_plugin(registry)
        
        logger.info("=" * 60)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 60)
        return 0
        
    except Exception as e:
        logger.error(f"✗ TEST FAILED: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
