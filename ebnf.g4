grammar ebnf;
    start: text ;

    text: indent=SP* WORD SP* '->' right=expr ENDL text #ruleExpr
          | EOF #endExpr
          ;

    expr:  left=expr ALT right=expr           #altExpr
          | left=expr CONCAT right=expr       #concatExpr
          | '(' expr ')'                      #parenExpr
          | STAR expr                         #starExpr
          | OPT expr                          #optExpr
          | atom                              #atomExpr
          ;

    atom: WORD #wordAtom
          | CHR #chrAtom
          ;

    BlockComment: '#{' .*? '}#' -> skip;

    LineComment: '#' ~ [\r\n]* -> skip;

    CHR: '"' [a-zA-Z0-9_ ] '"';

    ALT: '|' ;

    LP: '(' ;

    RP: ')' ;

    CONCAT: ',' ;

    STAR: '*' ;

    OPT: '?' ;

    WORD: [A-Za-z][a-zA-Z0-9_ ]*[^ ] ;

    SP: ' ' ;

    ENDL: ';\n' ;

    WS: [\t\r\n]+ -> skip ;

    END: 'EOF' ;