from antlr4 import *
from antlr4.error.ErrorListener import *
from ebnfLexer import ebnfLexer
from ebnfVisitor import ebnfVisitor
from ebnfParser import ebnfParser
import sys
from pprint import pprint


import codecs
import sys


def print_error_msg(line, column, str1, msg = ''):
    print("Error! Incorrect input in line {}:{}".format(str(line), str(column)))
    print("  " + str1)
    print("  " + column * " " + "^")
    print(msg)


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
                if not new_rules:
                    print_error_msg(rule.indent_token.line, rule.indent_token.column, rule.text, msg='Wrong level of nesting')
                    sys.exit(1)
                new_rules[-1].add_subrule(rule)
            else:
                new_rules.append(rule)
                new_rules[-1].subrules = []
        self.rules = new_rules
        for rule in self.rules:
            rule.fix_subrules()

    def check_errors(self):
        previous_rules = []
        for rule in self.rules:
            subrules_names = rule.check_errors()
            rules_in_def = rule.definition.get_rules_from_expr()
            for used in rules_in_def:
                txt = used.text
                if not txt in subrules_names and not txt in previous_rules:
                    print_error_msg(used.line, used.column, rule.text, msg="This rule isn't defined")
                    sys.exit(1)
            previous_rules.append(rule.name)

    def to_string(self, level):
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
    indent_token = None

    def __init__(self, text, name, indent_token, definition):
        self.text = text
        self.indent_token = indent_token
        if self.indent_token:
            if len(self.indent_token.text) % 2 == 1:
                print_error_msg(self.indent_token.line, self.indent_token.column, text, msg='Wrong number of spaces')
                sys.exit(1)
            self.level = int(len(self.indent_token.text) / 2)
        self.name = name
        self.definition = definition

    def add_subrule(self, new_rule):
        self.subrules.append(new_rule)
        self.subrules[-1].subrules = []


    def fix_subrules(self):
        new_rules = []
        for rule in self.subrules:
            if rule.level > self.level + 1:
                if not new_rules:
                    print_error_msg(rule.indent_token.line, rule.indent_token.column, rule.text, msg='Wrong level of nesting')
                    sys.exit(1)
                new_rules[-1].add_subrule(rule)
            else:
                new_rules.append(rule)
                new_rules[-1].subrules = []
        self.subrules = new_rules
        for rule in self.subrules:
            rule.fix_subrules()

    def check_errors(self):
        previous_subrules = []
        subrules_names = []
        for rule in self.subrules:
            new_subrules_names = rule.check_errors()
            rules_in_def = rule.definition.get_rules_from_expr()
            for used in rules_in_def:
                txt = used.text
                if not txt in new_subrules_names and not txt in previous_subrules:
                    print_error_msg(used.line, used.column, rule.text, msg="This rule isn't defined")
                    sys.exit(1)
            previous_subrules.append(rule.name)
            subrules_names += new_subrules_names

        return previous_subrules + subrules_names

    def to_string(self, level):
        indent = '  ' * level
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

    def get_rules_from_expr(self):
        return self.expr.get_rules_from_expr()

    def to_string(self, level):
        indent = '  ' * level
        str = indent + 'star expression:\n'
        str += self.expr.to_string(level + 1)
        return str

class OptNode(TreeNode):
    expr = TreeNode()

    def __init__(self, text, expr):
        self.text = text
        self.expr = expr

    def get_rules_from_expr(self):
        return self.expr.get_rules_from_expr()

    def to_string(self, level):
        indent = '  ' * level
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

    def get_rules_from_expr(self):
        return self.left.get_rules_from_expr() + self.right.get_rules_from_expr()

    def to_string(self, level):
        indent = '  ' * level
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

    def get_rules_from_expr(self):
        return self.left.get_rules_from_expr() + self.right.get_rules_from_expr()

    def to_string(self, level):
        indent = '  ' * level
        str = indent + "concatination:\n"
        str += indent + 'left:\n'
        str += self.left.to_string(level + 1)
        str += indent + 'right:\n'
        str += self.right.to_string(level + 1)
        return str

class AtomNode(TreeNode):
    token = None
    def __init__(self, text, token):
        self.text = text
        self.token = token

    def get_rules_from_expr(self):
        if self.token:
            return [self.token.word]
        return []

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
        print_error_msg(line ,column, strings[line - 1])
        sys.exit(1)




class EvalVisitor(ebnfVisitor):

    def visitStart(self, ctx):
        return TextNode(ctx.getText(), self.visitChildren(ctx))

    def visitRuleText(self, ctx):
        rule_text = ctx.getText()
        rule_text = rule_text[:rule_text.find(';')]
        left = RuleNode(rule_text, ctx.name.text, ctx.indent, self.visit(ctx.left))
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
        return self.visit(ctx.s)
        
    def visitRuleAtom(self, ctx):
        return AtomNode(ctx.getText(), ctx)

    def visitChrAtom(self, ctx):
        return AtomNode(ctx.getText(), None)

    def visitStrAtom(self, ctx):
        return AtomNode(ctx.getText(), None)

    def visitParenExpr(self, ctx):
        return self.visit(ctx.left)

    def visitOptExpr(self, ctx):
        return OptNode(ctx.getText(), self.visit(ctx.left))

    def visitConcatExpr(self, ctx):
        left = self.visit(ctx.left)
        right = self.visit(ctx.right)
        return ConcatNode(ctx.getText(), left, right)

    
def main():

    if (len(sys.argv) == 1): 
        print("Error! No input file")
        sys.exit(1)
    try:
        with open(sys.argv[1], 'r') as f:
            input = f.read()
    except Exception:
        print("Can't open file {} for reading".format(sys.argv[1]))
        sys.exit(1)

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
    abs_tree.check_errors()
    print(abs_tree.to_string(0))
        
    

if __name__ == '__main__':
    main()
