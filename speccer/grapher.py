import contextlib

from . import config

_count = 0

class Node:
    def __init__(self, id, name='unknown'):
        self.id, self.name = id, name
        self.edges = set()
        self._edge_attrs = {}

    def __repr__(self):
        return 'Node({}, name={})'.format(repr(self.id), repr(self.name))

    def __str__(self):
        return '({})'.format(self.name)

    def __hash__(self):
        return hash(self.id) ^ 0b101010110101101010

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False

class Graph:
    def __init__(self):
        self._nodes = set()
        self.stack = []
        self._previous = None
        self._sz = 0
        self.gv = config.CONFIG.graphviz_digraph
        self.iterator = None

    def create_node(self, name=None):
        node = self.add(Graph.generate_hash(), name)
        return node

    @contextlib.contextmanager
    def push_node(self, node=None, name=None, **edge_attrs):

        if not node:
            node = self.create_node(name)

        last = None
        if self.stack:
            last = self.stack[-1]

        self.stack.append(node)

        try:
            yield node
        except StopIteration:
            node.name = "StopIteration"  # this seems weird to put the StopIteration in the graph, but it's for completeness
        finally:
            self.stack.pop()

        if last:
            self.edge(node, last, **edge_attrs)

    def add(self, node_id, name):
        node_id = node_id or Graph.generate_hash()
        if name:
            node = Node(node_id, name)
        else:
            node = Node(node_id)

        self._nodes.add(node)
        return node

    def edge(self, a, b, **attrs):
        a._edge_attrs[b] = attrs
        a.edges.add(b)

    def remove(self, node):
        self._nodes.remove(node)

        for n in iter(self._nodes):
            with contextlib.suppress(KeyError):
                n.edges.remove(node)

    def _push(self, node):
        self._stack.append(node)
        return node

    def _pop(self):
        self._previous = self._stack.pop()
        return self._previous

    def render(self):
        for node in self._nodes:
            self.gv.node(node.id, label=node.name)
            for n in node.edges:
                self.gv.edge(node.id, n.id, **node._edge_attrs[n])

        self.gv.render('generation.gv')

    @staticmethod
    def generate_hash():
        global _count
        _count += 1
        return str(_count)

    def __eq__(self, other):
        if not isinstance(other, Graph):
            return False

        return (other._stack == self._stack
                and other._nodes == self._nodes)

if not config.CONFIG.graphviz:
    import unittest.mock
    Graph = unittest.mock.Mock()