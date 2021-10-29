grammar ebnf;
    start: text ;

    text: indent=SP_M name=RULE SP* '->' left=expr ENDL SP* NEW_L* right=text #ruleText
          | name=RULE SP* '->' left=expr ENDL SP* NEW_L* right=text #ruleText
          | END #endText
          ;

    expr: SP* STAR left=expr                          #starExpr
          | SP* OPT left=expr                         #optExpr
          | left=expr SP* ALT SP* right=expr          #altExpr
          | left=expr SP* CONCAT SP* right=expr       #concatExpr
          | '(' left=expr ')'                         #parenExpr
          | SP* s=atom SP*                            #atomExpr
          ;

    atom: word=RULE   #ruleAtom
          | STR #strAtom
          | CHR  #chrAtom
          ;

    OpenBlockComment: ' '*'#{' -> channel(2);

    CloseBlockComment: '}#'' '* -> channel(2);

    LineComment: ' '*'%' ~ [\r\n]* -> skip;

    END: 'EOF' ;

    CHR: '"' [a-zA-Z0-9_ ] '"';

    STR: '"' [a-zA-Z0-9_ ]* '"' ;

    ALT: '|' ;

    LP: '(' ;

    RP: ')' ;

    CONCAT: ',' ;

    STAR: '*' ;

    OPT: '?' ;

    RULE: [a-zA-Z][a-zA-Z0-9_ ]*[a-zA-Z0-9_] ;

    SP: ' ' ;

    SP_M: ' '' '* ;

    ENDL: ';' ;

    NEW_L: [\r\n]+;

    WS: [\t]+ -> skip ;

    SYM: . -> channel(2);