from collections import defaultdict
from collections.abc import Collection
from typing import TypedDict

from networkx import DiGraph
from networkx.algorithms import simple_cycles, topological_sort
from networkx.algorithms.dag import lexicographical_topological_sort

from .models import FormLogic


def create_graph(rules: Collection[FormLogic]) -> DiGraph:
    """
    Create a directed graph from a list of rules.

    Rules will be added as nodes, and dependencies between rules are the edges. These
    are determined based on the input and output variables of the rules. The variable
    that describe the dependencies will be added to the edge data.
    """
    # Mapping from variables to list of rules which mutate/change them in their actions
    output_variables_to_rule = defaultdict(list)
    for rule in rules:
        for component in rule.output_variable_keys:
            output_variables_to_rule[component].append(rule)

    graph = DiGraph()
    for rule in rules:
        graph.add_node(rule)

        # For all the input variable keys of the current rule, check if there are other
        # rules that mutate this variable
        for key in rule.input_variable_keys:
            if key not in output_variables_to_rule:
                continue

            # List of rules that mutate this variable in their actions
            dep_rules = output_variables_to_rule[key]
            for dep_rule in dep_rules:
                if (dep_rule, rule) in graph.edges:
                    # If we already have an edge, just add the key to the variables
                    graph.get_edge_data(dep_rule, rule)["variables"].add(key)
                    continue

                # Add an edge from the dependency rule to the rule we are currently
                # evaluating
                graph.add_edge(dep_rule, rule, variables={key})

    return graph


class Cycle(TypedDict):
    rules: list[FormLogic]
    variables: set[str]


def detect_cycles(graph: DiGraph) -> list[Cycle] | None:
    """Detect cycles in the graph."""
    cycles = []
    # TODO-2409: simple_cycles also detects self cycles of nodes. Should we allow this?
    #  It doesn't neem too weird to do something like "var_1 = var_1 + var_2". Although,
    #  this does mean variables will keep changing on each logic evaluation pass, so
    #  it's not single pass
    for rules in simple_cycles(graph):
        # Get the variables that create the cycle by inspecting the edge data for each
        # of the involved rules.
        variables = set()
        for r1, r2 in zip(rules, rules[1:] + rules[:1], strict=False):
            variables |= graph.get_edge_data(r1, r2)["variables"]
        cycles.append(Cycle(rules=rules, variables=variables))

    return cycles if cycles else None


def resolve_order(graph: DiGraph) -> list[FormLogic]:
    """
    Perform a topological sort on the graph.

    If there are cycles in the graph, this will raise an error, so make sure to call
    ``detect_cycles(graph)`` first.
    TODO-2409: might be good to combine them?
    """
    return list(topological_sort(graph))


def resolve_order_with_step(graph: DiGraph) -> list[FormLogic]:
    """
    Perform a topological sort on the graph, with the step order (ascending) being the
    deciding factor if there is no required order between rules.

    For example, if we have two rules that are not dependent on each other, but they
    should be executed on step 1 and 2, respectively, the rule from step 1 will be
    first in the list.
    """

    def get_order_of_first_step(rule: FormLogic) -> int:
        # If we were not able to associate any steps with this rule, return -1 to ensure
        # sorting doesn't crash. Step ordering starts at 0, so -1 just puts the rule
        # in front of all others that do have a step.
        return min(rule.steps, key=lambda step: step.order).order if rule.steps else -1

    return list(lexicographical_topological_sort(graph, key=get_order_of_first_step))


def add_missing_steps(graph: DiGraph):
    """
    Iterate over all nodes of the graph and resolve a step for logic rules that do not
    have one yet. We look at the parent nodes for this.

    Iterating over the sorted nodes ensures we are able to resolve a step for nodes of
    which their direct parent does not have a step, but their grandparent does. It makes
    sure the parent gets processed before the child.
    """
    for rule in topological_sort(graph):
        if rule.steps:
            # Skip rules that already have steps
            continue

        if graph.in_degree(rule) == 0:
            # TODO-2409: if it has no predecessors, we should add the first step. E.g.
            #  service fetch that sets user-defined variable, which is used as dynamic
            #  options by radio/select/selectboxes components. Should we add it here?
            continue

        parent_steps = set()
        for parent in graph.predecessors(rule):
            parent_steps |= parent.steps
        # Assign the last step to ensure we have all data available
        rule.steps = {max(parent_steps, key=lambda step: step.order)}
