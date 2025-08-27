# Agent Coordination Protocol

## Overview
This document defines the coordination protocol for the multi-agent system deployed in the financial analysis project. It establishes communication patterns, conflict resolution, and collaborative workflows.

## Agent Hierarchy & Roles

### Lead Agent
- **Code Quality Agent** 🔧
  - Primary coordinator for Task #46
  - Decision-making authority for conflicts
  - Overall progress responsibility
  - Cross-agent communication hub

### Parallel Agents
- **Documentation Agent** 📚
  - Works simultaneously with Code Quality Agent
  - Equal priority on documentation tasks
  - Coordinated but independent execution

### Consultant Agents
- **Financial Domain Agent** 💰
  - Provides expertise on financial calculations
  - Reviews financial logic changes
  - Advisory role, not direct implementation

- **Testing & Validation Agent** 🧪
  - Final quality gate for all changes
  - Validation of agent modifications
  - Quality assurance oversight

## Communication System

### Primary Communication Hub
**Task Master System** serves as the central coordination platform:
- Real-time task status updates
- Subtask assignment and completion tracking
- Progress visibility across all agents
- Conflict logging and resolution tracking

### Communication Patterns

#### 1. Status Updates
```
Agent → Task Master → All Agents
- Subtask completion notifications
- Progress milestone updates  
- Blocker identification and reporting
- Quality gate status changes
```

#### 2. Collaboration Requests
```
Requesting Agent → Task Master → Target Agent
- Domain expertise consultation
- Code review requests
- Validation service requests
- Conflict resolution escalation
```

#### 3. Coordination Messages
```
Lead Agent → Task Master → All Agents
- Phase transition announcements
- Priority changes and updates
- Resource allocation decisions
- Overall strategy modifications
```

## Workflow Coordination

### Phase-Based Execution
**Sequential Phases with Parallel Activities:**

#### Phase 1: Import Organization & Naming
- **Lead:** Code Quality Agent (primary execution)
- **Support:** Documentation Agent (type hints for renamed modules)
- **Consultation:** Financial Domain Agent (if financial modules affected)
- **Validation:** Testing & Validation Agent (ensure tests still pass)

#### Phase 2: Code Structure & Organization  
- **Lead:** Code Quality Agent (structure refactoring)
- **Support:** Documentation Agent (update docstrings for new structure)
- **Consultation:** Financial Domain Agent (validate calculation logic integrity)
- **Validation:** Testing & Validation Agent (comprehensive testing post-refactoring)

#### Phase 3: Error Handling & Logging
- **Lead:** Code Quality Agent (implement centralized error handling)
- **Support:** Documentation Agent (document new exception classes)
- **High Consultation:** Financial Domain Agent (domain-specific error scenarios)
- **Validation:** Testing & Validation Agent (test error handling paths)

#### Phase 4: Configuration & Constants
- **Lead:** Code Quality Agent (consolidate configuration)
- **Support:** Documentation Agent (document configuration options)
- **Consultation:** Financial Domain Agent (financial parameter validation)
- **Validation:** Testing & Validation Agent (configuration testing)

#### Phase 5: Documentation & Type Safety
- **Lead:** Documentation Agent (primary execution)
- **Support:** Code Quality Agent (ensure consistency with code changes)
- **Consultation:** Financial Domain Agent (financial terminology accuracy)
- **Validation:** Testing & Validation Agent (test documentation examples)

#### Phase 6: Testing & Quality Assurance
- **Lead:** Testing & Validation Agent (primary execution)
- **Support:** All agents (provide testing requirements and scenarios)
- **Coordination:** Code Quality Agent (ensure alignment with overall quality goals)

## Conflict Resolution Protocol

### Conflict Types & Resolution

#### 1. Technical Conflicts
**Scenario:** Agents propose different solutions for the same issue
**Resolution Process:**
1. Agents document their approaches in Task Master
2. Code Quality Agent (Lead) reviews both approaches
3. Financial Domain Agent provides domain expertise if applicable
4. Decision made based on:
   - Code quality impact
   - Financial accuracy maintenance
   - Implementation complexity
   - Long-term maintainability

#### 2. Priority Conflicts
**Scenario:** Multiple urgent tasks competing for attention
**Resolution Process:**
1. Code Quality Agent assesses overall Task #46 impact
2. Tasks prioritized based on:
   - Dependency chains
   - Risk to financial accuracy
   - Impact on other agents' work
   - Overall project timeline

#### 3. Quality Standard Conflicts
**Scenario:** Different interpretations of quality requirements
**Resolution Process:**
1. Testing & Validation Agent provides quality standard clarification
2. Documentation Agent ensures consistency with documentation standards
3. Code Quality Agent makes final decision on implementation approach

### Escalation Path
```
Agent-to-Agent Discussion
↓ (If unresolved within 1 work session)
Lead Agent Decision
↓ (If impacts project timeline)
Human Project Manager Consultation
```

## Progress Tracking & Reporting

### Real-Time Tracking
- **Task Master Dashboard:** Live status of all subtasks
- **Agent Status Updates:** Current focus and next steps
- **Blocker Identification:** Immediate visibility of impediments
- **Quality Metrics:** Coverage, compliance, and error rates

### Progress Reporting Format
```
Agent: [Agent Name]
Current Focus: [Task ID and description]  
Status: [In Progress/Completed/Blocked]
Next Steps: [Planned activities]
Dependencies: [Waiting on other agents]
Issues: [Any blockers or concerns]
ETA: [Estimated completion time]
```

### Coordination Meetings
**Virtual Coordination Points:**
- **Phase Start:** All agents align on phase objectives
- **Mid-Phase Check:** Progress review and blocker resolution  
- **Phase End:** Quality validation and next phase preparation
- **Issue Escalation:** As needed for conflict resolution

## Quality Gates & Validation

### Inter-Agent Quality Checks
1. **Code Quality Gate:** All code changes reviewed by Code Quality Agent
2. **Documentation Gate:** All documentation changes validated by Documentation Agent
3. **Financial Accuracy Gate:** Financial logic changes approved by Financial Domain Agent  
4. **Testing Gate:** All changes must pass comprehensive testing by Testing & Validation Agent

### Cross-Agent Validation Requirements
- **Code Changes:** Must maintain or improve quality metrics
- **Documentation Updates:** Must be consistent and accurate
- **Financial Logic:** Must maintain calculation accuracy
- **Test Coverage:** Must maintain or improve coverage levels

## Resource Allocation & Management

### Tool Access Coordination
- **Exclusive Access:** Agents coordinate file locks during simultaneous editing
- **Shared Resources:** Task Master system shared across all agents
- **Bash Execution:** Coordinated to avoid conflicts (e.g., test runs)

### Time Management
- **Parallel Execution:** Documentation and Code Quality agents work simultaneously when possible
- **Sequential Dependencies:** Respect task dependencies and validation requirements
- **Buffer Time:** Account for coordination overhead in time estimates

## Success Metrics

### Coordination Effectiveness
- **Communication Latency:** Average time for agent responses (<30 minutes)
- **Conflict Resolution Time:** Average time to resolve conflicts (<2 hours)
- **Task Handoff Efficiency:** Smooth transitions between phases
- **Overall Project Velocity:** Task completion rate vs. estimates

### Quality Outcomes
- **Consistency Across Agents:** Uniform quality standards application
- **Integration Success:** Seamless integration of agent outputs
- **Regression Prevention:** Zero functionality regressions
- **Stakeholder Satisfaction:** Meeting project quality expectations

## Protocol Maintenance
- **Regular Review:** Monthly protocol effectiveness assessment
- **Adaptation:** Modify protocols based on agent performance and project needs
- **Documentation Updates:** Keep coordination protocols current with project evolution
- **Lesson Learning:** Capture and apply coordination improvements continuously