from collections import defaultdict, deque

class Graph:
    def __init__(self):
        self.graph = defaultdict(list)

    def add_edge(self, node1, node2):
        self.graph[node1].append(node2)
        


# Create the graph for Test Case 2
graph = Graph()
graph.add_edge('A', 'B')
graph.add_edge('B', 'C')
graph.add_edge('C', 'D')
graph.add_edge('D', 'B')  # Cycle here

print("BFS from A:", graph.bfs('A'))  # Expected: ['A', 'B', 'C', 'D']
print("DFS from A:", graph.dfs('A'))  # Expected: ['A', 'B', 'C', 'D'] or other DFS order