"""
Composite Variable Calculator Engine
====================================

High-performance calculation engine that computes composite financial variables in the
correct dependency order, with automatic recalculation when base variables change and
incremental update support.

This module implements:
- Dependency-aware calculation ordering using topological sort
- Incremental updates (only recalculate affected variables)
- Caching for expensive calculations
- Parallel processing for independent variable groups
- Rollback functionality for failed calculations
- Comprehensive logging and debugging
- Support for custom calculation functions and lambda expressions

Usage Example
-------------
>>> from composite_variable_calculator import CompositeVariableCalculator
>>> from composite_variable_dependency_graph import CompositeVariableDependencyGraph
>>>
>>> # Create calculator with dependency graph
>>> graph = CompositeVariableDependencyGraph()
>>> graph.add_variable("revenue")
>>> graph.add_variable("net_income")
>>> graph.add_variable("profit_margin", depends_on=["net_income", "revenue"])
>>>
>>> calculator = CompositeVariableCalculator(graph)
>>>
>>> # Register calculation function
>>> calculator.register_calculation(
...     "profit_margin",
...     lambda data: data["net_income"] / data["revenue"] if data["revenue"] != 0 else 0
... )
>>>
>>> # Provide base data and calculate
>>> base_data = {"revenue": 1000000, "net_income": 150000}
>>> results = calculator.calculate_all(base_data)
>>> print(results["profit_margin"])  # 0.15
>>>
>>> # Update base data and recalculate only affected variables
>>> updated_data = {"net_income": 200000}
>>> results = calculator.update_and_recalculate(updated_data, results)
>>> print(results["profit_margin"])  # 0.20
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import traceback

from .composite_variable_dependency_graph import CompositeVariableDependencyGraph

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CalculationResult:
    """
    Represents the result of a variable calculation.

    Attributes:
        variable: Variable name
        value: Calculated value
        success: Whether calculation succeeded
        error: Error message if failed
        execution_time_ms: Time taken to calculate in milliseconds
        dependencies_used: List of dependencies that were used
        calculated_at: Timestamp of calculation
    """
    variable: str
    value: Any = None
    success: bool = True
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    dependencies_used: List[str] = field(default_factory=list)
    calculated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CalculationContext:
    """
    Context for a calculation session.

    Attributes:
        base_data: Base variable values
        calculated_data: Calculated variable values
        calculation_results: Detailed results for each calculation
        errors: List of errors encountered
        start_time: When calculation started
        end_time: When calculation completed
    """
    base_data: Dict[str, Any]
    calculated_data: Dict[str, Any] = field(default_factory=dict)
    calculation_results: Dict[str, CalculationResult] = field(default_factory=dict)
    errors: List[Tuple[str, str]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    def get_value(self, variable: str) -> Any:
        """Get value from either base data or calculated data."""
        if variable in self.calculated_data:
            return self.calculated_data[variable]
        return self.base_data.get(variable)

    def has_value(self, variable: str) -> bool:
        """Check if variable has a value."""
        return variable in self.base_data or variable in self.calculated_data

    def set_calculated(self, variable: str, value: Any, result: CalculationResult):
        """Set a calculated value."""
        self.calculated_data[variable] = value
        self.calculation_results[variable] = result

    def add_error(self, variable: str, error: str):
        """Add an error."""
        self.errors.append((variable, error))

    def merge_results(self) -> Dict[str, Any]:
        """Merge base and calculated data."""
        return {**self.base_data, **self.calculated_data}


class CompositeVariableCalculator:
    """
    High-performance calculation engine for composite financial variables.

    This class uses a CompositeVariableDependencyGraph to determine calculation order
    and supports:
    - Automatic ordering based on dependencies
    - Incremental updates
    - Caching
    - Parallel processing
    - Rollback on errors
    - Custom calculation functions
    """

    def __init__(
        self,
        dependency_graph: CompositeVariableDependencyGraph,
        enable_caching: bool = True,
        enable_parallel: bool = True,
        max_workers: Optional[int] = None
    ):
        """
        Initialize the calculator.

        Args:
            dependency_graph: Dependency graph for variable relationships
            enable_caching: Enable caching of calculation results
            enable_parallel: Enable parallel processing for independent variables
            max_workers: Maximum number of parallel workers (None = auto)
        """
        self._graph = dependency_graph
        self._enable_caching = enable_caching
        self._enable_parallel = enable_parallel
        self._max_workers = max_workers

        # Calculation functions registry
        self._calculation_functions: Dict[str, Callable] = {}

        # Cache for calculated values
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        # Statistics
        self._stats = {
            "total_calculations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "parallel_batches": 0
        }

        logger.info(
            f"CompositeVariableCalculator initialized with {len(dependency_graph)} variables "
            f"(caching={enable_caching}, parallel={enable_parallel})"
        )

    def register_calculation(
        self,
        variable: str,
        calculation_func: Callable[[Dict[str, Any]], Any]
    ) -> bool:
        """
        Register a calculation function for a variable.

        The function should accept a dictionary of all available data and return
        the calculated value.

        Args:
            variable: Variable name
            calculation_func: Function that calculates the variable value

        Returns:
            True if registered successfully
        """
        if variable not in self._graph:
            logger.error(f"Variable {variable} not in dependency graph")
            return False

        self._calculation_functions[variable] = calculation_func
        logger.info(f"Registered calculation function for {variable}")
        return True

    def register_calculations(self, calculations: Dict[str, Callable]) -> int:
        """
        Register multiple calculation functions at once.

        Args:
            calculations: Dictionary mapping variable names to calculation functions

        Returns:
            Number of successfully registered functions
        """
        count = 0
        for variable, func in calculations.items():
            if self.register_calculation(variable, func):
                count += 1
        return count

    def clear_cache(self, variables: Optional[List[str]] = None):
        """
        Clear the calculation cache.

        Args:
            variables: Specific variables to clear, or None for all
        """
        if variables is None:
            self._cache.clear()
            self._cache_timestamps.clear()
            logger.info("Cleared all cache")
        else:
            for var in variables:
                self._cache.pop(var, None)
                self._cache_timestamps.pop(var, None)
            logger.info(f"Cleared cache for {len(variables)} variables")

    def _get_cache_key(self, variable: str, context: CalculationContext) -> str:
        """Generate cache key for a variable calculation."""
        # Use variable name and hash of dependencies
        deps = self._graph.get_dependencies(variable, recursive=False)
        dep_values = tuple(sorted((d, context.get_value(d)) for d in deps))
        return f"{variable}:{hash(dep_values)}"

    def _calculate_single_variable(
        self,
        variable: str,
        context: CalculationContext
    ) -> CalculationResult:
        """
        Calculate a single variable.

        Args:
            variable: Variable to calculate
            context: Calculation context with all data

        Returns:
            CalculationResult with success/error info
        """
        start_time = datetime.now()

        try:
            # Check if we have a calculation function
            if variable not in self._calculation_functions:
                # Check if it's a base variable (already in context)
                if context.has_value(variable):
                    value = context.get_value(variable)
                    result = CalculationResult(
                        variable=variable,
                        value=value,
                        success=True,
                        execution_time_ms=0.0,
                        dependencies_used=[]
                    )
                    self._stats["total_calculations"] += 1
                    return result
                else:
                    error_msg = f"No calculation function registered for {variable}"
                    logger.error(error_msg)
                    self._stats["errors"] += 1
                    return CalculationResult(
                        variable=variable,
                        success=False,
                        error=error_msg
                    )

            # Check cache
            if self._enable_caching:
                cache_key = self._get_cache_key(variable, context)
                if cache_key in self._cache:
                    self._stats["cache_hits"] += 1
                    value = self._cache[cache_key]
                    logger.debug(f"Cache hit for {variable}")
                    return CalculationResult(
                        variable=variable,
                        value=value,
                        success=True,
                        execution_time_ms=0.0,
                        dependencies_used=self._graph.get_dependencies(variable, recursive=False)
                    )
                self._stats["cache_misses"] += 1

            # Get dependencies
            dependencies = self._graph.get_dependencies(variable, recursive=False)

            # Verify all dependencies are available
            missing_deps = [d for d in dependencies if not context.has_value(d)]
            if missing_deps:
                error_msg = f"Missing dependencies for {variable}: {missing_deps}"
                logger.error(error_msg)
                self._stats["errors"] += 1
                return CalculationResult(
                    variable=variable,
                    success=False,
                    error=error_msg
                )

            # Prepare data for calculation
            all_data = context.merge_results()

            # Execute calculation
            calc_func = self._calculation_functions[variable]
            value = calc_func(all_data)

            # Calculate execution time
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            # Cache result
            if self._enable_caching:
                cache_key = self._get_cache_key(variable, context)
                self._cache[cache_key] = value
                self._cache_timestamps[cache_key] = datetime.now()

            # Update stats
            self._stats["total_calculations"] += 1

            logger.debug(
                f"Calculated {variable} = {value} in {execution_time_ms:.2f}ms"
            )

            return CalculationResult(
                variable=variable,
                value=value,
                success=True,
                execution_time_ms=execution_time_ms,
                dependencies_used=dependencies
            )

        except Exception as e:
            error_msg = f"Error calculating {variable}: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            self._stats["errors"] += 1

            return CalculationResult(
                variable=variable,
                success=False,
                error=error_msg,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    def _calculate_batch_parallel(
        self,
        variables: List[str],
        context: CalculationContext
    ) -> List[CalculationResult]:
        """
        Calculate a batch of independent variables in parallel.

        Args:
            variables: List of variables to calculate
            context: Calculation context

        Returns:
            List of calculation results
        """
        results = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit all calculations
            futures = {
                executor.submit(self._calculate_single_variable, var, context): var
                for var in variables
            }

            # Collect results as they complete
            for future in as_completed(futures):
                variable = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Parallel calculation failed for {variable}: {e}")
                    results.append(CalculationResult(
                        variable=variable,
                        success=False,
                        error=str(e)
                    ))

        self._stats["parallel_batches"] += 1
        return results

    def calculate_variable(
        self,
        variable: str,
        base_data: Dict[str, Any],
        existing_results: Optional[Dict[str, Any]] = None
    ) -> Tuple[Any, CalculationResult]:
        """
        Calculate a specific variable and all its dependencies.

        Args:
            variable: Variable to calculate
            base_data: Base variable values
            existing_results: Existing calculated values to reuse

        Returns:
            Tuple of (calculated_value, calculation_result)
        """
        if variable not in self._graph:
            raise ValueError(f"Variable {variable} not in dependency graph")

        # Create context
        context = CalculationContext(
            base_data=base_data.copy(),
            calculated_data=existing_results.copy() if existing_results else {}
        )

        # Get all dependencies (including transitive)
        all_deps = self._graph.get_dependencies(variable, recursive=True)

        # Get calculation order for dependencies + this variable
        try:
            full_order = self._graph.get_calculation_order()
            # Filter to only dependencies and the target variable
            calc_order = [v for v in full_order if v in all_deps or v == variable]
        except ValueError as e:
            raise ValueError(f"Cannot calculate {variable}: {e}")

        # Calculate in order
        for var in calc_order:
            # Skip if already calculated
            if context.has_value(var) and var != variable:
                continue

            result = self._calculate_single_variable(var, context)

            if not result.success:
                raise ValueError(f"Failed to calculate {var}: {result.error}")

            context.set_calculated(var, result.value, result)

        # Return the requested variable
        final_result = context.calculation_results.get(variable)
        if not final_result:
            raise ValueError(f"Variable {variable} was not calculated")

        return final_result.value, final_result

    def calculate_all(
        self,
        base_data: Dict[str, Any],
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate all composite variables or a specific subset.

        Args:
            base_data: Base variable values
            variables: Specific variables to calculate (None = all composite variables)

        Returns:
            Dictionary with all variable values (base + calculated)

        Raises:
            ValueError: If calculation fails
        """
        logger.info(f"Starting calculate_all with {len(base_data)} base variables")

        # Create context
        context = CalculationContext(base_data=base_data.copy())

        # Determine what to calculate
        if variables is None:
            # Calculate all composite variables
            variables_to_calc = self._graph.get_composite_variables()
        else:
            # Calculate only specified variables
            variables_to_calc = variables

        # Get calculation order
        try:
            full_order = self._graph.get_calculation_order()
            # Filter to only variables we want to calculate
            calc_order = [v for v in full_order if v in variables_to_calc]
        except ValueError as e:
            raise ValueError(f"Cannot determine calculation order: {e}")

        logger.info(f"Calculation order determined: {len(calc_order)} variables")

        # Group variables by depth for parallel processing
        if self._enable_parallel and len(calc_order) > 1:
            depth_groups = self._group_by_depth(calc_order)
            logger.info(f"Grouped into {len(depth_groups)} parallel batches")

            for depth, batch_vars in sorted(depth_groups.items()):
                logger.debug(f"Processing depth {depth}: {len(batch_vars)} variables")

                if len(batch_vars) == 1:
                    # Single variable - calculate directly
                    var = batch_vars[0]
                    result = self._calculate_single_variable(var, context)
                    if result.success:
                        context.set_calculated(var, result.value, result)
                    else:
                        context.add_error(var, result.error)
                else:
                    # Multiple independent variables - calculate in parallel
                    results = self._calculate_batch_parallel(batch_vars, context)
                    for result in results:
                        if result.success:
                            context.set_calculated(result.variable, result.value, result)
                        else:
                            context.add_error(result.variable, result.error)
        else:
            # Sequential calculation
            for var in calc_order:
                # Skip if already in context (base variable or already calculated)
                if context.has_value(var):
                    continue

                result = self._calculate_single_variable(var, context)
                if result.success:
                    context.set_calculated(var, result.value, result)
                else:
                    context.add_error(var, result.error)

        # Check for errors
        if context.errors:
            error_summary = "\n".join([f"{var}: {err}" for var, err in context.errors])
            raise ValueError(f"Calculation errors:\n{error_summary}")

        context.end_time = datetime.now()
        total_time = (context.end_time - context.start_time).total_seconds()
        logger.info(
            f"Calculation complete: {len(context.calculated_data)} variables "
            f"calculated in {total_time:.2f}s"
        )

        return context.merge_results()

    def update_and_recalculate(
        self,
        updated_data: Dict[str, Any],
        current_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update base data and recalculate only affected variables.

        This is more efficient than recalculating everything when only a few
        base variables change.

        Args:
            updated_data: Dictionary of updated variable values
            current_results: Current calculation results

        Returns:
            Updated results with recalculated values
        """
        logger.info(f"Incremental update for {len(updated_data)} changed variables")

        # Determine which variables are affected
        affected_vars = set()
        for changed_var in updated_data.keys():
            if changed_var in self._graph:
                # Get all dependents (variables that depend on this one)
                dependents = self._graph.get_dependents(changed_var, recursive=True)
                affected_vars.update(dependents)

        logger.info(f"Found {len(affected_vars)} affected variables")

        # Clear cache for affected variables
        if self._enable_caching:
            self.clear_cache(list(affected_vars))

        # Start with current results
        merged_results = current_results.copy()

        # Apply updates
        merged_results.update(updated_data)

        # Recalculate only affected variables
        if affected_vars:
            # Separate base variables from calculated variables in merged_results
            base_vars = self._graph.get_base_variables()
            base_data = {k: v for k, v in merged_results.items() if k in base_vars}

            # Create context with base data and existing calculated values
            context = CalculationContext(base_data=base_data)

            # Add non-affected calculated values to context
            for var in self._graph.get_composite_variables():
                if var not in affected_vars and var in merged_results:
                    context.calculated_data[var] = merged_results[var]

            # Get calculation order for affected variables only
            full_order = self._graph.get_calculation_order()
            calc_order = [v for v in full_order if v in affected_vars]

            # Calculate affected variables
            for var in calc_order:
                result = self._calculate_single_variable(var, context)
                if result.success:
                    context.set_calculated(var, result.value, result)
                else:
                    context.add_error(var, result.error)

            # Check for errors
            if context.errors:
                error_summary = "\n".join([f"{var}: {err}" for var, err in context.errors])
                raise ValueError(f"Calculation errors:\n{error_summary}")

            # Return merged results
            return context.merge_results()
        else:
            return merged_results

    def update_dependencies(self):
        """
        Update the calculator when the dependency graph changes.

        Call this after adding/removing variables or dependencies in the graph.
        """
        # Clear cache since dependencies may have changed
        self.clear_cache()

        # Validate graph
        is_valid, errors = self._graph.validate_dependencies()
        if not is_valid:
            error_msg = "Dependency graph validation failed:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Dependencies updated successfully")

    def _group_by_depth(self, variables: List[str]) -> Dict[int, List[str]]:
        """
        Group variables by their depth in the dependency graph.

        Variables at the same depth can be calculated in parallel.

        Args:
            variables: List of variables to group

        Returns:
            Dictionary mapping depth -> list of variables at that depth
        """
        depth_groups: Dict[int, List[str]] = {}

        for var in variables:
            depth = self._graph.get_variable_depth(var)
            if depth not in depth_groups:
                depth_groups[depth] = []
            depth_groups[depth].append(var)

        return depth_groups

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get calculation statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            **self._stats,
            "cache_size": len(self._cache),
            "registered_functions": len(self._calculation_functions),
            "cache_hit_rate": (
                self._stats["cache_hits"] / max(1, self._stats["cache_hits"] + self._stats["cache_misses"])
            )
        }

    def reset_statistics(self):
        """Reset calculation statistics."""
        self._stats = {
            "total_calculations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "parallel_batches": 0
        }
        logger.info("Statistics reset")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CompositeVariableCalculator("
            f"variables={len(self._graph)}, "
            f"functions={len(self._calculation_functions)}, "
            f"cache_size={len(self._cache)})"
        )
