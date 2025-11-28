# # agent_tree.py (unchanged)
# class AgentNode:
#     def __init__(self, name, agent=None):
#         self.name = name
#         self.agent = agent
#         self.children = []
#         self.tools = []

#     def add_child(self, child_node):
#         self.children.append(child_node)
#         return child_node

#     def add_tool(self, tool_name):
#         self.tools.append(tool_name)

#     def __repr__(self):
#         return f"AgentNode(name={self.name}, children={len(self.children)}, tools={self.tools})"


# class AgentTree:
#     def __init__(self, root: AgentNode):
#         self.root = root

#     def visualize(self):
#         print("🌳 Agent Tree Structure:")
#         self._print_node(self.root, indent=0)

#     def _print_node(self, node, indent):
#         print(" " * indent + f"- {node.name} (tools={node.tools})")
#         for child in node.children:
#             self._print_node(child, indent + 4)

# agent_tree.py
from graphviz import Digraph


class AgentNode:
    def __init__(self, name, agent=None):
        self.name = name
        self.agent = agent
        self.children = []
        self.tools = []

    def add_child(self, child_node):
        self.children.append(child_node)
        return child_node

    def add_tool(self, tool_name):
        self.tools.append(tool_name)

    def __repr__(self):
        return f"AgentNode(name={self.name}, children={len(self.children)}, tools={self.tools})"


class AgentTree:
    def __init__(self, root: AgentNode):
        self.root = root

    # --------- OLD CONSOLE VISUALIZATION (kept) ---------
    def visualize_console(self):
        print("🌳 Agent Tree Structure:")
        self._print_node(self.root, indent=0)

    def _print_node(self, node, indent):
        print(" " * indent + f"- {node.name} (tools={node.tools})")
        for child in node.children:
            self._print_node(child, indent + 4)

    # --------- NEW: GRAPHVIZ DIGRAPH REPRESENTATION ---------
    def to_digraph(self) -> Digraph:
        """
        Build and return a graphviz.Digraph representing this agent tree.
        You can then render() / view() it outside.
        """
        dot = Digraph(name="AgentTree", format="png")
        self._add_node_to_digraph(self.root, dot)
        return dot

    def _add_node_to_digraph(self, node: AgentNode, dot: Digraph):
        # Label node with name and tools
        tools_label = ", ".join(node.tools) if node.tools else "no tools"
        label = f"{node.name}\n[{tools_label}]"
        dot.node(node.name, label=label, shape="box")

        for child in node.children:
            dot.edge(node.name, child.name)
            self._add_node_to_digraph(child, dot)

    # --------- OPTIONAL: visualize() now returns the Digraph ---------
    def visualize(self) -> Digraph:
        """
        Console + graphviz combo:
        - print tree in console
        - return Digraph so caller can render/save it
        """
        self.visualize_console()
        return self.to_digraph()
