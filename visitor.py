from typing_extensions import ParamSpecArgs
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
    def ToString():
         pass

class TextNode(TreeNode):
    rules = []

    def __init__(self, text):
        self.text = text

    def add_rule(self, new_rule):
        self.rules.append(new_rule)

class RuleNode(TreeNode):
    level = 0;
    subrules = []
    name = ''
    definition = TreeNode()

    def __init__(self, text, level, name):
        self.text = text
        self.level = level
        self.name = name

    def add_subrule(self, new_rule):
        self.subrules.append(new_rule)


class StarNode(TreeNode):
    expr = TreeNode()

    def __init__(self, text, expr):
        self.text = text
        self.expr = expr

class OptNode(TreeNode):
    expr = TreeNode()

    def __init__(self, text, expr):
        self.text = text
        self.expr = expr

class AltNode(TreeNode):
    left = TreeNode()
    right = TreeNode()

    def __init__(self, text, left, right):
        self.text = text
        self.left = left
        self.right = right

class ConcatNode(TreeNode):
    left = TreeNode()
    right = TreeNode()

    def __init__(self, text, left, right):
        self.text = text
        self.left = left
        self.right = right


class EvalVisitor(ebnfVisitor):

    def visitStart(self, ctx):
        print("visitStart",ctx.getText())
        return self.visitChildren(ctx)

    def visitRuleText(self, ctx):
        print("visitRuleText",ctx.name.text)
        return self.visitChildren(ctx)

    def visitEndText(self, ctx):
        print("visitEndText",ctx.getText())

    def visitStarExpr(self, ctx):
        print("visitStarExpr",ctx.getText())
        return self.visitChildren(ctx)

    def visitAltExpr(self, ctx):
        print("visitAltExpr",ctx.getText())
        return self.visitChildren(ctx)

    def visitAtomExpr(self, ctx):
        print("visitAtomExpr",ctx.getText())

    def visitParenExpr(self, ctx):
        print("visitParenExpr",ctx.getText())
        return self.visitChildren(ctx)

    def visitOptExpr(self, ctx):
        print("visitOptExpr",ctx.getText())
        return self.visitChildren(ctx)

    def visitConcatExpr(self, ctx):
        print("visitConcatExpr",ctx.getText())
        return self.visitChildren(ctx)

    def visitWordAtom(self, ctx):
        print("visitWordAtom",ctx.getText())

    def visitChrAtom(self, ctx):
        print("visitChrAtom",ctx.getText())
    
def main():
    with open(sys.argv[1]) as file:
        lexer = ebnfLexer(InputStream(file.read()))
        stream = CommonTokenStream(lexer)
        parser = ebnfParser(stream)
        tree = parser.start()
        EvalVisitor().visit(tree) 
        
    

if __name__ == '__main__':
    main()
