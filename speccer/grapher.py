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

    def __hash__(self):
        return hash(self.id) ^ 0b101010110101101010

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False

        return (self.id == other.id
                and self.edges == other.edges
                and self._edge_attrs == other._edge_attrs)

class Graph:
    def __init__(self):
        self._nodes = set()
        self._stack = []
        self._previous = None
        self._sz = 0
        self.gv = config.CONFIG.graphviz_digraph

    def new_node(self, node=None, name=None):
        if node is None:
            node = self.add(Graph.generate_hash(), name)
        elif name is not None:
            node.name = name
        return node

    @contextlib.contextmanager
    def push_context(self, node=None, name=None, remove=False, edge_attrs={}):
        node = self.new_node(node=node, name=name)

        last = None
        if self._stack:
            last = self._stack[-1]

        self._push((node, edge_attrs))

        try:
            yield node
        except StopIteration:
            if remove:
                self.remove(node)
            raise
        else:
            if last:
                last_node, last_attrs = last
                self.edge(last_node, node, **edge_attrs)
        finally:
            self._pop()

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
        
