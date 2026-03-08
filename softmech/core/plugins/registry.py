"""
Plugin discovery and registry system.

Dynamically discovers and loads plugins from plugin directories at runtime.
Supports multiple plugin locations and categories (filters, contact_point, etc.)
"""

from importlib import import_module
from pathlib import Path
from typing import Dict, Type, Optional, List
import logging

from .base import PluginBase, Filter, ContactPointDetector, ForceModel, ElasticModel, Exporter

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Discovers and manages plugins at runtime.

    Plugins are discovered by scanning directories for .py files.
    Convention: One file = One plugin.

    Each plugin module must define:
    - NAME: str - Display name
    - DESCRIPTION: str - What it does
    - VERSION: str - Version string (e.g., "1.0.0")
    - DOI: str - Optional publication DOI
    - One of: Filter, ContactPointDetector, ForceModel, ElasticModel, Exporter class
    """

    # Mapping from category to expected class name
    CATEGORY_TO_CLASS = {
        "filter": Filter,
        "contact_point": ContactPointDetector,
        "force_model": ForceModel,
        "elastic_model": ElasticModel,
        "exporter": Exporter,
    }

    def __init__(self):
        """Initialize empty registry."""
        self.plugins: Dict[str, Type[PluginBase]] = {}
        self.plugin_info: Dict[str, dict] = {}

    def discover(self, plugin_dir: Path, package_name: str, category: str) -> Dict[str, str]:
        """
        Scan directory for plugins and load them.

        Discovers all .py files in the directory (excluding _* and __init__.py)
        and attempts to load them as plugins.

        Parameters
        ----------
        plugin_dir : Path
            Directory to scan (e.g., softmech/plugins/filters)
        package_name : str
            Python package name (e.g., 'softmech.plugins.filters')
        category : str
            Category name ('filter', 'contact_point', etc.)

        Returns
        -------
        dict
            {plugin_id: display_name} for found plugins
        """
        found_plugins = {}

        if not plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {plugin_dir}")
            return found_plugins

        # Scan for .py files
        for py_file in sorted(plugin_dir.glob("*.py")):
            # Skip private/init files
            if py_file.name.startswith("_") or py_file.name == "__init__.py":
                continue

            plugin_id = py_file.stem

            try:
                # Dynamically import module
                module = import_module(f"{package_name}.{plugin_id}")

                # Check for required attributes
                if not hasattr(module, "NAME"):
                    logger.warning(f"Plugin {plugin_id} missing NAME attribute - skipping")
                    continue

                # Extract plugin class
                plugin_class = self._get_plugin_class(module, category)
                if plugin_class is None:
                    logger.warning(
                        f"Plugin {plugin_id} missing implementation class for category {category}"
                    )
                    continue

                # Store plugin information
                self.plugins[plugin_id] = plugin_class
                self.plugin_info[plugin_id] = {
                    "name": module.NAME,
                    "description": getattr(module, "DESCRIPTION", ""),
                    "doi": getattr(module, "DOI", ""),
                    "equation": getattr(module, "EQUATION", ""),
                    "version": getattr(module, "VERSION", "1.0.0"),
                    "category": category,
                    "module": module,
                }

                found_plugins[plugin_id] = module.NAME
                logger.info(f"Loaded plugin: {plugin_id} ({module.NAME}) v{self.plugin_info[plugin_id]['version']}")

            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_id}: {e}", exc_info=True)
                continue

        return found_plugins

    @staticmethod
    def _get_plugin_class(module, category: str) -> Optional[Type[PluginBase]]:
        """
        Extract plugin class from module based on category.

        Parameters
        ----------
        module : module
            Imported module
        category : str
            Plugin category

        Returns
        -------
        Type or None
            Plugin class if found, None otherwise
        """
        expected_class_name = {
            "filter": Filter.__name__,
            "contact_point": ContactPointDetector.__name__,
            "force_model": ForceModel.__name__,
            "elastic_model": ElasticModel.__name__,
            "exporter": Exporter.__name__,
        }.get(category)

        if not expected_class_name:
            return None

        cls = getattr(module, expected_class_name, None)
        
        # Verify it's actually a subclass of the expected base
        if cls and issubclass(cls, PluginRegistry.CATEGORY_TO_CLASS.get(category, PluginBase)):
            return cls
        
        return None

    def get(self, plugin_id: str) -> PluginBase:
        """
        Instantiate a plugin by ID.

        Parameters
        ----------
        plugin_id : str
            Plugin identifier

        Returns
        -------
        PluginBase
            New instance of the plugin

        Raises
        ------
        KeyError
            If plugin_id not found
        """
        if plugin_id not in self.plugins:
            raise KeyError(f"Unknown plugin: {plugin_id}")

        return self.plugins[plugin_id]()

    def list(self, category: Optional[str] = None) -> Dict[str, str]:
        """
        List all loaded plugins.

        Parameters
        ----------
        category : str, optional
            Filter by category (e.g., 'filter'). If None, return all.

        Returns
        -------
        dict
            {plugin_id: display_name}
        """
        result = {}
        for plugin_id, info in self.plugin_info.items():
            if category is None or info["category"] == category:
                result[plugin_id] = info["name"]
        return result

    def get_info(self, plugin_id: str) -> dict:
        """
        Get metadata about a plugin.

        Parameters
        ----------
        plugin_id : str
            Plugin identifier

        Returns
        -------
        dict
            Plugin metadata (name, description, version, doi, etc.)
        """
        return self.plugin_info.get(plugin_id, {})

    def get_all_info(self) -> Dict[str, dict]:
        """
        Get metadata for all plugins.

        Returns
        -------
        dict
            {plugin_id: metadata}
        """
        return self.plugin_info.copy()
