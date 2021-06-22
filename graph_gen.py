from pycparser import parse_file
from graphviz import Digraph
from graphviz import escape
import os

class AstNode:
    def __init__(self, gid, code=None, connectTo=None, child=None, d=None, u=None, isStart=False, isEnd=False):
        """
        AsrNode 保存形式

        :param gid: 节点编号 int
        :param code: 代码片段 [str]
        :param connectTo: 节点标号 [int]
        :param child: 代码块包含内容 [AstNode]
        :param d: 变量定义 [str]
        :param u: 变量使用 [str]
        :param isStart: 开始节点 Bool
        :param isEnd: 终止节点 Bool
        """
        self.id = gid
        self.code = code if code is not None else []
        self.connectTo = connectTo if connectTo is not None else []
        self.child = child if child is not None else []
        self.d = d if d is not None else []
        self.u = u if u is not None else []
        self.isStart = isStart
        self.isEnd = isEnd
        # self.attr = ('id', 'code', 'connectTo', 'child', 'd', 'u', 'isStart', 'isEnd')
        self.attr = ('id', 'code', 'connectTo', 'd', 'u')

    def show(self):
        d = list(set(self.d))
        u = list(set(self.u))
        string = "\n".join(self.code)
        string += "\n##############"
        string += "\nid: " + str(self.id)
        string += "\nd: "
        string += ', '.join(d) if len(d) > 0 else "None"
        string += "\nu: "
        string += ', '.join(u) if len(u) > 0 else "None"
        return string

    def __str__(self):
        string = "##############\n"
        for each in self.attr:
            string += "%s: %s\n" % (each, str(getattr(self, each)))
        return string

## 废弃类 ##
class ConditionNode(AstNode):
    def __init__(self, gid, code=None, connectTo=None, d=None, u=None, cond=None):
        """
        和AstNode不同的是，有条件控制语句执行方向

        :param cond: {'case条件'/'ifTrue'/'ifFalse': AstNode}
        """
        super(ConditionNode, self).__init__(gid, code, connectTo=connectTo, d=d, u=u)

        self.cond = cond if cond is not None else {}
        self.attr = ('id', 'code', 'connectTo', 'd', 'u', 'cond')


class Graph:
    def __init__(self, ast, name="c"):
        """
        通过ast建立图，列表存储，并记录变量的du情况
        g: [AstNode] 全局变量、方法或typedef
        du_path: [{global_var: [[id,'d'/'u'], ...]}, {}] 变量声明和使用（一个字典表示一个AstNode节点）

        :param ast: pycpaser Ast部分语句节点
        :param name: 图名称
        """
        self.node_num = 0
        self.g = None
        self.du_path = None
        self.dot = None
        self.name = name
        self.build(ast)
        if self.g is not None:
            self.travel_dupath()
            for graph in self.g:
                self.travel_graph(graph)
            self.dot.render(os.path.join('tmp', self.name), view=True)

    def travel_path(self, path):
        tmp = []
        for each in path:
            name = each[0].__class__.__name__
            if name == 'int':
                tmp.append('%d|%s' % (each[0], each[1]))
            else:
                # 嵌套列表 或 元组
                name = each.__class__.__name__
                if name == 'tuple':
                    tmp.append('( %s )' % self.travel_path(each))
                else:
                    tmp.append('[ %s ]' % self.travel_path(each))

        return '-> '.join(tmp)

    def travel_dupath(self):
        for i in range(len(self.du_path)):
            print('=======图%d dupath=======' % i)
            for k, v in self.du_path[i].items():
                print("%s:\t\t%s" % (k, self.travel_path(v)))
            print()

    def travel_graph(self, node):
        if node.isStart is True:
            self.dot.attr('node', shape="doublecircle")
        if node.isEnd is True:
            self.dot.attr('node', shape="box")
        if node.id != -1:
            self.dot.node(str(node.id), escape(node.show()))
        self.dot.attr('node', shape="ellipse")

        # if节点画true false
        if len(node.child) == 2 and node.child[0].id == -1:
            for c in node.child:
                for c_stmt in c.child:
                    if len(c_stmt.code) == 0:
                        continue
                    self.travel_graph(c_stmt)
            self.dot.edge(str(node.id), str(node.connectTo[0]), "True")
            self.dot.edge(str(node.id), str(node.connectTo[1]), "False")
        else:
            # 递归
            for each in node.child:
                self.travel_graph(each)
            # 画连接线
            for connect in node.connectTo:
                self.dot.edge(str(node.id), str(connect))


    def getDeclTypeAttr(self, typeNode):
        node_name = typeNode.__class__.__name__
        # FuncDecl 不做考虑
        # TypeDecl->type:IdentifierType
        if node_name == 'TypeDecl':
            string = self.getDeclTypeAttr(typeNode.type)
            if typeNode.declname is not None:
                string += ' ' + typeNode.declname
            return string
        # PtrDecl->type:TypeDecl->type:IdentifierType
        elif node_name == 'PtrDecl':
            string = self.getDeclTypeAttr(typeNode.type)
            string = string.split(' ')
            string[-1] = '*' + string[-1]
            string = ' '.join(string)
            return string
        elif node_name == 'ArrayDecl':
            string = self.getDeclTypeAttr(typeNode.type)
            if typeNode.dim is None:
                string += '[]'
            else:
                string += '[%s]' % typeNode.dim.value
            return string
        elif node_name == 'IdentifierType':
            return ' '.join(typeNode.names)
        elif node_name == 'Typename':
            return ' '.join(typeNode.quals) + self.getDeclTypeAttr(typeNode.type)
        elif node_name == 'Struct':
            string = "struct %s{" % typeNode.name
            strings = []
            # 结构体中的d和u暂不考虑
            for each_decl in typeNode.decls:
                inner_str, _, _ = self.getDecl_DU(each_decl)
                strings.append(inner_str)
            string += '; '.join(strings) + '}'
            return string
        else:
            print('未处理的Decl的type属性')
            print(typeNode)
            return ''

    def getComputeStatement_U(self, node):
        """
        UnaryOp(* &也算), BinaryOp, TernaryOp, ArrayRef, Constant, Cast, InitList, ID, None

        :param node: 节点或空节点
        :return: codeStr 和数组 u
        """
        node_name = node.__class__.__name__
        string = ""
        u = []
        if node_name == 'UnaryOp':
            inner_str, u = self.getComputeStatement_U(node.expr)
            if node.op == "p++":
                string = inner_str + "++"
            else:
                string = node.op + inner_str
        elif node_name == 'BinaryOp':
            left_str, left_u = self.getComputeStatement_U(node.left)
            right_str, right_u = self.getComputeStatement_U(node.right)
            string = left_str + ' %s ' % node.op + right_str
            u = left_u + right_u
        elif node_name == 'TernaryOp':
            cond_str, cond_u = self.getComputeStatement_U(node.cond)
            true_str, true_u = self.getComputeStatement_U(node.iftrue)
            false_str, false_u = self.getComputeStatement_U(node.iffalse)
            u = cond_u + true_u + false_u
            string = "%s ? %s : %s" % (cond_str, true_str, false_str)
        elif node_name == 'ArrayRef':
            name_str, name_u = self.getComputeStatement_U(node.name)
            sub_str, sub_u = self.getComputeStatement_U(node.subscript)
            u = name_u + sub_u
            string = "%s[%s]" % (name_str, sub_str)
        elif node_name == 'Constant':
            string = node.value
        elif node_name == 'Cast':
            expr_string, u = self.getComputeStatement_U(node.expr)
            # 处理Cast的typename
            string = "(%s)%s" % (self.getDeclTypeAttr(node.to_type), expr_string)
        elif node_name == 'InitList':
            string = []
            for eachNode in node.exprs:
                inner_str, inner_u = self.getComputeStatement_U(eachNode)
                string.append(inner_str)
                u += inner_u
            string = "{" + ", ".join(string) + "}"
        elif node_name == 'ID':
            string = node.name
            u = [node.name]
        elif node_name == 'NoneType':
            pass
        else:
            print("未处理的表达式类型")
            print(node)
        return string, u

    def getDecl_DU(self, declNode):
        # typedef如果没有声明值，就是None
        d = [declNode.name] if declNode.name is not None else []
        string = ' '.join(declNode.storage) + ' ' if len(declNode.storage) != 0 else ''
        string += ' '.join(declNode.quals) + ' ' if len(declNode.quals) != 0 else ''
        string += self.getDeclTypeAttr(declNode.type)
        init_str, u = self.getComputeStatement_U(declNode.init)
        if init_str != '':
            string += ' = ' + init_str
        return string, d, u


    def getParamList_DU(self, ParamList):
        string = []
        d = []
        u = []
        if ParamList is None:
            return '()', d, u
        for each in ParamList.params:
            each_str, each_d, each_u = self.getDecl_DU(each)
            string.append(each_str)
            d += each_d
            u += each_u
        return '(' + ', '.join(string) + ')', d, u

    def build_decl(self, nodeList):
        """
        建立全局变量的节点，并直接添加g和dupath

        :param nodeList: [Node] pycparser全区变量节点
        :return: None
        """
        string = []
        d = []
        u = []
        n = AstNode(self.node_num)
        self.node_num += 1
        for eachNode in nodeList:
            inner_str, inner_d, inner_u = self.getDecl_DU(eachNode)
            string.append(inner_str)
            d += inner_d
            u += inner_u
        # 完善节点
        n.code = string
        n.d = d
        n.u = u
        # 完善du路径
        dupath = self.combine_du_to_dict(n.id, d=n.d, u=n.u)
        # 添加到图
        self.g.append(n)
        self.du_path.append(dupath)

    def build_typedef(self, nodeList):
        """
        建立全局下typedef的节点，并直接添加g和dupath

        :param nodeList: [Node] pycparser全局类型定义节点
        :return: None
        """
        n = AstNode(self.node_num)
        self.node_num += 1
        for each_typedef in nodeList:
            n.d.append(each_typedef.name)
            string = ' '.join(each_typedef.storage) + ' ' if len(each_typedef.storage) != 0 else ''
            string += ' '.join(each_typedef.quals) + ' ' if len(each_typedef.quals) != 0 else ''
            string += self.getDeclTypeAttr(each_typedef.type)
            n.code.append(string)

        dupath = self.combine_du_to_dict(n.id, d=n.d, u=n.u)
        # 更新到图
        self.g.append(n)
        self.du_path.append(dupath)

    def build_statement(self, nodeList, astn):
        """
        完善普通statement节点的 code, d, u

        :param nodeList: [pycparser Node] 为每一个statement生成语句
        :param astn: 可以是AstNode节点
        :return: astn, dupath
        """
        # 简单语句间不会影响，所以可以从前向后计算
        for pycNode in nodeList:
            node_name = pycNode.__class__.__name__
            string = ""
            d = []
            u = []
            if node_name == "Decl":
                string, d, u = self.getDecl_DU(pycNode)
            elif node_name == "Assignment":
                l_str, l_d = self.getComputeStatement_U(pycNode.lvalue)
                # 总会有人嵌套Assignment
                if pycNode.rvalue.__class__.__name__ == "Assignment":
                    tmpNode = AstNode(-1)
                    tmpNode, _= self.build_statement([pycNode.rvalue], tmpNode)
                    r_str = tmpNode.code[0]
                    r_u = tmpNode.u
                else:
                    r_str, r_u = self.getComputeStatement_U(pycNode.rvalue)
                d = [l_d[0]] if len(l_d) > 0 else []
                u = l_d[1:] if len(l_d) > 1 else []
                u += r_u
                string = l_str + ' ' + pycNode.op + ' ' + r_str
            elif node_name == "FuncCall":
                string, _ = self.getComputeStatement_U(pycNode.name)
                exprlist = pycNode.args.exprs
                strings = []
                for expr in exprlist:
                    expr_str, expr_u = self.getComputeStatement_U(expr)
                    u += expr_u
                    strings.append(expr_str)
                string += '(' + ', '.join(strings) + ')'
            elif node_name == "EmptyStatement":
                pass
            elif node_name in ('UnaryOp', 'BinaryOp', 'TernaryOp'):
                string, u = self.getComputeStatement_U(pycNode)
            else:
                print('未处理的statement')
                print(pycNode)
            # 保存数据，还原dupath
            astn.code.append(string)
            astn.d += d
            astn.u += u

        # 计算du路径
        dupath = self.combine_du_to_dict(astn.id, d=d, u=u)

        return astn, dupath

    def build_nested_node(self, node, children, end, otherEnd=None, returnEnd=None, continueEnd=None):
        """
        建立带有内部嵌套节点的 child属性 （这里忽略Goto、Label）

        :param node: AstNode对象
        :param children: AstNode对象的孩子节点
        :param end: AstNode的终止节点（普通statement）
        :param otherEnd: Case或While等节点的break指向节点，判断优先级高于end（AstNode对象）
        :param returnEnd: Return节点只想节点（AstNode对象）
        :param continueEnd: 用于While等节点的continue指向节点
        :return node: AstNode 对象
        :return dupath: {var: [id, 'd'/'u'], ...} du-path
        """
        dupath = {}
        special_node_name = ('Switch', 'Case', 'Default', 'If', 'DoWhile',
                             'While', 'For', 'Break', 'Continue', 'Return')
        statement = []

        # 无子节点，添加空节点
        if children is None:
            n = AstNode(self.node_num, connectTo=[end.id])
            self.node_num += 1
            node.child.insert(0, n)
            return node, dupath

        for i in range(len(children)-1,-1,-1):
            nodename = children[i].__class__.__name__

            # 处理statement代码段
            if nodename in special_node_name and len(statement) > 0:
                n = AstNode(gid=self.node_num, connectTo=[end.id])
                self.node_num += 1
                # 完善子节点，并把节点添加到child，合并path
                n, path = self.build_statement(statement, n)
                node.child.insert(0, n)
                # 从后向前添加dupath，所以是dupath = path <- dupath
                dupath = self.combine_dupath(path, dupath)
                # 维护计算后的结果
                statement = []
                end = n

            # 1. Switch及其子节点
            if nodename == 'Switch':
                # 建立节点
                n = AstNode(self.node_num)
                self.node_num += 1
                # 获取switch条件，计算dupath
                cond_str, cond_u = self.getComputeStatement_U(children[i].cond)
                n.code = ['switch(%s)' % cond_str]
                n.u = cond_u
                switch_dupath = self.combine_du_to_dict(n.id, u=n.u)
                # 从后向前添加
                dupath = self.combine_dupath(switch_dupath, dupath)

                # 节点加入条件 和 子节点的dupath
                n, stmt_path = self.build_nested_node(n, children[i].stmt.block_items, end, otherEnd=end, returnEnd=returnEnd)
                # n.connectTo.insert(0, n.child[0].id) # switch不仅链接此节点

                # 添加多孩子节点
                dupath = self.combine_multiple_dupath(dupath, stmt_path)
                node.child.insert(0, n)
                # print(n.code, n.id, n.connectTo)
                # for each in n.child:
                #     print(each.code, each.id, each.connectTo)

            elif nodename == 'Case':
                # 父节点是 Switch（该节点不需要设置connectTo）
                n = AstNode(self.node_num)
                self.node_num += 1
                # 获取条件的字符串和u
                expr_str, expr_u = self.getComputeStatement_U(children[i].expr)
                n.code.append('case %s :' % expr_str)
                n.u = expr_u
                case_dupath = self.combine_du_to_dict(n.id, n.u)

                # 整理子节点，合并du路径
                n, stmt_dupath = self.build_nested_node(n, children[i].stmts, end, otherEnd, returnEnd)
                n.connectTo.append(n.child[0].id)
                # 添加
                case_dupath = self.combine_dupath(case_dupath, stmt_dupath)
                dupath = self.combine_same_kind_dupath(dupath, case_dupath)
                node.child.insert(0, n)
                node.connectTo.insert(0, n.id)
                # 更新end
                end = n.child[0]
                # print(n.code, n.id, n.connectTo)
                # for each in n.child:
                #     print(each.code, each.id, each.connectTo)

            elif nodename == 'Default':
                # 父节点是 Switch（该节点不需要设置connectTo）
                n = AstNode(self.node_num)
                self.node_num += 1
                # 添加条件
                n.code.append('default :')

                # 整理子节点，合并du路径
                n, default_dupath = self.build_nested_node(n, children[i].stmts, end, otherEnd, returnEnd)
                n.connectTo.append(n.child[0].id)
                # 添加
                dupath = self.combine_same_kind_dupath(dupath, default_dupath)
                node.child.insert(0, n)
                node.connectTo.insert(0, n.id)
                # 更新end
                end = n.child[0]
                # print(n.code, n.id, n.connectTo)
                # for each in n.child:
                #     print(each.code, each.id, each.connectTo)

            # 2. 条件节点
            elif nodename == 'If':
                # 该节点有iftrue和iffalse，两者可取：None, EmptyStatement, Compound, If
                n = AstNode(self.node_num)
                self.node_num += 1
                # 建立条件节点
                cond_str, cond_u = self.getComputeStatement_U(children[i].cond)
                n.code.append("if(%s)" % cond_str)
                n.u = cond_u
                # 先添加孩子的节点，再添加父节点的dupath
                cond_dupath = self.combine_du_to_dict(n.id, u=n.u)

                # 建立孩子节点    0: iftrue 1: iffalse if的child形式为 [AstNode1, AstNode2]
                if_child_dupath = {}
                child_list = [children[i].iftrue, children[i].iffalse]
                for each_child in child_list:
                    child_name = each_child.__class__.__name__
                    tmp = None
                    child_n = AstNode(-1)
                    if child_name == "Compound":
                        tmp = each_child.block_items
                    elif child_name != "NoneType":
                        tmp = [each_child]
                    child_n, child_dupath = self.build_nested_node(child_n, tmp, end, returnEnd=returnEnd)
                    if_child_dupath = self.combine_same_kind_dupath(if_child_dupath, child_dupath)
                    # 添加孩子节点
                    n.child.append(child_n)
                    if tmp is None:
                        n.connectTo.append(end.id)
                    else:
                        n.connectTo.append(child_n.child[0].id)
                dupath = self.combine_multiple_dupath(dupath, if_child_dupath)
                dupath = self.combine_dupath(cond_dupath, dupath)

                # 添加到主节点中
                node.child.insert(0, n)
                end = n
                # print(n.code, n.connectTo)
                # for e in n.child:
                #     for each in e.child:
                #         print(each.code, each.id, each.connectTo)

            # 作为普通表达式来看
            # elif nodename == 'TernaryOp':
            #     pass

            # 3. 循环节点
            elif nodename == 'DoWhile':
                # 建立节点，获取条件节点的u
                n = AstNode(self.node_num)
                self.node_num += 1
                cond_str, cond_u = self.getComputeStatement_U(children[i].cond)
                n.code = ["do{ ... } while(%s)" % cond_str]
                n.u = cond_u
                # 先添加到dupath中
                dowhile_dupath = self.combine_du_to_dict(n.id, u=n.u)
                dupath = self.combine_dupath(dowhile_dupath, dupath)

                # 该节点配置：connectTo: 0True 1False
                # 配置False节点
                n.connectTo.insert(0, end.id)
                # 扩充stmt子节点
                tmp = None
                if children[i].stmt.__class__.__name__ == "Compound":
                    tmp = children[i].stmt.block_items
                n, stmt_path = self.build_nested_node(n, tmp, n, end, returnEnd, n)
                # 配置True节点
                n.connectTo.insert(0, n.child[0].id)
                # 循环体dupath，先扩展成列表形式，再添加到主节点中
                stmt_dupath = self.combine_same_kind_dupath({},stmt_path)
                dupath = self.combine_dupath(stmt_dupath, dupath)

                # 维护
                node.child.insert(0, n)
                end = n.child[0]
                # print(n.code, n.id, n.connectTo)
                # for each in n.child:
                #     print(each.code, each.id, each.connectTo)

            elif nodename == 'While':
                n = AstNode(self.node_num, connectTo=[end.id])
                self.node_num += 1
                # 获取while的条件和u
                cond_str, cond_u = self.getComputeStatement_U(children[i].cond)
                n.code = ["while (%s)" % cond_str]
                n.u = cond_u
                # 后添加到dupath中
                while_dupath = self.combine_du_to_dict(n.id, u=n.u)

                # 获取节点信息
                tmp = None
                if children[i].stmt.__class__.__name__ == "Compound":
                    tmp = children[i].stmt.block_items
                n, stmt_path = self.build_nested_node(n, tmp, n, end, returnEnd, n)
                # 配置True节点
                n.connectTo.insert(0, n.child[0].id)
                # 循环体dupath，先扩展成列表形式，再添加到主节点中
                stmt_dupath = self.combine_same_kind_dupath({},stmt_path)
                dupath = self.combine_dupath(stmt_dupath, dupath)
                dupath = self.combine_dupath(while_dupath, dupath)

                # 维护
                node.child.insert(0, n)
                end = n # Dowhile不同之处
                # print(n.code, n.id, n.connectTo)
                # for each in n.child:
                #     print(each.code, each.id, each.connectTo)

            elif nodename == 'For':
                n = AstNode(self.node_num, connectTo=[end.id])
                self.node_num += 1
                init_str = ""
                cond_str = ""
                next_str = ""
                # For的init属性是DeclList或Assignment或None
                if children[i].init.__class__.__name__ == "DeclList":
                    strings = []
                    d = []
                    u = []
                    for each_decl in children[i].init.decls:
                        decl_str, decl_d, decl_u = self.getDecl_DU(each_decl)
                        strings.append(decl_str)
                        d += decl_d
                        u += decl_u
                    n.d = d
                    n.u = u
                    init_str = ", ".join(strings)
                elif children[i].init.__class__.__name__ == "Assignment":
                    tmpNode = AstNode(-1)
                    tmpNode, _ = self.build_statement([children[i].init], tmpNode)
                    init_str = tmpNode.code[0]
                    n.u = tmpNode.u
                # For的cond属性
                if children[i].cond is not None:
                    cond_str, cond_u = self.getComputeStatement_U(children[i].cond)
                    n.u += cond_u
                # For的next属性
                if children[i].next is not None:
                    next_str, next_u = self.getComputeStatement_U(children[i].next)
                    n.u += next_u
                n.code.append("for(%s;%s;%s)" % (init_str, cond_str, next_str))
                for_dupath = self.combine_du_to_dict(n.id, d=n.d, u=n.u)

                # 完善stmt孩子节点
                tmp = None
                stmt_name = children[i].stmt.__class__.__name__
                if stmt_name == "Compound":
                    tmp = children[i].stmt.block_items
                elif stmt_name != "NoneType":
                    tmp = [children[i].stmt]
                n, stmt_path = self.build_nested_node(n, tmp, n, end, returnEnd, n)

                n.connectTo.insert(0, n.child[0].id)
                # 循环体dupath，先扩展成列表形式，再添加到主节点中
                stmt_dupath = self.combine_same_kind_dupath({},stmt_path)
                dupath = self.combine_dupath(stmt_dupath, dupath)
                dupath = self.combine_dupath(for_dupath, dupath)
                # 维护节点
                node.child.insert(0, n)
                end = n
                # print(n.code, n.id, n.connectTo)
                # for each in n.child:
                #     print(each.code, each.id, each.connectTo)

            # 4. 特殊节点
            elif nodename == 'Break':
                n = AstNode(self.node_num, code=["break"])
                self.node_num += 1
                # otherEnd > end
                if otherEnd is not None:
                    n.connectTo.append(otherEnd.id)
                else:
                    n.connectTo.append(end.id)
                # 维护节点
                node.child.insert(0, n)
                end = n

            elif nodename == 'Continue':
                n = AstNode(self.node_num, code=["continue"], connectTo=[continueEnd.id])
                self.node_num += 1
                # 维护节点
                node.child.insert(0, n)
                end = n

            elif nodename == 'Return':
                n = AstNode(self.node_num, connectTo=[returnEnd.id])
                self.node_num += 1
                expr_str, expr_u = self.getComputeStatement_U(children[i].expr)
                n.u = expr_u
                n.code.append("return %s" % expr_str)
                # 维护节点
                return_dupath = self.combine_du_to_dict(n.id, u=n.u)
                dupath = self.combine_dupath(return_dupath, dupath)
                node.child.insert(0, n)
                end = n


            # 5. 普通的数据流节点
            else:
                statement.insert(0, children[i])

        # 维护循环结束后的节点
        if len(statement) > 0:
            n = AstNode(gid=self.node_num, connectTo=[end.id])
            self.node_num += 1
            # 完善子节点，并把节点添加到child，合并path
            n, path = self.build_statement(statement, n)
            node.child.insert(0, n)
            dupath = self.combine_dupath(path, dupath)

        # 如果child代码块为空，添加空节点
        if len(node.child) == 0:
            n = AstNode(self.node_num, connectTo=[end.id])
            self.node_num += 1
            node.child.insert(0, n)
        return node, dupath

    def combine_same_kind_dupath(self, dupath, kind):
        # 注意：这是把kind的属性值添加到dupath列表中
        for each_k in kind.keys():
            if each_k in dupath:
                dupath[each_k].insert(0, kind[each_k])
            else:
                dupath[each_k] = [kind[each_k]]
        return dupath

    def combine_multiple_dupath(self, dupath, child):
        for each_c in child.keys():
            if each_c in dupath:
                dupath[each_c].insert(0, tuple(child[each_c]))
            else:
                dupath[each_c] = [tuple(child[each_c])]
        return dupath

    def combine_du_to_dict(self, uid, d=[], u=[]):
        d = list(set(d))
        u = list(set(u))
        dic = {each_d: [[uid, 'd']] for each_d in d}
        for each_u in u:
            if each_u in dic:
                dic[each_u][0][1] = 'du'
            else:
                dic[each_u] = [[uid, 'u']]
        return dic


    def combine_dupath(self, p1, p2):
        # 把p2的列表合并到p1后面
        for key in p2.keys():
            if key in p1:
                p1[key].extend(p2[key])
                # for index in range(len(p2[key])-1, -1, -1):
                #     p1[key].insert(0, p2[key][index])
            else:
                p1[key] = p2[key]
        return p1

    def get_last_from_nested_node(self, n):
        first_c = n.child[0]
        # 判断是否是父节点后置节点（do-while）
        if first_c.id in n.connectTo:
            return n
        else:
            last_c = n.child[-1]
            # 如果该节点继续嵌套，递归查找
            if len(last_c.child) != 0:
                return self.get_last_from_nested_node(last_c)
            else:
                return last_c


    def build(self, node):
        nodeName = node.__class__.__name__
        if nodeName == 'FileAST':
            self.g = []
            self.du_path = []
            self.dot = Digraph(name=self.name)
            flag = 0
            decl = []
            typedef = []
            # funcdef = []
            for eachNode in node.ext:
                if eachNode.__class__.__name__ == "Decl":
                    # 如果存在连续的typedef声明，优先处理
                    if flag == 2:
                        self.build_typedef(typedef)
                        typedef = []
                    # 处理decl的连续标记
                    flag = 1
                    decl.append(eachNode)
                elif eachNode.__class__.__name__ == "Typedef":
                    # 如果存在连续的decl声明，优先处理
                    if flag == 1:
                        self.build_decl(decl)
                        decl = []
                    flag = 2
                    typedef.append(eachNode)
                elif eachNode.__class__.__name__ == "FuncDef":
                    if flag == 1:
                        self.build_decl(decl)
                        decl = []
                    elif flag == 2:
                        self.build_typedef(typedef)
                        typedef = []
                    flag = 0
                    self.build(eachNode)
            # 结尾控制
            if flag == 1:
                self.build_decl(decl)
            elif flag == 2:
                self.build_typedef(typedef)
        elif nodeName == "FuncDef":
            # 处理Decl节点下的 FuncDecl
            code = ''
            code += ' '.join(node.decl.storage) + ' ' if len(node.decl.storage) != 0 else '' + \
                    ' '.join(node.decl.quals) + ' ' if len(node.decl.quals) != 0 else ''

            funcdecl = node.decl.type
            code_str, d, u = self.getParamList_DU(funcdecl.args)
            code += self.getDeclTypeAttr(funcdecl.type) + ' ' + code_str

            # 建立节点，然后处理节点内部的Compound对象
            astn = AstNode(self.node_num, code=['Start', code], d=d, u=u, isStart=True)
            dupath = self.combine_du_to_dict(astn.id, d=d, u=u)
            self.node_num += 1

            # 先加入终止节点，再 从后往前生成节点信息
            astn.child.append(AstNode(self.node_num, code=['End'], isEnd=True))
            self.node_num += 1
            astn, path = self.build_nested_node(astn, node.body.block_items, astn.child[-1], returnEnd=astn.child[-1])
            astn.connectTo.insert(0, astn.child[0].id)
            dupath = self.combine_dupath(dupath, path)

            # print('go')
            # for each_node in astn.child:
            #     print('code', each_node.code, each_node.id, each_node.connectTo)
            #     print('d', each_node.d)
            #     print('u', each_node.u)

            # 最后将方法节点添加，加入du路径到图中
            self.g.append(astn)
            self.du_path.append(dupath)


def build_graph(path, name="test"):
    # 处理‘#include’标签
    with open(path, encoding='utf-8') as f:
        txt_list = f.readlines()
        txt = ''
        for each in txt_list:
            if each.find('#include') != -1 or each.find('using') == 0:
                continue
            elif each.find('//') != -1:
                txt += each[:each.find('//')] + '\n'
            else:
                txt += each
    with open('tmp/c_processfile.c', 'w', encoding='utf-8') as f:
        f.write(txt)
    ast = parse_file('tmp/c_processfile.c', use_cpp=True, cpp_path=r'C:\MinGW\bin\gcc.exe', cpp_args=['-E', r'-Iutils/fake_libc_include'])
    # ast.show()
    # print(ast)
    graph = Graph(ast, name)

    # dot = Digraph(name='test1', comment='t1')
    # dot.node('a','a1')
    # dot.edge('a','b','a1->b1')
    # dot.node('b','b1')
    # # dot.view()
    # dot.render('c_file.gv', view=True)

if __name__ == '__main__':
    build_graph(r'tmp/c_processfile.c')