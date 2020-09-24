import os
import re
from copy import deepcopy

import numpy as np

from merlin.study.dag.merlin_dag import ValueDAG
from merlin.study.step import MerlinStepRecord, Step


SOURCE_NODE = "_source"


def populate_basic_dag(study):
    basic_dag = ValueDAG()
    step_dicts = list(study.expanded_spec.study)

    # add nodes to basic dag
    for step_dict in step_dicts:
        workspace_value = os.path.join(study.workspace, step_dict["name"])
        # print(f"***workspace_value={workspace_value}")
        # print(f"***step dict={step_dict}")
        step_obj = Step(MerlinStepRecord(workspace_value, step_dict))
        basic_dag.add_node(step_dict["name"], step_obj)

    # add edges to basic dag
    for node in basic_dag.nodes:
        step = basic_dag.values[node]
        if "depends" not in step["run"]:
            continue
        name = step["name"]
        for dep in step["run"]["depends"]:
            if dep.endswith("_*"):
                dep = dep[:-2]
            basic_dag.add_edge(dep, name)

    basic_dag.add_node(SOURCE_NODE, None, node_id=-1)
    for node in basic_dag.nodes:
        if node == SOURCE_NODE:
            continue
        if len(basic_dag.in_edges(node)) == 0:
            basic_dag.add_edge(SOURCE_NODE, node)
    return basic_dag


def expand_parameterized_steps(study, basic_dag):
    param_dag = deepcopy(basic_dag)
    for node_name in list(param_dag.topological_sort()):
        if node_name == SOURCE_NODE:
            continue
        # print(node_name)

        # determine whether this step has params
        has_params = param_dag.values[node_name].contains_global_params(
            study.expanded_spec.globals
        )

        # TODO make sure this works, is robust, and put in the correct place
        # bottleneck_node = False
        # if "depends" in param_dag.values[node_name]["run"]:
        #    for dep in param_dag.values[node_name]["run"]["depends"]:
        #        if not dep.endswith("_*"):
        #            continue
        #        bottleneck_node = True
        #        break
        # if bottleneck_node and not has_params:
        #    continue

        # get vector of relevant parameters for this node
        parents = list(param_dag.predecessors(node_name))
        # node_params = np.array([False] * len(study.expanded_spec.globals))
        node_params = np.array(
            basic_dag.values[node_name].get_global_param_vector(
                study.expanded_spec.globals
            )
        )
        for parent in parents:
            if parent == SOURCE_NODE:
                continue
            # print(f"\tparent={parent}")
            # print(f"\t***parent param_vector={param_dag.values[parent].merlin_step_record.param_vector}")
            if param_dag.values[parent].merlin_step_record.param_vector is None:
                parent_params = np.array(
                    param_dag.values[parent].get_global_param_vector(
                        study.expanded_spec.globals
                    )
                )
            else:
                parent_params = param_dag.values[parent].merlin_step_record.param_vector
            # print(f"\t***node_params pre-update={node_params}")
            # print(f"\t***parent_params for {parent}={parent_params}")
            node_params = parent_params | node_params
            # print(f"\t***node_params updated={node_params}")
        param_dag.values[node_name].merlin_step_record.param_vector = node_params
        is_parameterized = True in node_params
        # print(f"***node_params for {node_name}={node_params}\n")

        # if this step is parameterized
        if is_parameterized:
            # relevant_params = []
            # for i, (global_name, global_val) in enumerate(study.expanded_spec.globals.items()):
            #    if node_params[i]:
            #        relevant_params.append(global_name)
            # print(f"***relevant_params={relevant_params}")

            parameterized_steps = param_dag.values[node_name].expand_global_params(
                study.expanded_spec.globals, node_params
            )

            # print(f"***parameterized_steps={parameterized_steps}")
            if parameterized_steps:
                # print(f"len of parameterized steps: {len(parameterized_steps)}")
                parent_nodes = [x[0] for x in list(param_dag.in_edges(node_name))]
                child_nodes = [x[1] for x in list(param_dag.out_edges(node_name))]
                # print(f"parents: {parent_nodes}")
                # print(f"children: {child_nodes}")
                # print(f"deleted node: {node_name}")
                node_id = basic_dag.node_ids[node_name]
                param_dag.remove_node(node_name)
                for (param_step, param_step_name) in parameterized_steps:
                    # print(f"parameterized name: {param_step_name}")
                    param_step.merlin_step_record.workspace.value = os.path.join(
                        study.workspace, param_step_name
                    )
                    # print(f"***Adding {node_id} id to node {param_step_name}")
                    param_dag.add_node(param_step_name, param_step, node_id=node_id)
                    for parent_node in parent_nodes:
                        # print(parent_node)
                        if parent_node == SOURCE_NODE:
                            parent_param_index = -1
                        else:
                            parent_param_index = param_dag.values[
                                parent_node
                            ].merlin_step_record.param_index
                        node_param_index = param_dag.values[
                            param_step_name
                        ].merlin_step_record.param_index
                        if (
                            has_params
                            or parent_param_index == -1
                            or parent_param_index == node_param_index
                        ):
                            param_dag.add_edge(parent_node, param_step_name)
                    for child_node in child_nodes:
                        param_dag.add_edge(param_step_name, child_node)
            else:
                print("ERROR does not have parameterized steps")
    return param_dag


def expand_workspace_references(basic_dag, param_dag):
    result_dag = deepcopy(param_dag)
    for node_name in list(result_dag.topological_sort()):
        if node_name == SOURCE_NODE:
            continue

        node_cmd = result_dag.values[node_name].get_cmd()

        if re.search(
            r"\$\(\w+\.workspace\)", node_cmd
        ):  # TODO make sure \w+ is correct for step names
            # print(node_name)
            ancestors = result_dag.get_ancestor_nodes(node_name)
            # print("ancestors: " + str(list(ancestors)))
            ancestor_ids = [
                result_dag.node_ids[x] for x in result_dag.get_ancestor_nodes(node_name)
            ]
            # print("ancestor ids: " + str(list(ancestor_ids)))
            workspace_node_names = re.findall(r"\$\(\w+\.workspace\)", node_cmd)
            for workspace_name in workspace_node_names:
                # workspace_name = workspace_name.strip("$(").strip("\.workspace)")
                basic_workspace_name = re.findall("\w+\.", workspace_name)[0][:-1]
                # print(workspace_name)
                workspace_id = basic_dag.node_ids[basic_workspace_name]
                if workspace_id not in ancestor_ids:
                    raise ValueError(
                        f"Step '{node_name}' is referencing an incorrect step workspace!"
                    )
                param_index = result_dag.values[
                    node_name
                ].merlin_step_record.param_index
                for node in result_dag.nodes:
                    if (
                        result_dag.node_ids[node] == workspace_id
                        and result_dag.values[node].merlin_step_record.param_index
                        == param_index
                    ):
                        workspace_path = result_dag.values[
                            node
                        ].merlin_step_record.workspace.value
                        break
                # print(f"{workspace_name} id: {workspace_id}")
                # print(workspace_name)
                # print(workspace_path)
                result_dag.values[node_name]["run"]["cmd"] = node_cmd.replace(
                    workspace_name, workspace_path
                )
                node_cmd = result_dag.values[node_name].get_cmd()
                # print("***NEW CMD:")
                # print(result_dag.values[node_name]["run"]["cmd"])

        # print(param_dag.values[node_name].get_cmd())
        # print(param_dag.values[node_name].merlin_step_record.workspace_value)
        # input()
    return result_dag


#def make_param_dirs(param_dag):
#    for node in param_dag:
#        if node == SOURCE_NODE:
#            continue
#        workspace_path = param_dag.values[node].merlin_step_record.workspace.value
#        os.mkdir(workspace_path)


def stage(study):
    # TODO
    # @1. make basic step DAG including edges
    # @2. make second DAG with parameterized names and edges
    # >3. Fix bugs

    basic_dag = populate_basic_dag(study)
    # print(f"***BASIC_DAG: {basic_dag.node_ids}")
    # if there are no global parameters, return the basic DAG.
    if study.expanded_spec.globals is None or len(study.expanded_spec.globals) == 0:
        return basic_dag

    basic_dag.display()

    # expand paramaterized steps with param_dag
    param_dag = expand_parameterized_steps(study, basic_dag)
    # print(f"***PARAM DAG IDS={param_dag.node_ids}")

    param_dag.display()

    # expand $(<step>.workspace) references in param_dag
    expanded_workspace_dag = expand_workspace_references(basic_dag, param_dag)

    # for node in expanded_workspace_dag:
    # print(node)
    # if node != "_source":
    #    print(expanded_workspace_dag.values[node].merlin_step_record.workspace)
    # print("\n")

    # expanded_workspace_dag.display()

    return expanded_workspace_dag
