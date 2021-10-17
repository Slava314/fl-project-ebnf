grammar ebnf;
    start: text ;

    text: indent=SP* name=WORD SP* '->' left=expr ENDL right=text #ruleText
          | END #endText
          ;

    expr: SP* STAR expr                         #starExpr
          | SP* OPT expr                          #optExpr
          | left=expr SP* ALT SP* right=expr           #altExpr
          | left=expr SP* CONCAT SP* right=expr       #concatExpr
          | '(' expr ')'                      #parenExpr
          | SP* s=atom SP*                          #atomExpr
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

    ENDL: ';' ;

    WS: [\t\r\n]+ -> skip ;

    END: 'EOF' ;