from antlr4 import *
from antlr4.error.ErrorListener import *
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
        self.rules.reverse()

    def fix_subrules(self):
        new_rules = []
        for rule in self.rules:
            if rule.level > 0:
                new_rules[-1].add_subrule(rule)
            else:
                new_rules.append(rule)
                new_rules[-1].subrules = []
        self.rules = new_rules
        for rule in self.rules:
            rule.fix_subrules()

    def check_errors(self):
        pass

    def to_string(self, level):
        indent = level * 2
        indent *= ' '
        str1 = ''
        i = 1
        for rule in self.rules:
            str1 += 'rule ' + str(i) + ':\n'
            str1 += rule.to_string(level + 1)
            str1 += '------------------\n'
            i += 1
        return str1

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
        self.subrules[-1].subrules = []


    def fix_subrules(self):
        new_rules = []
        for rule in self.subrules:
            if rule.level > self.level + 1:
                new_rules[-1].add_subrule(rule)
            else:
                new_rules.append(rule)
                new_rules[-1].subrules = []
        self.subrules = new_rules
        for rule in self.subrules:
            rule.fix_subrules()

    def to_string(self, level):
        indent = ''
        for i in range(level):
            indent += '  '
        str1 = indent + 'name: ' + str(self.name) + '\n'
        str1 += indent + 'subrules:\n'
        for rule in self.subrules:
            str1 += rule.to_string(level + 1)
        str1 += indent + 'definiton:\n' + self.definition.to_string(level + 1)
        return str1


class StarNode(TreeNode):
    expr = TreeNode()

    def __init__(self, text, expr):
        self.text = text
        self.expr = expr

    def to_string(self, level):
        indent = level * 2
        indent *= ' '
        str = indent + 'star expression:\n'
        str += self.expr.to_string(level + 1)
        return str

class OptNode(TreeNode):
    expr = TreeNode()

    def __init__(self, text, expr):
        self.text = text
        self.expr = expr

    def to_string(self, level):
        indent = level * 2
        indent *= ' '
        str = indent + 'optional expression:\n'
        str += self.expr.to_string(level + 1)
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
        str = indent + "alternative:\n"
        str += indent + 'left:\n'
        str += self.left.to_string(level + 1)
        str += indent + 'right:\n'
        str += self.right.to_string(level + 1)
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
        str = indent + "concatination:\n"
        str += indent + 'left:\n'
        str += self.left.to_string(level + 1)
        str += indent + 'right:\n'
        str += self.right.to_string(level + 1)
        return str

class AtomNode(TreeNode):
    def __init__(self, text):
        self.text = text

    def to_string(self, level):
        indent = level * 2
        indent *= ' '
        str = indent + self.text.strip() + '\n'
        return str


class MyErrorListener(ErrorListener):
    def __init__(self, fileName, inputFile):
        self.fileName = fileName
        self.inpFile = inputFile

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        strings = self.inpFile.splitlines()
        print("Error! Incorrect input in {}:{}:{}".format(self.fileName, str(line), str(column)))
        print("  " + strings[line - 1])
        print("  " + column * " " + "^")
        sys.exit(3)
    


class EvalVisitor(ebnfVisitor):

    def visitStart(self, ctx):
        return TextNode(ctx.getText(), self.visitChildren(ctx))

    def visitRuleText(self, ctx):
        lst = []
        level = 0
        if not ctx.indent is None:
            level = int(len(ctx.indent.text) / 2)
        rule_text = ctx.getText()
        rule_text = rule_text[:rule_text.find(';')]
        left = RuleNode(rule_text, level, ctx.name.text, self.visit(ctx.left))
        right = self.visit(ctx.right)
        right.append(left)
        return right;

    def visitEndText(self, ctx):
        return []

    def visitStarExpr(self, ctx):
        return StarNode(ctx.getText(), self.visit(ctx.left))

    def visitAltExpr(self, ctx):
        left = self.visit(ctx.left)
        right = self.visit(ctx.right)
        return AltNode(ctx.getText(), left, right)

    def visitAtomExpr(self, ctx):
        return AtomNode(ctx.getText())

    def visitParenExpr(self, ctx):
        return self.visit(ctx.left)

    def visitOptExpr(self, ctx):
        return OptNode(ctx.getText(), self.visit(ctx.left))

    def visitConcatExpr(self, ctx):
        left = self.visit(ctx.left)
        right = self.visit(ctx.right)
        return ConcatNode(ctx.getText(), left, right)

    
def main():
    with open('test.txt') as file:
        input = file.read()
        lexer = ebnfLexer(InputStream(input))
        lexer.removeErrorListeners()
        lexer.addErrorListener(MyErrorListener(sys.argv[1], input))
        stream = CommonTokenStream(lexer)
        parser = ebnfParser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(MyErrorListener(sys.argv[1], input))
        tree = parser.start()
        abs_tree = EvalVisitor().visit(tree)
        abs_tree.fix_subrules()
        # abs_tree.check_errors()
        print(abs_tree.to_string(0))
        
    

if __name__ == '__main__':
    main()
