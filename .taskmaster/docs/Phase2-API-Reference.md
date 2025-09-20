# Phase 2 Advanced Features - API Reference

## Overview

This document provides a complete API reference for all Phase 2 advanced features in the Financial Analysis Toolkit. The APIs are organized by functional area and include detailed parameter descriptions, return values, and usage examples.

## Table of Contents

1. [Monte Carlo Simulation API](#monte-carlo-simulation-api)
2. [Collaboration System API](#collaboration-system-api)
3. [Advanced UI Components API](#advanced-ui-components-api)
4. [Statistical Analysis API](#statistical-analysis-api)
5. [User Preferences API](#user-preferences-api)
6. [Data Structures](#data-structures)

---

## Monte Carlo Simulation API

### MonteCarloEngine Class

Main class for Monte Carlo simulations with financial data integration.

#### Constructor

```python
MonteCarloEngine(financial_calculator: Optional[FinancialCalculator] = None)
```

**Parameters:**
- `financial_calculator` (FinancialCalculator, optional): FinancialCalculator instance for data access

**Example:**
```python
from core.analysis.statistics.monte_carlo_engine import MonteCarloEngine
from core.analysis.engines.financial_calculations import FinancialCalculator

calc = FinancialCalculator('AAPL')
monte_carlo = MonteCarloEngine(calc)
```

#### Methods

##### simulate_dcf_valuation()

Run Monte Carlo simulation for DCF valuation.

```python
simulate_dcf_valuation(
    num_simulations: int = 10000,
    revenue_growth_volatility: float = 0.15,
    discount_rate_volatility: float = 0.02,
    terminal_growth_volatility: float = 0.01,
    margin_volatility: float = 0.05,
    custom_distributions: Optional[Dict[str, ParameterDistribution]] = None,
    random_state: Optional[int] = None
) -> SimulationResult
```

**Parameters:**
- `num_simulations` (int): Number of simulation runs (default: 10000)
- `revenue_growth_volatility` (float): Standard deviation of revenue growth rate (default: 0.15)
- `discount_rate_volatility` (float): Standard deviation of discount rate (default: 0.02)
- `terminal_growth_volatility` (float): Standard deviation of terminal growth rate (default: 0.01)
- `margin_volatility` (float): Standard deviation of profit margins (default: 0.05)
- `custom_distributions` (Dict[str, ParameterDistribution], optional): Custom parameter distributions
- `random_state` (int, optional): Random seed for reproducibility

**Returns:**
- `SimulationResult`: Container with simulation output and statistics

**Example:**
```python
result = monte_carlo.simulate_dcf_valuation(
    num_simulations=10000,
    revenue_growth_volatility=0.15,
    discount_rate_volatility=0.02
)

print(f"Expected Value: ${result.mean_value:.2f}")
print(f"95% Confidence Interval: {result.ci_95}")
print(f"Value at Risk (5%): ${result.var_5:.2f}")
```

##### simulate_dividend_discount_model()

Run Monte Carlo simulation for Dividend Discount Model valuation.

```python
simulate_dividend_discount_model(
    num_simulations: int = 10000,
    dividend_growth_volatility: float = 0.20,
    required_return_volatility: float = 0.02,
    payout_ratio_volatility: float = 0.10,
    random_state: Optional[int] = None
) -> SimulationResult
```

**Parameters:**
- `num_simulations` (int): Number of simulation runs
- `dividend_growth_volatility` (float): Standard deviation of dividend growth rate
- `required_return_volatility` (float): Standard deviation of required return
- `payout_ratio_volatility` (float): Standard deviation of payout ratio
- `random_state` (int, optional): Random seed for reproducibility

**Returns:**
- `SimulationResult`: Container with simulation output and statistics

##### run_scenario_analysis()

Run scenario analysis with predefined parameter sets.

```python
run_scenario_analysis(
    scenarios: Dict[str, Dict[str, float]],
    base_valuation_method: str = 'dcf'
) -> Dict[str, float]
```

**Parameters:**
- `scenarios` (Dict[str, Dict[str, float]]): Dictionary of scenario names to parameter dictionaries
- `base_valuation_method` (str): Base valuation method ('dcf' or 'ddm')

**Returns:**
- `Dict[str, float]`: Dictionary mapping scenario names to calculated values

**Example:**
```python
scenarios = {
    'Base Case': {
        'revenue_growth': 0.05,
        'discount_rate': 0.10,
        'terminal_growth': 0.03,
        'operating_margin': 0.20
    },
    'Optimistic': {
        'revenue_growth': 0.15,
        'discount_rate': 0.08,
        'terminal_growth': 0.04,
        'operating_margin': 0.25
    }
}

results = monte_carlo.run_scenario_analysis(scenarios, 'dcf')
```

##### calculate_portfolio_var()

Calculate portfolio Value at Risk using Monte Carlo results.

```python
calculate_portfolio_var(
    portfolio_weights: Dict[str, float],
    individual_simulations: Dict[str, SimulationResult],
    confidence_level: float = 0.05
) -> Dict[str, float]
```

**Parameters:**
- `portfolio_weights` (Dict[str, float]): Dictionary mapping asset names to portfolio weights
- `individual_simulations` (Dict[str, SimulationResult]): Dictionary mapping asset names to simulation results
- `confidence_level` (float): Confidence level for VaR calculation (default: 0.05)

**Returns:**
- `Dict[str, float]`: Dictionary containing portfolio VaR metrics

### ParameterDistribution Class

Statistical distribution definition for Monte Carlo parameters.

#### Constructor

```python
ParameterDistribution(
    distribution: DistributionType,
    params: Dict[str, float],
    name: str,
    correlation_group: Optional[str] = None
)
```

**Parameters:**
- `distribution` (DistributionType): Type of statistical distribution
- `params` (Dict[str, float]): Distribution parameters (mean, std, min, max, etc.)
- `name` (str): Human-readable parameter name
- `correlation_group` (str, optional): Group ID for correlated parameters

#### Methods

##### sample()

Generate random samples from the distribution.

```python
sample(size: int, random_state: Optional[int] = None) -> np.ndarray
```

**Parameters:**
- `size` (int): Number of samples to generate
- `random_state` (int, optional): Random seed for reproducibility

**Returns:**
- `np.ndarray`: Array of random samples

### SimulationResult Class

Container for Monte Carlo simulation results and statistical analysis.

#### Properties

- `values` (np.ndarray): Array of simulated values
- `statistics` (Dict[str, float]): Descriptive statistics
- `risk_metrics` (RiskMetrics): Risk assessment metrics
- `percentiles` (Dict[str, float]): Key percentile values
- `mean_value` (float): Mean simulated value
- `median_value` (float): Median simulated value
- `ci_95` (Tuple[float, float]): 95% confidence interval
- `var_5` (float): 5% Value at Risk

#### Methods

##### summary_table()

Generate a summary table of key statistics.

```python
summary_table() -> pd.DataFrame
```

**Returns:**
- `pd.DataFrame`: Summary table with key metrics

---

## Collaboration System API

### CollaborationManager Class

Central manager for all collaboration features.

#### Constructor

```python
CollaborationManager(storage_path: Optional[Path] = None)
```

**Parameters:**
- `storage_path` (Path, optional): Path for collaboration data storage

#### Methods

##### create_analysis_share()

Create a comprehensive analysis share.

```python
create_analysis_share(
    analysis_data: Dict[str, Any],
    user_profile: UserProfile,
    title: str,
    description: str = "",
    analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE,
    is_public: bool = False,
    expires_in_days: Optional[int] = None,
    password: Optional[str] = None,
    allow_comments: bool = True,
    allow_downloads: bool = True
) -> SharedAnalysis
```

**Parameters:**
- `analysis_data` (Dict[str, Any]): Analysis data to share
- `user_profile` (UserProfile): User creating the share
- `title` (str): Share title
- `description` (str): Share description
- `analysis_type` (AnalysisType): Type of analysis
- `is_public` (bool): Whether share is publicly accessible
- `expires_in_days` (int, optional): Expiration in days
- `password` (str, optional): Password protection
- `allow_comments` (bool): Whether comments are allowed
- `allow_downloads` (bool): Whether downloads are allowed

**Returns:**
- `SharedAnalysis`: Created shared analysis object

##### access_shared_analysis()

Access a shared analysis with full collaboration context.

```python
access_shared_analysis(
    share_id: str,
    user_profile: Optional[UserProfile] = None,
    password: Optional[str] = None
) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `share_id` (str): ID of the share to access
- `user_profile` (UserProfile, optional): User accessing the share
- `password` (str, optional): Password if required

**Returns:**
- `Dict[str, Any]`: Collaboration context or None if access denied

##### add_annotation()

Add an annotation to an analysis.

```python
add_annotation(
    analysis_id: str,
    user_profile: UserProfile,
    annotation_type: AnnotationType,
    title: str,
    content: str,
    target_scope: AnnotationScope,
    target_id: Optional[str] = None,
    coordinates: Optional[Dict[str, float]] = None,
    share_id: Optional[str] = None,
    is_private: bool = False,
    tags: Optional[List[str]] = None
) -> AnalysisAnnotation
```

**Parameters:**
- `analysis_id` (str): ID of the analysis to annotate
- `user_profile` (UserProfile): User creating the annotation
- `annotation_type` (AnnotationType): Type of annotation
- `title` (str): Annotation title
- `content` (str): Annotation content
- `target_scope` (AnnotationScope): Target scope within analysis
- `target_id` (str, optional): Specific target ID
- `coordinates` (Dict[str, float], optional): Positioning coordinates
- `share_id` (str, optional): Associated share ID
- `is_private` (bool): Whether annotation is private
- `tags` (List[str], optional): Tags for organization

**Returns:**
- `AnalysisAnnotation`: Created annotation object

##### create_workspace()

Create a new collaborative workspace.

```python
create_workspace(
    name: str,
    description: str,
    workspace_type: WorkspaceType,
    user_profile: UserProfile,
    is_public: bool = False
) -> SharedWorkspace
```

**Parameters:**
- `name` (str): Workspace name
- `description` (str): Workspace description
- `workspace_type` (WorkspaceType): Type of workspace
- `user_profile` (UserProfile): Workspace creator
- `is_public` (bool): Whether workspace is publicly accessible

**Returns:**
- `SharedWorkspace`: Created workspace object

##### search_shared_analyses()

Search shared analyses by content.

```python
search_shared_analyses(
    query: str,
    user_profile: Optional[UserProfile] = None,
    analysis_type: Optional[AnalysisType] = None
) -> List[SharedAnalysis]
```

**Parameters:**
- `query` (str): Search query
- `user_profile` (UserProfile, optional): User performing search
- `analysis_type` (AnalysisType, optional): Filter by analysis type

**Returns:**
- `List[SharedAnalysis]`: List of matching shared analyses

---

## Advanced UI Components API

### AdvancedComponent Class

Base class for all advanced UI components with reactive state management.

#### Constructor

```python
AdvancedComponent(config: ComponentConfig)
```

**Parameters:**
- `config` (ComponentConfig): Component configuration

#### Methods

##### render()

Enhanced render method with lifecycle management.

```python
render(data: Any = None, **kwargs) -> Any
```

**Parameters:**
- `data` (Any, optional): Data to render
- `**kwargs`: Additional rendering parameters

**Returns:**
- `Any`: Rendered component result

##### add_event_handler()

Register an event handler for the component.

```python
add_event_handler(event: InteractionEvent, handler: EventHandler) -> None
```

**Parameters:**
- `event` (InteractionEvent): Event type to handle
- `handler` (EventHandler): Handler function

##### emit_event()

Emit an event to registered handlers.

```python
emit_event(event: InteractionEvent, data: Any = None) -> None
```

**Parameters:**
- `event` (InteractionEvent): Event type to emit
- `data` (Any, optional): Event data

##### Abstract Methods

These methods must be implemented by subclasses:

```python
def render_content(self, data: Any = None, **kwargs) -> Any:
    """Render the actual component content"""
    pass
```

### ComponentConfig Class

Configuration for advanced components.

#### Constructor

```python
ComponentConfig(
    id: str,
    title: str,
    description: str = "",
    cache_enabled: bool = True,
    auto_refresh: bool = False,
    refresh_interval: int = 30,
    animation_enabled: bool = True,
    loading_placeholder: str = "Loading...",
    error_fallback: str = "Unable to load component",
    responsive: bool = True,
    theme: str = "default",
    permissions: List[str] = []
)
```

**Parameters:**
- `id` (str): Unique component identifier
- `title` (str): Component title
- `description` (str): Component description
- `cache_enabled` (bool): Enable caching
- `auto_refresh` (bool): Enable automatic refresh
- `refresh_interval` (int): Refresh interval in seconds
- `animation_enabled` (bool): Enable animations
- `loading_placeholder` (str): Loading message
- `error_fallback` (str): Error fallback message
- `responsive` (bool): Enable responsive design
- `theme` (str): UI theme
- `permissions` (List[str]): Required permissions

---

## Statistical Analysis API

### PBStatisticalAnalysis Class

Advanced P/B ratio analysis with historical context and industry benchmarking.

#### Constructor

```python
PBStatisticalAnalysis(financial_calculator: FinancialCalculator)
```

**Parameters:**
- `financial_calculator` (FinancialCalculator): Financial calculator instance

#### Methods

##### calculate_industry_pb_statistics()

Calculate industry P/B statistics and percentiles.

```python
calculate_industry_pb_statistics(
    industry_data: pd.DataFrame,
    current_pb: float
) -> Dict[str, Any]
```

**Parameters:**
- `industry_data` (pd.DataFrame): Industry P/B ratio data
- `current_pb` (float): Current P/B ratio to analyze

**Returns:**
- `Dict[str, Any]`: Industry statistics and positioning

##### historical_pb_analysis()

Analyze historical P/B trends and patterns.

```python
historical_pb_analysis(
    historical_data: pd.DataFrame,
    lookback_years: int = 5
) -> Dict[str, Any]
```

**Parameters:**
- `historical_data` (pd.DataFrame): Historical financial data
- `lookback_years` (int): Years to look back for analysis

**Returns:**
- `Dict[str, Any]`: Historical analysis results

---

## User Preferences API

### UserProfile Class

User identity and preferences management.

#### Constructor

```python
UserProfile(
    user_id: str,
    username: str,
    email: Optional[str] = None,
    role: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `user_id` (str): Unique user identifier
- `username` (str): Display username
- `email` (str, optional): User email address
- `role` (str, optional): User role
- `preferences` (Dict[str, Any], optional): User preferences

### PreferenceManager Class

Manages user preferences and settings.

#### Constructor

```python
PreferenceManager(user_id: str, storage_path: Optional[Path] = None)
```

**Parameters:**
- `user_id` (str): User identifier
- `storage_path` (Path, optional): Storage location for preferences

#### Methods

##### get_preference()

Get a specific user preference.

```python
get_preference(key: str, default: Any = None) -> Any
```

**Parameters:**
- `key` (str): Preference key
- `default` (Any): Default value if key not found

**Returns:**
- `Any`: Preference value or default

##### set_preference()

Set a user preference.

```python
set_preference(key: str, value: Any) -> None
```

**Parameters:**
- `key` (str): Preference key
- `value` (Any): Preference value

---

## Data Structures

### Enums

#### DistributionType
```python
class DistributionType(Enum):
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    BETA = "beta"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"
    GAMMA = "gamma"
```

#### AnalysisType
```python
class AnalysisType(Enum):
    DCF = "dcf"
    DDM = "ddm"
    PB_RATIO = "pb_ratio"
    MONTE_CARLO = "monte_carlo"
    COMPARATIVE = "comparative"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"
```

#### AnnotationType
```python
class AnnotationType(Enum):
    COMMENT = "comment"
    QUESTION = "question"
    INSIGHT = "insight"
    CONCERN = "concern"
    SUGGESTION = "suggestion"
    APPROVAL = "approval"
    ISSUE = "issue"
```

#### AnnotationScope
```python
class AnnotationScope(Enum):
    GENERAL = "general"
    DCF_PROJECTIONS = "dcf_projections"
    VALUATION_PARAMETERS = "valuation_parameters"
    ASSUMPTIONS = "assumptions"
    SENSITIVITY_ANALYSIS = "sensitivity_analysis"
    MONTE_CARLO = "monte_carlo"
    PEER_COMPARISON = "peer_comparison"
    CHARTS_VISUALIZATION = "charts_visualization"
```

#### ComponentState
```python
class ComponentState(Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    LOADING = "loading"
    ERROR = "error"
    UPDATING = "updating"
```

#### InteractionEvent
```python
class InteractionEvent(Enum):
    CLICK = "click"
    HOVER = "hover"
    SELECT = "select"
    CHANGE = "change"
    SUBMIT = "submit"
    REFRESH = "refresh"
```

### Data Classes

#### RiskMetrics
```python
@dataclass
class RiskMetrics:
    var_5: float          # Value at Risk (5th percentile)
    var_1: float          # Value at Risk (1st percentile)
    cvar_5: float         # Conditional Value at Risk (5%)
    cvar_1: float         # Conditional Value at Risk (1%)
    max_drawdown: float   # Maximum potential loss
    upside_potential: float # 95th percentile value
    downside_deviation: float # Standard deviation of negative returns
    probability_of_loss: float # Probability of negative returns
```

#### ComponentMetrics
```python
@dataclass
class ComponentMetrics:
    render_time: float = 0.0
    last_render: datetime = field(default_factory=datetime.now)
    render_count: int = 0
    error_count: int = 0
    user_interactions: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
```

---

## Error Handling

### Common Exceptions

The API uses standard Python exceptions with custom messages:

- `ValueError`: Invalid parameter values or configuration
- `TypeError`: Incorrect parameter types
- `FileNotFoundError`: Missing data files or storage paths
- `PermissionError`: Insufficient permissions for collaboration features
- `ConnectionError`: Network or data source connection issues

### Example Error Handling

```python
try:
    result = monte_carlo.simulate_dcf_valuation(
        num_simulations=10000,
        revenue_growth_volatility=0.15
    )
except ValueError as e:
    print(f"Invalid simulation parameters: {e}")
except Exception as e:
    print(f"Simulation failed: {e}")
    # Fallback to deterministic analysis
```

---

## Rate Limits and Performance

### Simulation Limits

- Maximum simulations per request: 100,000
- Recommended simulation count: 10,000 for most analyses
- Memory usage: ~8 bytes per simulation per parameter

### Collaboration Limits

- Maximum share size: 100 MB
- Maximum annotations per analysis: 1,000
- Search result limit: 100 items per query

### UI Component Limits

- Maximum cached components: 1,000
- Component render timeout: 30 seconds
- Event handler limit: 50 per component

---

*This API reference covers all Phase 2 advanced features. For implementation examples and integration patterns, refer to the user guides and code examples.*