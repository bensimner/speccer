import graphviz as gv

class Config:
    '''Configuration object contains settings

    Settings:
    - Config.graphviz: bool
        When True will generate and output a generation.gv/generation.gv.pdf file
        that contains a graph of all the generation.

    - Config.graphviz_digraph
        The graphviz.Digraph object actually to be used if Config.graphviz is True
    '''
    def __init__(self, graphviz=False):
        self.graphviz = graphviz
        self.graphviz_digraph = gv.Digraph(format='svg', comment='Generation Instances') if graphviz else None

CONFIG = Config(graphviz=True)
