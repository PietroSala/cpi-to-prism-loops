# MDP Process Specifications

## State Values

Each region/module has a state{id} internal variable with these values:

- 0: (EXCLUDED) Will not be executed in current computation
- 1: (OPEN) Ready but not executed, initial state for non-root modules
- 2: (STARTED) Started, initial state for root module
- 3: (RUNNING) Running for at least one Unit of Time (UOT)
- 4: (COMPLETED) Just ended
- 5: (EXPIRED) Ended for at least 1 UOT

## Task Module Specifications

Task-type region modules have an additional internal variable step{id} that varies between 0 and the task's duration.

## Formula Properties

### ReadyPending Formula

`ReadyPending{id}` is true when: state{id}=1 AND one of:

1. For sequence parent:
   - Head child: parent state=2
   - Tail child: parent state in {2,3} AND head sibling state in {4,5}

2. For parallel parent:
   - Parent state in {2,3}

3. For choice parent:
   - True child: parent state in {2,3}
   - False child: parent state in {2,3} AND true sibling state in {0,2}

4. For nature parent:
   - True child: parent state in {2,3}
   - False child: parent state in {2,3} AND true sibling state in {0,2}

### ClosingPending Formula

`ClosingPending{id}` is true when state{id}=3 AND:

1. For task: step{id} equals duration
2. For sequence: tail child state in {4,5}
3. For parallel: both children states in {4,5}
4. For choice/nature: any child state in {4,5}

### Control Formulas

`ReadyPendingCleared`: Conjunction of NOT ReadyPending{id} for all non-root IDs

`ClosingPendingCleared`: Conjunction of NOT ClosingPending{id} for all IDs

`StepReady{id}`: For tasks only, true when:
- state{id} in {2,3} AND step{id} < duration{id}

`StepAvailable`: True when:
- ReadyPendingCleared AND ClosingPendingCleared AND
- At least one task has StepReady{id} true

### Active Properties

`ActiveReadyPending{id}`: True when:
- ReadyPending{id} holds AND
- All lower ID regions have ReadyPending false

`ActiveClosingPending{id}`: True when:
- ReadyPendingCleared holds AND
- ClosingPending{id} holds AND
- All lower ID regions have ClosingPending false

## Module Rules

### Task Module (duration > 1)

```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}' = 2
[step] StepAvailable & state{id}=2 -> step{id}'=1 & state{id}'=3
[step] StepAvailable & state{id}=3 & step{id}<duration{id}-1 -> step{id}'=step{id}+1
[step] StepAvailable & state{id}=3 & step{id}=duration{id}-1 -> step{id}'=step{id}+1 & state{id}'=4
[step] StepAvailable & state{id}=4 -> state{id}'=5
[step] StepAvailable & (state{id}=0 | state{id}=1 | state{id}=5) -> true
```

### Task Module (duration = 1)

```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}'=2
[step] StepAvailable & state{id}=2 -> step{id}'=1 & state{id}'=4
[step] StepAvailable & state{id}=4 -> state{id}'=5
[step] StepAvailable & (state{id}=0 | state{id}=1 | state{id}=5) -> true
```

### Sequence/Parallel Module

```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}'=2
[running_to_completed_{id}] ActiveClosingPending_{id} -> state{id}'=4
[step] StepAvailable & (state{id}=0 | state{id}=1 | state{id}=5 | state{id}=3) -> true
[step] StepAvailable & state{id}=2 -> state{id}'=3
[step] StepAvailable & state{id}=4 -> state{id}'=5
```

### Choice Region Rules

Choice module itself:
```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}'=2
[running_to_completed_{id}] ActiveClosingPending_{id} -> state{id}'=4
[step] StepAvailable & (state{id}=0 | state{id}=1 | state{id}=5 | state{id}=3) -> true
[step] StepAvailable & state{id}=2 -> state{id}'=3
[step] StepAvailable & state{id}=4 -> state{id}'=5
```

True child of choice:
```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}'=2
[open_to_disabled_{id}] ActiveReadyPending_{id} -> state{id}'=0
```

False child of choice (where id'' is true sibling):
```
[open_to_started_{id}] ActiveReadyPending_{id} & state{id''}=0 -> state{id}'=2
[open_to_disabled_{id}] ActiveReadyPending_{id} & state{id''}=2 -> state{id}'=0
```

### Nature Region Rules

Nature module itself:
```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}'=2
[running_to_completed_{id}] ActiveClosingPending_{id} -> state{id}'=4
[step] StepAvailable & (state{id}=0 | state{id}=1 | state{id}=5 | state{id}=3) -> true
[step] StepAvailable & state{id}=2 -> state{id}'=3
[step] StepAvailable & state{id}=4 -> state{id}'=5
```

True child of nature (where p is parent's probability):
```
[open_to_nature_{id}] ActiveReadyPending_{id} -> p:(state{id}'=2) + (1-p):(state{id}'=0)
```

False child of nature (where id'' is true sibling):
```
[open_to_started_{id}] ActiveReadyPending_{id} & state{id''}=0 -> state{id}'=2
[open_to_disabled_{id}] ActiveReadyPending_{id} & state{id''}=2 -> state{id}'=0
```

## Labels

Each formula has a corresponding label with identical name and condition. Labels support property verification and include:

1. All ClosingPending formulas
2. All ReadyPending formulas
3. ReadyPendingCleared and ClosingPendingCleared
4. All StepReady formulas
5. StepAvailable
6. All ActiveReadyPending formulas
7. All ActiveClosingPending formulas

## Module Generation Order

Modules must be generated in ascending order of region IDs to ensure proper initialization and consistent transition handling.

## Dependencies

When calculating formulas that reference multiple regions (like ActiveReadyPending), the order of evaluation must respect the region ID ordering to maintain consistency.