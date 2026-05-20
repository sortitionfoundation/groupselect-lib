# Concepts

## Citizens' Assemblies and group allocation

A Citizens' Assembly (CA) is a deliberative democratic process in which a
group of citizens — selected to be broadly representative of the population —
engage in structured discussion about a specific policy issue. Participants
are typically divided into smaller discussion tables for each session, then
reassigned to new tables for the next session.

**GroupSelect** solves the problem of deciding which participants sit at
which table, for each session. This is not trivial: two important and
partially conflicting criteria must be balanced.

## Diversity

Each discussion table should *demographically mirror* the full group of
participants. If the assembly is 50% women, each table should also be
approximately 50% women. The same applies to other relevant attributes:
age brackets, ethnicity, location, and so on.

Formally, for a field with categories $c_1, \ldots, c_k$ having population
shares $p_1, \ldots, p_k$, the ideal group has shares $p_1, \ldots, p_k$
as well. The diversity score measures the average L1 deviation from this
ideal across all groups and all diversification fields.

### FieldMode options

The library exposes three ways a field can influence the allocation:

| Mode | Behaviour |
|------|-----------|
| `Diversify` | Distribute participants proportionally (mirror the population) |
| `Cluster` | Keep participants with a specific value in the same groups |
| `Ignore` | Field is not used during allocation |

**Clustering** is used for accessibility or logistical constraints — for
example, keeping all participants who need sign-language interpretation at
the same table, so that only one interpreter is needed per session.

## Uniqueness (meeting diversity)

Over the course of a CA, participants should meet as many *different* fellow
participants as possible. Repeated pairings reduce the diversity of
perspectives encountered and may cause participants to form fixed opinions
within a smaller social circle.

GroupSelect tracks which pairs of participants have been in the same group
across allocation rounds. The meeting score measures how many unique pairs
have been formed, normalised between the theoretical worst case (all rounds
have identical groups) and best case (every round has entirely disjoint
pairings).

## The trade-off

Strict diversity enforcement *constrains* which swaps are permissible. If a
field is to be distributed exactly proportionally, a participant cannot be
moved from one group to another unless another participant of the same
demographic value moves in the opposite direction. This limits the search
space for meeting optimisation.

Conversely, relaxing diversity constraints allows more freedom to maximise
unique meetings — but at the cost of less representative group compositions.

The **HERMES** algorithm makes this trade-off explicit and user-controllable
via per-field weights (called `pareto_probs`). Setting a field's weight to
`0.5` enforces strict diversity for that field; setting it to `0.0`
effectively ignores that field's diversity constraint so meetings can be
maximised. See [HERMES](algorithms/hermes.md) for details.

## Input data format

Participant data is represented as an integer-encoded matrix:

- Each **row** is one participant.
- Each **column** is one categorical field.
- Field values must be **non-negative integers** (0, 1, 2, …). The actual
  category labels are not needed by the algorithm; only the integer codes.

The `allocate_pandas` function handles the encoding automatically from a
pandas DataFrame.

## Output: AllocationEnsemble

The result of an allocation run is an `AllocationEnsemble`: a list of
`Allocation` objects, one per session/round. Each `Allocation` is a list of
`ParticipantGroup` objects, each of which is a list of participant indices
(row numbers from the input data).

The ensemble provides scoring methods:

| Method | Description |
|--------|-------------|
| `calc_meeting_rel_score()` | Fraction of all possible pairs that met ≥ once |
| `calc_meeting_norm_score()` | Normalised score: 0 = worst case, 1 = best case |
| `calc_diversity_score(data)` | Sum of per-field L1 deviations (lower = better) |
