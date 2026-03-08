"""
Pipeline Builder Design Comparison: List vs Flowchart

Exploring different UI paradigms for the softmech pipeline editor.
"""

# ============================================================================
# OPTION 1: Simple List View (Original Plan)
# ============================================================================

OPTION_1_LIST = """
┌─────────────────────────────────────────────────────────────────┐
│ LEFT PANEL: Pipeline Editor (List View)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Pipeline: default_analysis                                    │
│  ├─ Filter: savgol                                             │
│  │  └─ window_size: 25                                         │
│  ├─ Contact Point: autothresh                                  │
│  │  └─ threshold: 0.5                                          │
│  └─ Force Model: hertz                                         │
│     └─ radius: 3.4e-6                                          │
│                                                                 │
│  [Add Step ▼] [Remove] [Run Pipeline]                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Pros:
✓ Simple to implement (~4-6 hours)
✓ Familiar tree-view UI pattern
✓ Easy to understand parameter list
✓ Fast to build in Sprint 1

Cons:
✗ Non-intuitive for non-programmers
✗ Doesn't show data flow visually
✗ Hard to see pipeline structure at a glance
✗ Feels clunky compared to modern tools
✗ Doesn't scale well for complex pipelines (>5 steps)
"""

# ============================================================================
# OPTION 2: Flowchart/Node Graph (Recommended)
# ============================================================================

OPTION_2_FLOWCHART = """
┌─────────────────────────────────────────────────────────────────┐
│ LEFT PANEL: Pipeline Editor (Flowchart)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│              [Input]                                            │
│               Curve                                             │
│                │                                                │
│                ▼                                                │
│        ┌──────────────┐                                         │
│        │   savgol     │  window_size: 25 ◄─ Right-click       │
│        │   Filter     │  polyorder: 3       to edit            │
│        └──────────────┘                                         │
│                │                                                │
│                ▼                                                │
│        ┌──────────────┐                                         │
│        │  autothresh  │  threshold: 0.5 ◄─ Parameter           │
│        │  Contact Pt  │                        controls         │
│        └──────────────┘                                         │
│                │                                                │
│                ▼                                                │
│        ┌──────────────┐                                         │
│        │    hertz     │  radius: 3.4e-6                        │
│        │  Force Model │                                         │
│        └──────────────┘                                         │
│                │                                                │
│                ▼                                                │
│            [Output]                                             │
│         Processing                                              │
│            Results                                              │
│                                                                 │
│  [+ Add Step] [Run Pipeline ▶] [Save] [Load]                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Pros:
✓ Modern, intuitive visual representation
✓ Shows data flow explicitly (curve → filter → detection → output)
✓ Matches professional tools (Orange, Houdini, Nuke)
✓ Scales well for complex pipelines
✓ PyQtGraph has built-in flowchart module
✓ Self-documenting (visual specification)
✓ Non-programmers understand it immediately
✓ Aligns with our pipeline descriptor model
✓ Ready for drag-drop enhancements in future

Cons:
✗ Slightly more implementation (~8-10 hours, not 4-6)
✗ Need to learn PyQtGraph.flowchart module
✗ Initial complexity higher (worth it)
"""

# ============================================================================
# TECHNOLOGY COMPARISON
# ============================================================================

TECH_COMPARISON = """
┌────────────────────────────────────────────────────────────────────┐
│ IMPLEMENTATION APPROACHES                                          │
├────────────────────────┬─────────────────────┬────────────────────┤
│ Aspect                 │ Custom QGraphicsView│ PyQtGraph Flowchart│
├────────────────────────┼─────────────────────┼────────────────────┤
│ Ease of Implementation │ Moderate (5-8 hrs)  │ Easy (3-4 hrs) ✓✓  │
│                        │ Need to code nodes  │ Built-in nodes     │
├────────────────────────┼─────────────────────┼────────────────────┤
│ Existing Examples      │ Many examples exist │ PyQtGraph examples ✓│
│                        │ (Qt docs)           │ Direct use         │
├────────────────────────┼─────────────────────┼────────────────────┤
│ Customization          │ Unlimited           │ Very extensible    │
│ (add brand, colors)    │                     │                    │
├────────────────────────┼─────────────────────┼────────────────────┤
│ Drag-Drop Support      │ Manual coding       │ Built-in ✓         │
├────────────────────────┼─────────────────────┼────────────────────┤
│ Node Parameter UI      │ Pop-up dialog       │ Integrated ✓       │
├────────────────────────┼──────────────────────┼────────────────────┤
│ Automatic Layout       │ Manual setup        │ Built-in ✓         │
├────────────────────────┼─────────────────────┼────────────────────┤
│ Connection Validation  │ Manual              │ Type checking ✓    │
├────────────────────────┼─────────────────────┼────────────────────┤
│ Integration w/ magicgui│ Possible            │ Seamless ✓✓        │
├────────────────────────┼─────────────────────┼────────────────────┤
│ Documentation          │ Extensive           │ Good ✓             │
└────────────────────────┴─────────────────────┴────────────────────┘

RECOMMENDATION: Use PyQtGraph.flowchart
- It's already optimized for exactly this use case
- Drag-drop is built-in
- Node creation from our plugins is straightforward
- Documentation is adequate
- 3-4 hours vs 5-8 hours for custom QGraphicsView
"""

# ============================================================================
# ORANGE DATA MINING EXAMPLE
# ============================================================================

ORANGE_APPROACH = """
Orange Visual Programming (reference for UX design):

https://orange.readthedocs.io/widgets/

Features we could learn from:
1. Colorized node categories (Filter=blue, Contact=green, Model=orange)
2. Connection validation (prevents invalid connections)
3. Parameter editing in side panel (not modal dialogs)
4. Automatic layout suggestions
5. Save/load workflow as .ows file (we use .json already ✓)
6. Thumbnail preview of results

Applied to softmech:

┌──────────────────────────────────────────┐
│ Node Colors by Category:                 │
│                                          │
│  🟦 Filters (savgol, median, etc.)      │
│  🟩 Contact Point Detectors (autothresh)│
│  🟧 Force Models (hertz, etc.)          │
│  🟨 Elastic Models (constant, etc.)     │
│  🟪 Exporters (scatter, average)        │
│                                          │
└──────────────────────────────────────────┘

This would make it VERY easy to see what type each node is
just by color. No need to read labels!
"""

# ============================================================================
# PYQTGRAPH FLOWCHART MODULE
# ============================================================================

PYQTGRAPH_FLOWCHART = """
PyQtGraph has a built-in flowchart.FlowchartWidget!

Key classes:
- FlowchartWidget: Main editor widget
- Node: Base class for flowchart nodes
- Terminal: Input/output sockets for nodes
- Flowchart: Container for nodes + connections

Example structure:

    from pyqtgraph.flowchart import FlowchartWidget, Node
    from pyqtgraph.flowchart.library.common import Output, Input
    import pyqtgraph as pg
    
    class PipelineFlowchart(FlowchartWidget):
        def __init__(self, registry):
            super().__init__(terminals={
                'Curve': {'io': 'in'},
                'Result': {'io': 'out'}
            })
            self.registry = registry
            
            # Create nodes from plugins
            for filter_id in registry.get_all('filters'):
                plugin = registry.get(filter_id)
                node = self.create_plugin_node(plugin)
                self.addNode(node, pos=(0, 0))
        
        def create_plugin_node(self, plugin):
            \"\"\"Create a flowchart node from a plugin.\"\"\"
            class PluginNode(Node):
                nodeName = plugin.NAME
                
                def __init__(self, name):
                    terminals = {
                        'In': {'io': 'in', 'multi': False},
                        'Out': {'io': 'out', 'multi': False}
                    }
                    # Add parameter sockets
                    for param_name in plugin.get_parameter_names():
                        terminals[param_name] = {
                            'io': 'in',
                            'value': plugin.get_parameter(param_name)
                        }
                    Node.__init__(self, name, terminals=terminals)
                
                def process(self, In, **keywords):
                    # Execute plugin with input curve and params
                    result = plugin.process(In, **keywords)
                    return {'Out': result}
            
            return PluginNode(plugin.NAME)

ADVANTAGES for softmech:
✓ Don't have to implement nodes from scratch
✓ Drag-drop connections are automatic
✓ Parameter editing can be integrated with magicgui
✓ Visual representation is professional
✓ Execution model matches our PipelineExecutor
"""

# ============================================================================
# SPRINT 1 IMPLEMENTATION STRATEGY
# ============================================================================

SPRINT_1_STRATEGY = """
╔════════════════════════════════════════════════════════════════════╗
║ UPDATED SPRINT 1 WEEK 1C: Flowchart Pipeline Editor              ║
╚════════════════════════════════════════════════════════════════════╝

OPTION A: Minimal Flowchart (6-8 hours)
────────────────────────────────────────────────────────────────────

Use PyQtGraph.flowchart with pre-created nodes for core plugins:
- Input: Curve dataset
- savgol Filter node
- autothresh Contact Point node
- hertz Force Model node
- Output: ProcessingResult

Features:
✓ Visual pipeline display
✓ Nodes can be dragged around
✓ Connections show data flow
✓ Double-click node to edit parameters (pop-up dialog)
✓ "Run Pipeline" executes in order
✓ "Save Pipeline" exports to JSON

Estimated time:
- Setup FlowchartWidget: 2 hours
- Create plugin nodes: 2 hours
- Parameter editing: 1 hour
- Integration + testing: 1-2 hours
Total: 6-8 hours (reasonable for Week 1c)

File: softmech/ui/designer/widgets/pipeline_editor.py


OPTION B: Full Graphical Pipeline Builder (10-14 hours) [SKIP FOR NOW]
────────────────────────────────────────────────────────────────────

For future sprints (Week 2+):
- Drag nodes from palette onto canvas
- Full parameter panel in right sidebar
- Live preview as you change parameters
- Connection validation (type checking)
- Colorized node categories
- Auto-layout suggestions
- History/undo

This is the "Orange-style" experience.


RECOMMENDATION FOR SPRINT 1:

Go with OPTION A: Minimal Flowchart
- 6-8 hours is reasonable (extends Week 1c from 4-6 to 6-8)
- User gets modern visual experience immediately
- Foundation is there for Option B in Sprint 2
- Better than list view at no massive cost
"""

# ============================================================================
# DETAILED PSEUDOCODE
# ============================================================================

PSEUDOCODE = """
# Week 1c Implementation Pseudocode

from pyqtgraph.flowchart import FlowchartWidget, Node
import pyqtgraph as pg

class SoftmechFlowchart(FlowchartWidget):
    \"\"\"Visual pipeline editor using PyQtGraph flowchart.\"\"\"
    
    def __init__(self, registry):
        # Define I/O terminals
        terminals = {
            'CurveIn': {'io': 'in'},
            'ResultOut': {'io': 'out'}
        }
        super().__init__(terminals=terminals)
        
        self.registry = registry
        self.nodes_by_plugin = {}
        
        # Pre-populate with common pipeline nodes
        self.setup_default_nodes()
        
    def setup_default_nodes(self):
        \"\"\"Create nodes for savgol, autothresh, hertz.\"\"\"
        
        # Node 1: SavGol Filter
        savgol_node = self.create_plugin_node('savgol', pos=(100, 0))
        self.addNode(savgol_node, name='savgol_step')
        
        # Node 2: AutoThresh Contact Point Detection
        autothresh_node = self.create_plugin_node('autothresh', pos=(300, 0))
        self.addNode(autothresh_node, name='autothresh_step')
        
        # Node 3: Hertz Force Model Fitting
        hertz_node = self.create_plugin_node('hertz', pos=(500, 0))
        self.addNode(hertz_node, name='hertz_step')
        
        # Connect Output of previous node to Input of next
        # This could be automatic or user-managed
    
    def create_plugin_node(self, plugin_id, pos=(0, 0)):
        \"\"\"Create a flowchart node for a plugin.\"\"\"
        
        plugin = self.registry.get(plugin_id)
        params = plugin.get_parameters()
        
        # Define terminals: In, Out, + one per parameter
        terminals = {
            'In': {'io': 'in', 'multi': False},
            'Out': {'io': 'out', 'multi': False}
        }
        
        # Add parameter terminals
        for param_name, param_info in params.items():
            terminals[param_name] = {
                'io': 'in',
                'value': param_info['value'],
                'type': param_info['type']
            }
        
        # Create node class
        class PluginNode(Node):
            nodeName = plugin.NAME
            
            def __init__(self, name):
                Node.__init__(self, name, terminals=terminals)
                self.plugin = plugin
                self.params = {k: v['value'] for k, v in params.items()}
            
            def process(self, In, **kwargs):
                # Get current parameter values
                for param_name in self.params:
                    if param_name in kwargs:
                        self.params[param_name] = kwargs[param_name]
                
                # Execute plugin
                result = self.plugin.process(In, **self.params)
                return {'Out': result}
            
            def double_clicked(self, event):
                \"\"\"Open parameter editor when node double-clicked.\"\"\"
                self.show_parameter_dialog()
            
            def show_parameter_dialog(self):
                \"\"\"Show dialog to edit parameters.\"\"\"
                # Could use magicgui here for fancy parameter UI
                # Or simple QDialog with spinboxes, sliders
                pass
        
        return PluginNode(plugin.NAME)
    
    def execute_pipeline(self, input_curve):
        \"\"\"Run the flowchart on input curve.\"\"\"
        # Topologically sort nodes
        # Execute in order
        # Connect outputs to next inputs
        result = self.fc.process(CurveIn=input_curve)
        return result['ResultOut']
    
    def to_json(self):
        \"\"\"Export pipeline as JSON.\"\"\"
        pipeline_dict = {
            'stages': [],
            'connections': []
        }
        
        for node_name, node in self.nodes().items():
            stage = {
                'name': node_name,
                'plugin_id': node.plugin.ID,
                'version': node.plugin.VERSION,
                'parameters': node.params
            }
            pipeline_dict['stages'].append(stage)
        
        # Export connections (which output feeds to which input)
        return pipeline_dict
    
    def from_json(self, pipeline_dict):
        \"\"\"Load pipeline from JSON.\"\"\"
        # Clear current nodes
        self.fc.clear()
        
        # Recreate nodes in order
        for stage in pipeline_dict['stages']:
            node = self.create_plugin_node(stage['plugin_id'])
            node.params.update(stage['parameters'])
            self.addNode(node, name=stage['name'])
        
        # Recreate connections
        for conn in pipeline_dict['connections']:
            # Connect nodes according to saved connections
            pass


# Integration with main_window.py:

class DesignerMainWindow(QMainWindow):
    
    def __init__(self):
        # ...existing code...
        self.pipeline_editor = SoftmechFlowchart(self.registry)
        self.left_layout.addWidget(self.pipeline_editor)
    
    def run_pipeline(self):
        \"\"\"Execute the flowchart pipeline on current curve.\"\"\"
        if self.current_curve is None:
            self.status_bar.showMessage("No curve loaded")
            return
        
        result = self.pipeline_editor.execute_pipeline(self.current_curve)
        
        # Update visualization with result
        self.visualization.plot_filtered_curve(result.F)
        self.status_bar.showMessage("Pipeline executed successfully")


"""

# ============================================================================
# FINAL RECOMMENDATION
# ============================================================================

RECOMMENDATION = """
════════════════════════════════════════════════════════════════════

RECOMMENDATION: Use PyQtGraph Flowchart (OPTION A)

Why this is the right choice:

1. MODERN UX
   Users immediately recognize this as a professional pipeline tool
   (like Orange, Nuke, etc.). Not a grid/list view like 1990s software.

2. SELF-DOCUMENTING
   The visual structure IS the specification. Anyone looking at it
   understands: Curve → Filter → Contact Point → Force Model → Output

3. PYQTGRAPH ALREADY HAS IT
   Don't reinvent the wheel. flowchart.FlowchartWidget is designed
   for exactly this. Just wrap our plugins as nodes.

4. REASONABLE EFFORT
   6-8 hours is acceptable for Week 1c (extends from 4-6 to 6-8).
   Not a huge time sink, huge UX improvement.

5. FOUNDATION FOR FUTURE
   Option B (full drag-drop builder) is Phase 2.
   You're not committing to future work; you're enabling it.

6. ALIGNS WITH ARCHITECTURE
   Our PipelineDescriptor is already a chain of stages.
   Flowchart is the perfect visual representation.

SPRINT 1 WEEK 1C REVISED:

Old: Pipeline Editor (List) - 4-6 hours
New: Pipeline Editor (Flowchart) - 6-8 hours

Deliverable:
✓ FlowchartWidget showing savgol → autothresh → hertz chain
✓ Double-click nodes to edit parameters
✓ "Run Pipeline" button executes the chain
✓ Save/Load as JSON
✓ Visual is professional and modern

Next Sprint (Week 2):
✓ Add drag-drop node palette
✓ Parameter panel in right sidebar
✓ Connection validation
✓ Colorized node categories
✓ Auto-layout

════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(OPTION_1_LIST)
    print("\n")
    print(OPTION_2_FLOWCHART)
    print("\n")
    print(TECH_COMPARISON)
    print("\n")
    print(ORANGE_APPROACH)
    print("\n")
    print(PYQTGRAPH_FLOWCHART)
    print("\n")
    print(SPRINT_1_STRATEGY)
    print("\n")
    print(PSEUDOCODE)
    print("\n")
    print(RECOMMENDATION)
