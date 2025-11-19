from collections import defaultdict
from typing import TypedDict

from networkx import DiGraph
from networkx.algorithms import simple_cycles, topological_sort

from openforms.forms.models import Form, FormLogic


def create_graph(form: Form) -> DiGraph:
    rules = FormLogic.objects.filter(form=form)

    # Mapping from variables to list of rules in which they are set as output
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
                # TODO-2409: if there is an edge already, it will not be added. We
                #  should append the variable key to the list "variable" edge data
                #  instead.
                # Add an edge from the dependency rule to the rule we are currently
                # evaluating
                graph.add_edge(dep_rule, rule, variable=key)

    return graph


class Cycle(TypedDict):
    rules: list[FormLogic]
    variables: list[str]


def detect_cycles(graph: DiGraph) -> list[Cycle] | None:
    cycles = []
    # TODO-2409: simple_cycles also detects self cycles of nodes. Should we allow this?
    #  It doesn't neem too weird to do something like "var_1 = var_1 + var_2"
    for rules in simple_cycles(graph):
        variables = [
            graph.get_edge_data(rules[i], rules[(i + 1) % len(rules)])["variable"]
            for i in range(len(rules))
        ]
        cycles.append(Cycle(rules=rules, variables=variables))

    return cycles if cycles else None


def resolve_order(graph: DiGraph) -> list[FormLogic]:
    return list(topological_sort(graph))
