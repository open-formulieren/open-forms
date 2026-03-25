from collections import defaultdict
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass

from networkx import DiGraph
from networkx.algorithms import simple_cycles, topological_sort
from networkx.algorithms.dag import lexicographical_topological_sort

from .models import Form, FormLogic, FormStep


def create_graph(rules: Iterable[FormLogic]) -> DiGraph:
    """
    Create a directed graph from a list of rules.

    Rules will be added as nodes, and dependencies between rules are the edges. These
    are determined based on the input and output variables of the rules. The variable(s)
    that describe the dependencies will be added to the edge data.

    :param rules: Iterable of FormLogic rules.
    """
    # Mapping from variables to list of rules which mutate/change them in their actions.
    output_variables_to_rule: defaultdict[str, list[FormLogic]] = defaultdict(list)
    for rule in rules:
        for variable_key in rule.output_variable_keys:
            output_variables_to_rule[variable_key].append(rule)

    graph = DiGraph()
    for rule in rules:
        graph.add_node(rule)

        # For all the input variable keys of the current rule, check if there are other
        # rules that mutate this variable.
        for key in rule.input_variable_keys:
            if key not in output_variables_to_rule:
                # If there aren't, continue to the next variable.
                continue

            # Get list of rules that mutate this variable in their actions.
            dep_rules = output_variables_to_rule[key]
            for dep_rule in dep_rules:
                if (dep_rule, rule) in graph.edges:
                    # If we already have an edge, just add the key to the variables.
                    graph.get_edge_data(dep_rule, rule)["variables"].add(key)
                    continue

                # Add an edge from the dependency rule to the rule we are currently
                # evaluating.
                graph.add_edge(dep_rule, rule, variables={key})

    return graph


@dataclass
class Cycle:
    rules: Collection[FormLogic]
    variables: Collection[str]


def detect_cycles(graph: DiGraph) -> Collection[Cycle] | None:
    """
    Detect (self) cycles in the graph.

    The graph consists of logic rules as nodes, and the edges are determined based on
    the input and output variables of the rules. It contains a cycle if following the
    dependencies of a rule brings us back to the same rule.

    Consider the following example:
    The form has three user-defined variables: "foo", "bar", and "baz"
    With logic rules:
      1. "foo" in the trigger (input) and "bar" in a variable action (output)
      2. "bar" in the trigger (input) and "baz" in a variable action (output)
      3. "baz" in the trigger (input) and "foo" in a variable action (output)
    If we look at rule 1, it uses "foo" as an input, which is set by rule 3. Then, if we
    look at rule 3, it uses "baz" as an input, which is set by rule 2. Finally, if we
    look at rule 2, it uses "bar" as an input, which is set by rule 1, completing the
    cycle: rule 1 -> rule 3 -> rule 2 -> rule 1 -> ...

    We need to detect this, as it implies logic evaluation is not a single pass
    operation -> it does not converge to a final state.

    A "self cycle" means a single rule uses a variable in both the input and output
    variables. Something like: "var = var + 1". Also this does not converge to a final
    state.

    :param graph: Directed graph with logic rules as nodes.
    :returns: List of cycles if there are any, ``None`` otherwise.
    """
    cycles = []
    # Note that `simple_cycles` also detects self cycles.
    for rules in simple_cycles(graph):
        # Get the variables that create the cycle by inspecting the edge data for each
        # of the involved rules.
        variables = set()
        # `rules` is a list (meaning it's ordered!) of nodes (`FormLogic`) which make up
        # the cycle. The dependencies (variables) between the rules can be extracted
        # from the edge data (we add this during creation of the graph). To do this, we
        # shift the rules by one, and zip them with the original rule list. This gives
        # us the edges between the nodes, e.g. for rules `[rule1, rule2, rule4]` we get
        # `(rule1, rule2), (rule2, rule4), and (rule4, rule1).
        shifted_rules = rules[1:] + rules[:1]
        for rule_1, rule_2 in zip(rules, shifted_rules, strict=True):
            variables |= graph.get_edge_data(rule_1, rule_2)["variables"]
        cycles.append(Cycle(rules=rules, variables=variables))

    return cycles if cycles else None


def resolve_order(graph: DiGraph, with_step: bool = True) -> Sequence[FormLogic]:
    """
    Perform a topological sort on the graph. Optionally with the step order (ascending)
    being the deciding factor if there is no required order between rules.

    For example, if we have two rules that are not dependent on each other, but they
    should be executed on step 1 and 2, respectively, the rule from step 1 will be
    first in the list.

    Note: if there are cycles in the graph, this will raise an error, so make sure to
    call ``detect_cycles(graph)`` first.

    :param graph: Directed acyclic graph with logic rules as nodes.
    :param with_step: If ``True``, the step order (ascending) will be the deciding
      factor if there is no required order between rules.
    """

    def get_order_of_first_step(rule: FormLogic) -> int:
        assert len(rule.steps) != 0, "A rule is expected to have a step"
        return min(rule.steps, key=lambda step: step.order).order

    return (
        list(lexicographical_topological_sort(graph, key=get_order_of_first_step))
        if with_step
        else list(topological_sort(graph))
    )


def add_missing_steps(graph: DiGraph, first_step: FormStep) -> None:
    """
    Iterate over all nodes of the graph and resolve a step for logic rules that do not
    have one yet. We look at the parent nodes for this, or assign the provided first
    step if it has no parent nodes.

    Iterating over the sorted nodes ensures we are able to resolve a step for nodes of
    which their direct parent does not have a step, but their grandparent does. It makes
    sure the parent gets processed before the child.

    :param graph: Directed acyclic graph with logic rules as nodes.
    :param first_step: Form step that will be assigned if a rule does not have any
      predecessors.
    """
    for rule in topological_sort(graph):
        if rule.steps:
            # Skip rules that already have steps
            continue

        if graph.in_degree(rule) == 0:
            # If the rule has no parents, add the first step
            rule.steps = {first_step}
            continue

        parent_steps = set()
        for parent in graph.predecessors(rule):
            parent_steps |= parent.steps

        rule.steps = parent_steps


class CyclesDetected(Exception):
    def __init__(self, cycles: Collection[Cycle], *args, **kwargs):
        self.cycles = cycles
        super().__init__(*args, **kwargs)


type RuleWithSteps = tuple[FormLogic, Collection[FormStep]]


def analyze_rules(
    form: Form,
    rules: Sequence[FormLogic] | None = None,
    first_step: FormStep | None = None,
) -> Sequence[RuleWithSteps]:
    """
    Determine which form steps are relevant for each logic rule in the form.

    :param form: The form to analyze. It must have the new logic evaluation enabled.
    :param rules: Input rules for the form to analyze. If not provided, the current
      set of rules on the form will be used. The instances can be unsaved, in-memory
      instances.
    :returns: An ordered sequence of ``(rule, steps)`` pairs. The input rules are
      re-ordered according to their dependencies. The collection of steps specifies on
      which steps the rule must be executed.
    """
    if not form.new_logic_evaluation_enabled:
        raise ValueError("Form to analyze must have the new logic evaluation enabled.")

    if rules is None:
        rules = list(form.formlogic_set.order_by("order"))

    graph = create_graph(rules)
    if cycles := detect_cycles(graph):
        raise CyclesDetected(cycles)

    if first_step is None:
        form_steps: Sequence[FormStep] = list(form.formstep_set.order_by("order"))
        assert form_steps, "Forms without any steps are not allowed."
        first_step = form_steps[0]

    assert first_step.order == 0
    add_missing_steps(graph, first_step)
    new_rule_order = resolve_order(graph)

    # Reorder the incoming data according to the determined order.
    return [(rule, rule.steps) for rule in new_rule_order]
