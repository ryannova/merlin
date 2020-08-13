"""Module that contains the implementation of a Directed-Acyclic Graph."""

from copy import deepcopy
import logging
import random

import networkx as nx


LOG = logging.getLogger(__name__)


class DAG(nx.DiGraph):
    def __init__(self):
        super(DAG, self).__init__()
        self.values = {}
        self.node_ids = {}
        self.curr_id = 0

    def add_node(self, name, obj, node_id=None):
        logging.debug(f"Adding node '{name}'...")
        if name in self.nodes:
            LOG.warning(f"Node '{name}' already exists. Returning.")
            return

        LOG.debug(f"Node {name} added. Value is of type {type(obj)}.")
        super().add_node(name)
        self.values[name] = obj
        if node_id is not None:
            new_id = node_id
        else:
            new_id = self.curr_id
            self.curr_id += 1
        self.node_ids[name] = new_id

    def remove_node(self, node):
        self.values.pop(node)
        #self.node_ids.pop(node)
        super().remove_node(node)

    def add_edge(self, src, dest):
        # Disallow loops to the same node.
        if src == dest:
            msg = "Cannot add self-referring cycle edge ({}, {})".format(src, dest)
            LOG.error(msg)
            return

        # Disallow adding edges to the graph before nodes are added.
        if src not in self.nodes:
            raise ValueError(
                f"Attempted to create edge ({src}, {dest}), but node '{src}' does not exist."
            )

        if dest not in self.nodes:
            raise ValueError(
                f"Attempted to create edge ({src}, {dest}), but node '{dest}' does not exist."
            )

        if (src, dest) in self.edges:
            LOG.debug("Edge (%s, %s) already in DAG. Returning.", src, dest)
            return

        # If dest is not already and edge from src, add it.
        super().add_edge(src, dest)
        logging.debug(f"Edge ({src}, {dest}) added.")

        # Check to make sure we've not created a cycle.
        if self.detect_cycle():
            msg = f"Adding edge ({src}, {dest}) creates a cycle."
            LOG.error(msg)
            raise Exception(msg)

    def remove_edge(self, src, dest):
        if src not in self.nodes:
            LOG.warning(
                f"Attempted to remove an edge ({src}, {dest}), but '{src}' does not exist."
            )
            return

        if dest not in self.nodes:
            LOG.warning(
                f"Attempted to remove an edge from ({src}, {dest}), but '{dest}' does not exist."
            )
            return

        if (src, dest) not in self.edges:
            LOG.warning(
                f"Attempted to remove edge ({src}, {dest}), which does not exist."
            )

        super().remove_edge(src, dest)
        logging.debug(f"Removed edge ({src}, {dest}).")

    def get_adjacency_matrix(self):
        # sparse_matrix = nx.linalg.graphmatrix.adjacency_matrix(self)
        result = nx.convert.to_dict_of_dicts(self)
        ##print("***Adjacency matrix:")
        ##print(result)
        ## TODO convert back to names
        ##result = sparse_matrix.todok()
        # result = dict(result)
        # result_final = {}
        # for k,v in sparse_matrix.items():
        #    result_final[k] = [v]
        # print(result_final)
        return result

    def dfs_subtree(self, src, par=None):
        return nx.dfs_tree(self, src)

    def bfs_subtree(self, src):
        return nx.bfs_tree(self, src)

    def topological_sort(self):
        return nx.topological_sort(self)

    def detect_cycle(self):
        return not nx.is_directed_acyclic_graph(self)

    def get_ancestor_nodes(self, node):
        result = nx.dfs_tree(self.reverse(), source=node).reverse()  
        result.remove_node(node)
        return result

    def get_tier(self, node):
        if "_source" not in list(self.nodes):
            raise ValueError("Node '_source' must be in DAG to measure node tier.")
        if node == "_source":
            return 0
        #return nx.shortest_path_length(self, source="_source", target=node, method='dijkstra')
        print(node)
        longest = max(nx.all_simple_paths(self, "_source", node), key=lambda x: len(x))
        return len(longest)

    def display(self):
        import matplotlib.pyplot as plt

        # remember number of nodes on each tier
        node_count = {}
        for node in self.nodes:
            tier = self.get_tier(node)
            if tier in node_count:
                node_count[tier] = node_count[tier] + 1
            else:
                node_count[tier] = 1

        # make dict to keep track of horizontal space on each tier
        horiz_space_used = {}
        for key in node_count:
            horiz_space_used[key] = 0

        # build a dictionary of positions for each node
        total_width = 100
        tier_space = 10
        pos_dict = {}
        for node in list(reversed(list(self.topological_sort()))):
            if node == "_source":
                pos_dict[node] = (0,0)
                continue
            tier = self.get_tier(node)
            n_nodes = node_count[tier]
            horiz_space = total_width / n_nodes
            x = horiz_space_used[tier] - ((n_nodes - 1) * horiz_space / 2)
            horiz_space_used[tier] = horiz_space_used[tier] + horiz_space
            y = (self.get_tier(node) - 1) * tier_space * -1
            pos_dict[node] = (x,y)

        # copy this DAG, but without the '_source' node
        display_dag = self
        if "_source" in self.nodes:
            no_source = deepcopy(self)
            no_source.remove_node("_source")
            pos_dict.pop("_source")
            display_dag = no_source

        #nx.draw(self, with_labels=True, layout=nx.spring_layout(self, seed=1))
        nx.draw(display_dag, pos_dict, with_labels=True)
        plt.show()

