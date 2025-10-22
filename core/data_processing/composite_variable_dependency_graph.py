"""
Composite Variable Dependency Graph
====================================

Sophisticated dependency graph system using networkx for managing calculation order
of composite financial variables. Ensures base variables are processed before
dependent calculations through topological sorting and cycle detection.

This module implements:
- Directed graph modeling of variable dependencies
- Topological sorting for optimal calculation order
- Cycle detection for invalid dependency chains
- Dynamic dependency updates
- Visualization capabilities
- Impact analysis for variable changes

Usage Example
-------------
>>> from composite_variable_dependency_graph import CompositeVariableDependencyGraph
>>>
>>> # Create dependency graph
>>> graph = CompositeVariableDependencyGraph()
>>>
>>> # Add variables with dependencies
>>> graph.add_variable("net_income")
>>> graph.add_variable("revenue")
>>> graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])
>>>
>>> # Get calculation order
>>> order = graph.get_calculation_order()
>>> print(order)  # ['net_income', 'revenue', 'profit_margin']
>>>
>>> # Check for cycles
>>> is_valid, errors = graph.validate_dependencies()
>>> print(f"Valid: {is_valid}")
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path
import networkx as nx
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class VariableNode:
    """
    Represents a variable node in the dependency graph.

    Attributes:
        name: Variable name
        category: Variable category (income_statement, balance_sheet, etc.)
        is_base: Whether this is a base variable (no dependencies)
        dependencies: List of variable names this depends on
        dependents: List of variable names that depend on this
        metadata: Additional metadata about the variable
    """
    name: str
    category: str = "unknown"
    is_base: bool = True
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, VariableNode):
            return self.name == other.name
        return False


class CompositeVariableDependencyGraph:
    """
    Manages dependency relationships between financial variables using a directed graph.

    This class uses networkx.DiGraph to model variable dependencies and provides:
    - Topological sorting for calculation order
    - Cycle detection for invalid dependencies
    - Dependency validation
    - Dynamic dependency updates
    - Visualization capabilities
    - Impact analysis

    The graph is a directed acyclic graph (DAG) where:
    - Nodes represent variables
    - Edges represent dependencies (A -> B means B depends on A)
    - Topological sort gives the calculation order
    """

    def __init__(self):
        """Initialize an empty dependency graph."""
        self._graph: nx.DiGraph = nx.DiGraph()
        self._nodes: Dict[str, VariableNode] = {}
        self._calculation_order: Optional[List[str]] = None
        self._calculation_order_dirty: bool = True

        logger.info("CompositeVariableDependencyGraph initialized")

    def add_variable(
        self,
        name: str,
        category: str = "unknown",
        depends_on: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a variable to the dependency graph.

        Args:
            name: Variable name
            category: Variable category (e.g., "income_statement", "calculated")
            depends_on: List of variable names this depends on
            metadata: Additional metadata

        Returns:
            True if successfully added, False if already exists
        """
        if name in self._nodes:
            logger.warning(f"Variable {name} already exists in graph")
            return False

        depends_on = depends_on or []
        metadata = metadata or {}

        # Create node
        node = VariableNode(
            name=name,
            category=category,
            is_base=len(depends_on) == 0,
            dependencies=depends_on.copy(),
            metadata=metadata
        )

        # Add to graph
        self._graph.add_node(name, data=node)
        self._nodes[name] = node

        # Add dependency edges
        for dep in depends_on:
            if dep not in self._nodes:
                # Auto-add missing dependencies as base variables
                logger.info(f"Auto-adding base variable {dep} for dependency")
                self.add_variable(dep, category="auto_added")

            # Add edge from dependency to this variable
            self._graph.add_edge(dep, name)
            self._nodes[dep].dependents.append(name)

        # Mark calculation order as dirty
        self._calculation_order_dirty = True

        logger.info(f"Added variable {name} with {len(depends_on)} dependencies")
        return True

    def remove_variable(self, name: str) -> bool:
        """
        Remove a variable from the dependency graph.

        Args:
            name: Variable name to remove

        Returns:
            True if successfully removed, False if not found
        """
        if name not in self._nodes:
            logger.warning(f"Variable {name} not found in graph")
            return False

        # Remove from graph
        self._graph.remove_node(name)

        # Update dependent nodes
        node = self._nodes[name]
        for dep in node.dependencies:
            if dep in self._nodes:
                self._nodes[dep].dependents.remove(name)

        # Remove from nodes dict
        del self._nodes[name]

        # Mark calculation order as dirty
        self._calculation_order_dirty = True

        logger.info(f"Removed variable {name}")
        return True

    def add_dependency(self, variable: str, depends_on: str) -> bool:
        """
        Add a dependency relationship between two variables.

        Args:
            variable: The variable that depends on another
            depends_on: The variable that is depended upon

        Returns:
            True if successfully added, False otherwise
        """
        if variable not in self._nodes:
            logger.error(f"Variable {variable} not found")
            return False

        if depends_on not in self._nodes:
            logger.info(f"Auto-adding base variable {depends_on}")
            self.add_variable(depends_on, category="auto_added")

        # Check if this would create a cycle
        if nx.has_path(self._graph, variable, depends_on):
            logger.error(f"Adding dependency {depends_on} -> {variable} would create a cycle")
            return False

        # Add edge
        self._graph.add_edge(depends_on, variable)
        self._nodes[variable].dependencies.append(depends_on)
        self._nodes[depends_on].dependents.append(variable)
        self._nodes[variable].is_base = False

        # Mark calculation order as dirty
        self._calculation_order_dirty = True

        logger.info(f"Added dependency: {variable} depends on {depends_on}")
        return True

    def remove_dependency(self, variable: str, depends_on: str) -> bool:
        """
        Remove a dependency relationship.

        Args:
            variable: The variable that depends on another
            depends_on: The variable to remove from dependencies

        Returns:
            True if successfully removed, False otherwise
        """
        if variable not in self._nodes or depends_on not in self._nodes:
            logger.error(f"One or both variables not found")
            return False

        if not self._graph.has_edge(depends_on, variable):
            logger.warning(f"No dependency edge exists from {depends_on} to {variable}")
            return False

        # Remove edge
        self._graph.remove_edge(depends_on, variable)
        self._nodes[variable].dependencies.remove(depends_on)
        self._nodes[depends_on].dependents.remove(variable)

        # Update is_base status
        if len(self._nodes[variable].dependencies) == 0:
            self._nodes[variable].is_base = True

        # Mark calculation order as dirty
        self._calculation_order_dirty = True

        logger.info(f"Removed dependency: {variable} no longer depends on {depends_on}")
        return True

    def has_cycle(self) -> Tuple[bool, Optional[List[str]]]:
        """
        Check if the dependency graph contains cycles.

        Returns:
            Tuple of (has_cycle, cycle_path)
            - has_cycle: True if cycle exists
            - cycle_path: List of variables in the cycle, or None
        """
        try:
            # Try to find a cycle
            cycle = nx.find_cycle(self._graph, orientation='original')
            # Convert edge list to node list
            cycle_nodes = [edge[0] for edge in cycle] + [cycle[-1][1]]
            return True, cycle_nodes
        except nx.NetworkXNoCycle:
            return False, None

    def get_calculation_order(self, force_recalculate: bool = False) -> List[str]:
        """
        Get the topological order for calculating variables.

        Base variables (no dependencies) come first, followed by variables
        that depend on them, etc.

        Args:
            force_recalculate: Force recalculation even if cached

        Returns:
            List of variable names in calculation order

        Raises:
            ValueError: If graph contains cycles
        """
        if not self._calculation_order_dirty and self._calculation_order and not force_recalculate:
            return self._calculation_order.copy()

        # Check for cycles first
        has_cycle, cycle = self.has_cycle()
        if has_cycle:
            cycle_str = " -> ".join(cycle)
            raise ValueError(f"Dependency graph contains cycle: {cycle_str}")

        # Perform topological sort
        try:
            order = list(nx.topological_sort(self._graph))
            self._calculation_order = order
            self._calculation_order_dirty = False
            logger.info(f"Calculated topological order for {len(order)} variables")
            return order.copy()
        except nx.NetworkXError as e:
            raise ValueError(f"Failed to calculate topological order: {str(e)}")

    def validate_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Validate the dependency graph for common issues.

        Checks for:
        - Cycles
        - Missing dependencies
        - Orphaned variables

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check for cycles
        has_cycle, cycle = self.has_cycle()
        if has_cycle:
            cycle_str = " -> ".join(cycle)
            errors.append(f"Dependency cycle detected: {cycle_str}")

        # Check for missing dependencies (this shouldn't happen with auto-add)
        for name, node in self._nodes.items():
            for dep in node.dependencies:
                if dep not in self._nodes:
                    errors.append(f"Variable {name} depends on missing variable {dep}")

        # Check for orphaned variables (no dependencies and no dependents)
        orphaned = [
            name for name, node in self._nodes.items()
            if len(node.dependencies) == 0 and len(node.dependents) == 0
        ]
        if orphaned:
            logger.warning(f"Found {len(orphaned)} orphaned variables: {orphaned}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_dependencies(self, variable: str, recursive: bool = False) -> List[str]:
        """
        Get all dependencies for a variable.

        Args:
            variable: Variable name
            recursive: If True, get all transitive dependencies

        Returns:
            List of dependency variable names
        """
        if variable not in self._nodes:
            logger.warning(f"Variable {variable} not found")
            return []

        if not recursive:
            return self._nodes[variable].dependencies.copy()

        # Get all ancestors (transitive dependencies)
        try:
            ancestors = nx.ancestors(self._graph, variable)
            return list(ancestors)
        except nx.NetworkXError:
            return []

    def get_dependents(self, variable: str, recursive: bool = False) -> List[str]:
        """
        Get all variables that depend on this variable.

        Args:
            variable: Variable name
            recursive: If True, get all transitive dependents

        Returns:
            List of dependent variable names
        """
        if variable not in self._nodes:
            logger.warning(f"Variable {variable} not found")
            return []

        if not recursive:
            return self._nodes[variable].dependents.copy()

        # Get all descendants (transitive dependents)
        try:
            descendants = nx.descendants(self._graph, variable)
            return list(descendants)
        except nx.NetworkXError:
            return []

    def get_impact_analysis(self, variable: str) -> Dict[str, Any]:
        """
        Analyze the impact of changing a variable.

        Returns information about:
        - Direct dependents
        - All affected variables (transitive)
        - Calculation depth from this variable

        Args:
            variable: Variable name to analyze

        Returns:
            Dictionary with impact analysis results
        """
        if variable not in self._nodes:
            return {
                "variable": variable,
                "exists": False,
                "error": "Variable not found"
            }

        direct_dependents = self.get_dependents(variable, recursive=False)
        all_affected = self.get_dependents(variable, recursive=True)

        # Calculate depth (longest path from this variable to any leaf)
        try:
            if len(all_affected) == 0:
                max_depth = 0
            else:
                depths = []
                for affected in all_affected:
                    try:
                        path_length = nx.shortest_path_length(self._graph, variable, affected)
                        depths.append(path_length)
                    except nx.NetworkXNoPath:
                        pass
                max_depth = max(depths) if depths else 0
        except Exception as e:
            logger.warning(f"Error calculating depth: {e}")
            max_depth = -1

        return {
            "variable": variable,
            "exists": True,
            "is_base": self._nodes[variable].is_base,
            "direct_dependents": direct_dependents,
            "direct_dependent_count": len(direct_dependents),
            "all_affected_variables": all_affected,
            "total_affected_count": len(all_affected),
            "max_propagation_depth": max_depth,
            "category": self._nodes[variable].category
        }

    def get_base_variables(self) -> List[str]:
        """
        Get all base variables (variables with no dependencies).

        Returns:
            List of base variable names
        """
        return [name for name, node in self._nodes.items() if node.is_base]

    def get_composite_variables(self) -> List[str]:
        """
        Get all composite variables (variables with dependencies).

        Returns:
            List of composite variable names
        """
        return [name for name, node in self._nodes.items() if not node.is_base]

    def get_variable_depth(self, variable: str) -> int:
        """
        Get the depth of a variable in the dependency graph.

        Depth is the longest path from any base variable to this variable.

        Args:
            variable: Variable name

        Returns:
            Depth (0 for base variables, -1 if not found)
        """
        if variable not in self._nodes:
            return -1

        if self._nodes[variable].is_base:
            return 0

        # Get all dependencies
        deps = self.get_dependencies(variable, recursive=True)
        base_deps = [d for d in deps if self._nodes[d].is_base]

        if not base_deps:
            return 0

        # Calculate longest path from any base variable
        max_depth = 0
        for base_var in base_deps:
            try:
                path_length = nx.shortest_path_length(self._graph, base_var, variable)
                max_depth = max(max_depth, path_length)
            except nx.NetworkXNoPath:
                pass

        return max_depth

    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export graph to dictionary format.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "variables": {
                name: {
                    "name": node.name,
                    "category": node.category,
                    "is_base": node.is_base,
                    "dependencies": node.dependencies,
                    "dependents": node.dependents,
                    "metadata": node.metadata,
                    "depth": self.get_variable_depth(name)
                }
                for name, node in self._nodes.items()
            },
            "total_variables": len(self._nodes),
            "base_variables": len(self.get_base_variables()),
            "composite_variables": len(self.get_composite_variables()),
            "total_edges": self._graph.number_of_edges()
        }

    def visualize(
        self,
        output_file: Optional[str] = None,
        format: str = "png",
        show_labels: bool = True
    ) -> Optional[str]:
        """
        Visualize the dependency graph.

        Args:
            output_file: Path to save visualization (if None, returns DOT string)
            format: Output format ("png", "pdf", "svg", "dot")
            show_labels: Whether to show variable names

        Returns:
            DOT string if output_file is None, otherwise None
        """
        try:
            import matplotlib.pyplot as plt

            # Create figure
            plt.figure(figsize=(12, 8))

            # Calculate layout
            try:
                # Try hierarchical layout for DAG
                pos = nx.nx_agraph.graphviz_layout(self._graph, prog='dot')
            except:
                # Fall back to spring layout
                pos = nx.spring_layout(self._graph, k=1, iterations=50)

            # Color nodes by type
            node_colors = []
            for node_name in self._graph.nodes():
                node = self._nodes[node_name]
                if node.is_base:
                    node_colors.append('lightblue')
                else:
                    node_colors.append('lightcoral')

            # Draw graph
            nx.draw(
                self._graph,
                pos,
                with_labels=show_labels,
                node_color=node_colors,
                node_size=1500,
                font_size=8,
                font_weight='bold',
                arrows=True,
                arrowsize=15,
                edge_color='gray',
                alpha=0.7
            )

            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='lightblue', label='Base Variables'),
                Patch(facecolor='lightcoral', label='Composite Variables')
            ]
            plt.legend(handles=legend_elements, loc='upper right')

            plt.title("Variable Dependency Graph", fontsize=14, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()

            if output_file:
                plt.savefig(output_file, format=format, dpi=300, bbox_inches='tight')
                logger.info(f"Graph visualization saved to {output_file}")
                plt.close()
                return None
            else:
                plt.show()
                return None

        except ImportError:
            logger.warning("matplotlib not available, generating DOT format")

            # Generate DOT format as fallback
            dot_string = "digraph DependencyGraph {\n"
            dot_string += "  rankdir=TB;\n"
            dot_string += "  node [shape=box];\n\n"

            # Add nodes
            for name, node in self._nodes.items():
                color = "lightblue" if node.is_base else "lightcoral"
                dot_string += f'  "{name}" [style=filled, fillcolor={color}];\n'

            # Add edges
            dot_string += "\n"
            for edge in self._graph.edges():
                dot_string += f'  "{edge[0]}" -> "{edge[1]}";\n'

            dot_string += "}\n"

            if output_file:
                Path(output_file).write_text(dot_string)
                logger.info(f"DOT format saved to {output_file}")
                return None
            else:
                return dot_string

    def __len__(self) -> int:
        """Return the number of variables in the graph."""
        return len(self._nodes)

    def __contains__(self, variable: str) -> bool:
        """Check if a variable exists in the graph."""
        return variable in self._nodes

    def __repr__(self) -> str:
        """String representation of the graph."""
        return (
            f"CompositeVariableDependencyGraph("
            f"variables={len(self._nodes)}, "
            f"base={len(self.get_base_variables())}, "
            f"composite={len(self.get_composite_variables())})"
        )


# Convenience function
def create_dependency_graph_from_registry(
    registry: Any,
    filter_category: Optional[str] = None
) -> CompositeVariableDependencyGraph:
    """
    Create a dependency graph from a FinancialVariableRegistry.

    Args:
        registry: FinancialVariableRegistry instance
        filter_category: Optional category filter

    Returns:
        Populated CompositeVariableDependencyGraph
    """
    graph = CompositeVariableDependencyGraph()

    # Get all variables from registry
    variable_names = registry.list_all_variables()

    for var_name in variable_names:
        var_def = registry.get_variable_definition(var_name)

        if var_def is None:
            continue

        # Apply category filter if specified
        if filter_category and var_def.category.value != filter_category:
            continue

        # Add to graph
        graph.add_variable(
            name=var_def.name,
            category=var_def.category.value,
            depends_on=var_def.depends_on,
            metadata={
                "data_type": var_def.data_type.value,
                "units": var_def.units.value,
                "description": var_def.description,
                "required": var_def.required
            }
        )

    logger.info(f"Created dependency graph with {len(graph)} variables from registry")
    return graph
