# Process Region State Specifications

## Region State Values

Each region/module has a state{id} internal variable that can take the following values:

- 0: (EXCLUDED) Will not be executed in the current computation
- 1: (OPEN) Ready but not executed, will possibly be executed
     (This is the initial position of every module except the root)
- 2: (STARTED) Started
     (This is the initial position of the root)
- 3: (RUNNING) Running - the module has been executed for at least one Unit of Time (UOT)
- 4: (COMPLETED) The module has just ended
- 5: (EXPIRED) The module has been ended for a while, at least 1 UOT

## Task Module Specifications

Task-type region modules have an additional internal variable step{id} that varies between 0 and the task's duration.

## System Formula Properties

### Base Properties

`ReadyPending{id}`: True when:
- state{id} = 1 AND one of the following holds:
  - For sequence father: module is head child and father state = 2
  - For sequence father: module is tail child, father state in {2,3}, and head child state in {4,5}
  - For parallel father: father state in {2,3}
  - For choice father:
    * If true child: father state in {2,3}
    * If false child: father state in {2,3} AND true sibling state = 0 OR true sibling state = 2

`ClosingPending{id}`: True when:
- state{id} = 3 AND one of the following holds:
  - For task: step{id} equals duration
  - For sequence: tail child state in {4,5}
  - For parallel: both children states in {4,5}
  - For choice: at least one child state in {4,5}

### Control Properties

`ReadyPendingCleared`: Conjunction of NOT ReadyPending{id} for all non-root identifiers

`ClosingPendingCleared`: Conjunction of NOT ClosingPending{id} for all identifiers

`StepReady{id}`: Only for tasks, true when:
- state{id} in {2,3} AND step{id} < duration{id}

`StepAvailable`: True when:
- ReadyPendingCleared AND ClosingPendingCleared AND
- There exists at least one task id for which StepReady{id} is true

### Active Properties

`ActiveReadyPending{id}`: True when:
- ReadyPending{id} holds AND
- For each identifier less than id (except root), ReadyPending is false

`ActiveClosingPending{id}`: True when:
- ReadyPendingCleared holds AND
- ClosingPending{id} holds AND
- For each identifier less than id, ClosingPending is false

## Module Rules

### Step Rules for Task Modules

For a task module with id and duration > 1:
```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}' = 2
[step] StepAvailable & state{id}=2 -> step{id}'=1 & state{id}'=3
[step] StepAvailable & state{id}=3 & step{id}<duration{id}-1 -> step{id}'=step{id}+1
[step] StepAvailable & state{id}=3 & step{id}=duration{id}-1 -> step{id}'=step{id}+1 & state{id}'=4
[step] StepAvailable & state{id}=4 -> state{id}'=5
[step] StepAvailable & (state{id}=0 | state{id}=1 | state{id}=5) -> true
```

For a task with duration = 1:
```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}'=2
[step] StepAvailable & state{id}=2 -> step{id}'=1 & state{id}'=4
[step] StepAvailable & state{id}=4 -> state{id}'=5
[step] StepAvailable & (state{id}=0 | state{id}=1 | state{id}=5) -> true
```

### Choice Region Rules

For true child of choice region:
```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}' = 2
[open_to_disabled_{id}] ActiveReadyPending_{id} -> state{id}' = 0
```

For false child id of choice region (where id'' is true child):
```
[open_to_started_{id}] ActiveReadyPending_{id} & state{id''}=0 -> state{id}' = 2
[open_to_disabled_{id}] ActiveReadyPending_{id} & state{id''}=2 -> state{id}' = 0
```

For the choice module itself:
```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}'=2
[running_to_completed_{id}] ActiveClosingPending_{id} -> state{id}'=4
[step] StepAvailable & (state{id}=0 | state{id}=1 | state{id}=5 | state{id}=3) -> true
[step] StepAvailable & state{id}=2 -> state{id}'=3
[step] StepAvailable & state{id}=4 -> state{id}'=5
```

### Rules for Sequence and Parallel Modules

Non-choice children:
```
[open_to_started_{id}] ActiveReadyPending_{id} -> state{id}'=2
[running_to_completed_{id}] ActiveClosingPending_{id} -> state{id}'=4
[step] StepAvailable & (state{id}=0 | state{id}=1 | state{id}=5 | state{id}=3) -> true
[step] StepAvailable & state{id}=2 -> state{id}'=3
[step] StepAvailable & state{id}=4 -> state{id}'=5
```

When child of choice region, same rules as "Choice Region Rules" above apply.