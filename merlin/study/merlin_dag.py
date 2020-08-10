"""Module that contains the implementation of a Directed-Acyclic Graph."""

import logging

import networkx as nx


LOG = logging.getLogger(__name__)


class DAG(nx.DiGraph):
    def __init__(self):
        super(DAG, self).__init__()
        self.values = {}

    def add_node(self, name, obj):
        logging.debug(f"Adding node '{name}'...")
        if name in self.nodes:
            LOG.warning(f"Node '{name}' already exists. Returning.")
            return

        LOG.debug(f"Node {name} added. Value is of type {type(obj)}.")
        super().add_node(name)
        self.values[name] = obj

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
