# agent_tree.py

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

    def visualize(self):
        print("🌳 Agent Tree Structure:")
        self._print_node(self.root, indent=0)

    def _print_node(self, node, indent):
        print(" " * indent + f"- {node.name} (tools={node.tools})")
        for child in node.children:
            self._print_node(child, indent + 4)
