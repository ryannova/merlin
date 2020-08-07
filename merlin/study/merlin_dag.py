"""Module that contains the implementation of a Directed-Acyclic Graph."""

import logging

import networkx as nx


logger = logging.getLogger(__name__)


class DAG(nx.DiGraph):
    def __init__(self):
        super(DAG, self).__init__()
        self.values = {}

    def add_node(self, name, obj):
        logging.debug(f"Adding {name}...")
        if name in self.nodes:
            logger.warning(f"Node {name} already exists. Returning.")
            return

        logger.debug(f"Node {name} added. Value is of type {type(obj)}.")
        super().add_node(name)
        self.values[name] = obj

    def add_edge(self, src, dest):
        # Disallow loops to the same node.
        if src == dest:
            msg = "Cannot add self-referring cycle edge ({}, {})".format(src, dest)
            logger.error(msg)
            return

        # Disallow adding edges to the graph before nodes are added.
        error = (
            "Attempted to create edge ({src}, {dest}), but node {node}"
            " does not exist."
        )
        if src not in self.nodes:
            error = error.format(src=src, dest=dest, node=src)
            logger.error(error)
            raise ValueError(error)

        if dest not in self.nodes:
            logger.error(error, src, dest, dest)
            return

        if (src, dest) in self.edges:
            logger.debug("Edge (%s, %s) already in DAG. Returning.", src, dest)
            return

        # If dest is not already and edge from src, add it.
        super().add_edge(src, dest)
        logging.debug(f"Edge ({src}, {dest}) added.")

        # Check to make sure we've not created a cycle.
        if self.detect_cycle():
            msg = f"Adding edge ({src}, {dest}) creates a cycle."
            logger.error(msg)
            raise Exception(msg)

    def remove_edge(self, src, dest):
        if src not in self.nodes:
            logger.warning(
                f"Attempted to remove an edge ({src}, {dest}), but {src} does not exist."
            )
            return

        if dest not in self.nodes:
            logger.warning(
                f"Attempted to remove an edge from ({src}, {dest}), but {dest} does not exist."
            )
            return

        if (src, dest) not in self.edges:
            logger.warning(
                f"Attempted to remove edge ({src}, {dest}), which does not exist."
            )

        super().remove_edge(src, dest)
        logging.debug(f"Removed edge ({src}, {dest}).")

    def get_adjacency_matrix(self):
        sparse_matrix = nx.linalg.graphmatrix.adjacency_matrix(self)
        result = sparse_matrix.todok()
        return dict(result)

    def dfs_subtree(self, src, par=None):
        return nx.dfs_tree(self, src)

    def bfs_subtree(self, src):
        return nx.bfs_tree(self, src)

    def topological_sort(self):
        return nx.topological_sort(self)

    def detect_cycle(self):
        return not nx.is_directed_acyclic_graph(self)
