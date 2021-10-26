import {ebnfVisitor} from "./antlr/ebnfVisitor";
import {RoutineSymbol, ScopedSymbol, SymbolTable, VariableSymbol} from "antlr4-c3";
import {AbstractParseTreeVisitor, ParseTree} from "antlr4ts/tree";
import {} from "./antlr/ebnfParser";

export class SymbolTableVisitor extends AbstractParseTreeVisitor<SymbolTable> implements ebnfVisitor<SymbolTable> {
    constructor(
        protected readonly symbolTable = new SymbolTable("", {}),
        protected scope = symbolTable.addNewSymbolOfType(ScopedSymbol, undefined)) {
        super();
    }

    protected defaultResult(): SymbolTable {
        return this.symbolTable;
    }

    protected withScope<T>(tree: ParseTree, type: new (...args: any[]) => ScopedSymbol, args: any[], action: () => T): T {
        const scope = this.symbolTable.addNewSymbolOfType(type, this.scope, ...args);
        scope.context = tree;
        this.scope = scope;
        try {
            return action();
        } finally {
            this.scope = scope.parent as ScopedSymbol;
        }
    }

}