from config import graph
import py2neo

def get_AST_node_by_type(type):
    """
    提供AST Type，获取AST结点
    :param lineno:
    :return: 返回第一个Node结点
    """
    Node_list = list(graph.nodes.match("AST", type=type))
    if len(Node_list) == 0:
        return None
    return Node_list[0]


def get_CFG_FUNC_ENTRY_relationships(Node):
    """
    寻找CFG的ENTRY结点，先得到relationships
    :param Node:
    :return:
    """
    return list(py2neo.RelationshipMatch(graph, nodes={Node}, r_type='ENTRY'))

def get_CFG_FUNC_ENTRY_node(Node):
    """
    寻找CFG的入口结点，只有一个
    :param Node:
    :return:
    """
    entry_relationship = get_CFG_FUNC_ENTRY_relationships(Node)
    for rel in entry_relationship:
        if rel in entry_relationship:
            if rel.start_node == Node:
                return rel.end_node
    return None

def get_PARENT_OF_relationship(Node):
    """
    提供一个Node结点, 返回和该node相关的 PARENT_OF Relationship list
    :param Node:
    :return:
    """
    return list(py2neo.RelationshipMatch(graph, nodes={Node}, r_type='PARENT_OF'))

def get_PARENT_OF_NODE(Node):
    """
    提供一个Node结点, 返回和该node相关的 PARENT_OF Relationship list
    :param Node:
    :return:
    """
    parent_of_rels_list = get_PARENT_OF_relationship(Node)
    for rel in parent_of_rels_list:
        if rel.end_node == Node:
            return rel.start_node
    return None

def get_AST_node_by_lineno(lineno):
    """
    提供lineno，返回AST 结点，有多个
    :param lineno:
    :return:
    """
    Node_list = list(graph.nodes.match("AST", lineno=lineno))
    return Node_list[0]

def get_Line_Root_Node(Node):
    """
    提供一个结点，找到该节点所在行中的根节点
    :param Node:
    :return:
    """
    if Node == None:
        print("[*] The Node is None.")
        return None
    if Node['lineno'] == None:
        print("[*] The attribute does not exists in Node.")
        return
    lineno = Node['lineno']
    while True:
        Parent_Node = get_PARENT_OF_NODE(Node)
        if Parent_Node['lineno'] == None:
            break
        if Parent_Node['lineno'] == lineno:
            Node = Parent_Node
        else:
            break
    return Node

def get_Child_Nodes(Node):
    """
    提供一个结点，通过PARENT_OF relationships来寻找该结点的child 结点，有多个
    :param Node:
    :return:
    """
    child_node_list = []
    parent_of_rels_list = get_PARENT_OF_relationship(Node)
    for rel in parent_of_rels_list:
        if rel.start_node == Node:
            if rel.end_node not in child_node_list:
                child_node_list.append(rel.end_node)
    child_node_list.sort(key=lambda node: node['id'], reverse=False)
    return child_node_list

def traverse_Child_Node_DFS(Node):
    """
    通过深搜DFS来确定当前Node结点或是子结点是否存在`$DB->request()`函数标志
    :param Node:
    :return:
    """
    if Node['code'] == 'DB' or Node['code'] == 'request':
        return True
    child_node_list = get_Child_Nodes(Node)
    for child_node in child_node_list:
        flag = traverse_Child_Node_DFS(child_node)
        if flag == True:
            return True
    return False

def traverse_Child_Node_BFS(Node):
    """
    通过广搜BFS来确定当前Node结点或是子结点是否存在`$DB->request()`函数标志
    :param Node:
    :return:
    """
    import queue

    que = queue.Queue()
    vis_nodes = []
    que.put(Node)
    while que.qsize() != 0:
        top_node = que.get()
        if top_node not in vis_nodes:
          vis_nodes.append(top_node)
        if top_node['code'] == 'DB' or top_node['code'] == 'request':
            return True
        child_node_list = get_Child_Nodes(top_node)
        for child_node in child_node_list:
            if child_node in vis_nodes:
                continue
            que.put(child_node)
            vis_nodes.append(child_node)
    return False


def get_Target_Child_Node(Node):
    """
    根据提供的根节点（即foreach结点），确定$DB->request($query)函数的根结点
    :param Node:
    :return:
    """
    child_node_list = get_Child_Nodes(Node)
    for child_node in child_node_list:
        flag = traverse_Child_Node_BFS(child_node)
        if flag == True:
            return child_node
    return None


def get_FLOWS_TO_relationship(Node):
    """
    提供一个Node结点, 返回和该node相关的 FLOWS_TO Relationship list
    :param Node:
    :return:
    """
    return list(py2neo.RelationshipMatch(graph, nodes={Node}, r_type='FLOWS_TO'))


def get_CFG_Child_Nodes_List(Node):
    """
    提供一个Node结点，找到Node结点在CFG图中的子结点，应存在多个
    :param Node:
    :return:
    """
    cfg_child_node_list = []
    cfg_flows_to_rels = get_FLOWS_TO_relationship(Node)
    for rel in cfg_flows_to_rels:
        if rel.start_node == Node:
            if rel.end_node not in cfg_child_node_list:
                cfg_child_node_list.append(rel.end_node)
    cfg_child_node_list.sort(key=lambda node: node['id'], reverse=False)
    return cfg_child_node_list


def print_CFG_PathList(PathList, CycleDict):
    """
    用于输出CFG路径，同时需要对循环涉及的路径进行特殊处理
    :param PathList:
    :param CycleDict:
    :return:
    : 存在循环的情况
    : PathList = [34, 36, 38, 40, 41, 41, 48, 49, 54, 55, 60, 61, 67, 69, 70, 72]
    : CycleDict = {41: [42, 43, 45]}
    要将后一个重复的41替换为[42, 43, 45]
    但是要注意，当前的PathList = [..., 41, 41, 48, ......]也是正确的CFG路径
    """
    print(PathList)

    flag = True # 判断是否经过了循环路径
    final_PathList = list(set(PathList))
    if len(final_PathList) == len(PathList):
        flag = False
    final_PathList.sort(key=PathList.index)
    for key in sorted(CycleDict.keys()):
        if key in final_PathList:
            idx = PathList.index(key)   # 确定后一个重复的lineno的位置，进行替换
            final_PathList[idx + 1:idx + 1] = iter(CycleDict[key])
    if flag == True:    # 如果没有经过循环，那么不用输出final_PathList，已经输出过PathList了
        print(final_PathList)


def get_CFG_Path_DFS(StartNode, EndNode, PathList=[], CycleDict={}):
    """
    通过深搜来寻找CFG路径，当遍历到结束结点的时候就进行一次路径输出
    :param StartNode: 遍历的起始Node结点
    :param EndNode: 遍历的结束Node结点
    :param PathList: 存储CFG路径
    :param CycleDict: CFG图中存在的循环路径，需要特殊处理
    :return:
    """
    PathList.append(StartNode['lineno'])
    if StartNode == EndNode:
        print_CFG_PathList(PathList, CycleDict)
    else:
        CFG_Child_Node_List = get_CFG_Child_Nodes_List(StartNode)
        for CFG_Child_Node in CFG_Child_Node_List:
            # 情况1：绝大多数情况下，CFG的当前结点lineno都不会小于其后续结点的lineno
            if CFG_Child_Node['lineno'] >= StartNode['lineno']:
                get_CFG_Path_DFS(CFG_Child_Node, EndNode, PathList, CycleDict)
            # 情况2：在出现循环的情况下，当结点对应循环中的最后一行语句时，其后续子结点会回到循环体的初始行，所以会出现lineno变小的情况
            else:
                # CFG_Child_Node['lineno'] < StartNode['lineno']
                # 举例：41 -> 42 -> 43 -> 45(child_lineno) -> 41
                child_lineno = CFG_Child_Node['lineno'] # 相当于上面的41
                i = 0
                while PathList[i] != child_lineno:
                    i = i + 1
                i = i + 1
                CycleDict[child_lineno] = PathList[i + 1:]
    PathList.pop()


if __name__ == "__main__":
    start_lineno = 1
    end_lineno = 72

    # 从文件的起始行，也就是第一个Node开始遍历
    start_node_type = "AST_TOPLEVEL"    # 文件第一行的AST Type为 AST_TOPLEVEL
    start_node = get_AST_node_by_type(start_node_type)

    # 确定CFG的入口结点
    cfg_entry_node = get_CFG_FUNC_ENTRY_node(start_node)
    # cfg_start_node = get_Child_Nodes(cfg_entry_node)[0]
    cfg_start_node = graph.nodes[5]
    print("[*] The Entry Node = ", cfg_start_node)


    # 确定第72行对应的Node结点
    temp_node = get_AST_node_by_lineno(end_lineno)
    temp_root_node = get_Line_Root_Node(temp_node)
    cfg_target_node = get_Target_Child_Node(temp_root_node)
    print("[*] The Target Node = ", cfg_target_node)

    get_CFG_Path_DFS(cfg_start_node, cfg_target_node)