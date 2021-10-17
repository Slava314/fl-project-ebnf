from antlr4 import *
from ebnfLexer import ebnfLexer
from ebnfVisitor import ebnfVisitor
from ebnfParser import ebnfParser
import sys
from pprint import pprint


import codecs
import sys

class TreeNode:
    text = ''
    def to_string(self, level):
         pass

class TextNode(TreeNode):
    rules = []

    def __init__(self, text, rules):
        self.text = text
        self.rules = rules

    # def add_rule(self, new_rule):
    #     self.rules.append(new_rule)

    def to_string(self, level):
        indent = level * 2
        indent *= ' '
        str = indent + 'rules:\n'
        for rule in self.rules:
            str += rule.to_string(level + 1)
        return str

class RuleNode(TreeNode):
    level = 0;
    subrules = []
    name = ''
    definition = TreeNode()

    def __init__(self, text, level, name, definition):
        self.text = text
        self.level = level
        self.name = name
        self.definition = definition

    def add_subrule(self, new_rule):
        self.subrules.append(new_rule)

    def to_string(self, level):
        indent = ''
        for i in range(level):
            indent += '  '
        str1 = indent + 'name: ' + str(self.name) + '\n'
        str1 += indent + 'subrules:\n'
        for rule in self.subrules:
            str1 += rule.to_string(level + 1)
        str1 += indent + 'definiton:\n' + self.definition.to_string(level + 1) + '\n'
        return str1


class StarNode(TreeNode):
    expr = TreeNode()

    def __init__(self, text, expr):
        self.text = text
        self.expr = expr

    def to_string(self, level):
        indent = level * 2
        indent *= ' '
        str = indent + 'expression:\n'
        str += self.expr.to_string(level + 1) + '\n'
        return str

class OptNode(TreeNode):
    expr = TreeNode()

    def __init__(self, text, expr):
        self.text = text
        self.expr = expr

    def to_string(self, level):
        indent = level * 2
        indent *= ' '
        str = indent + 'expression:\n'
        str += self.expr.to_string(level + 1) + '\n'
        return str

class AltNode(TreeNode):
    left = TreeNode()
    right = TreeNode()

    def __init__(self, text, left, right):
        self.text = text
        self.left = left
        self.right = right

    def to_string(self, level):
        indent = level * 2
        indent *= ' '
        str = indent + 'left:\n'
        str += self.left.to_string(level + 1) + '\n'
        str += indent + 'right:\n'
        str += self.right.to_string(level + 1) + '\n'
        return str

class ConcatNode(TreeNode):
    left = TreeNode()
    right = TreeNode()

    def __init__(self, text, left, right):
        self.text = text
        self.left = left
        self.right = right

    def to_string(self, level):
        indent = level * 2
        indent *= ' '
        str = indent + 'left:\n'
        str += self.left.to_string(level + 1) + '\n'
        str += indent + 'right:\n'
        str += self.right.to_string(level + 1) + '\n'
        return str

class AtomNode(TreeNode):
    def __init__(self, text):
        self.text = text

    def to_string(self, level):
        indent = level * 2
        indent *= ' '
        str = indent + self.text + '\n'
        return str



class EvalVisitor(ebnfVisitor):

    def visitStart(self, ctx):
        return TextNode(ctx.text, self.visitChildren(ctx))

    def visitRuleText(self, ctx):
        lst = []
        level = 0
        if not ctx.indent is None:
            level = len(ctx.indent) / 2
        left = RuleNode(ctx.text, level, ctx.name.text, self.visit(ctx.left))
        right = self.visit(ctx.right)
        right.append(left)
        return right;

    def visitEndText(self, ctx):
        return []

    def visitStarExpr(self, ctx):
        return OptNode(ctx.text, self.visit(ctx.expr))

    def visitAltExpr(self, ctx):
        left = self.visit(ctx.left)
        right = self.visit(ctx.right)
        return ConcatNode(ctx.text, left, right)

    def visitAtomExpr(self, ctx):
        return AtomNode(ctx.getText())

    # def visitParenExpr(self, ctx):
    #     print("visitParenExpr",ctx.getText())
    #     return self.visitChildren(ctx)

    def visitOptExpr(self, ctx):
        return OptNode(ctx.text, self.visit(ctx.expr))

    def visitConcatExpr(self, ctx):
        left = self.visit(ctx.left)
        right = self.visit(ctx.right)
        return ConcatNode(ctx.text, left, right)

    
def main():
    with open(sys.argv[1]) as file:
        lexer = ebnfLexer(InputStream(file.read()))
        stream = CommonTokenStream(lexer)
        parser = ebnfParser(stream)
        tree = parser.start()
        print(EvalVisitor().visit(tree).to_string(0))
        
    

if __name__ == '__main__':
    main()
