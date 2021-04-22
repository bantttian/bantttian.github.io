import py2neo

neo4j_host = "10.176.36.21"
neo4j_username = "neo4j"
neo4j_password = "123"
port = '16888'
graph = py2neo.Graph(host=neo4j_host, port=port, auth=(neo4j_username, neo4j_password))
# print(graph.nodes[0])