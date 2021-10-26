/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */
import {
	createConnection,
	TextDocuments,
	Diagnostic,
	DiagnosticSeverity,
	ProposedFeatures,
	InitializeParams,
	DidChangeConfigurationNotification,
	CompletionItem,
	CompletionItemKind,
	TextDocumentPositionParams,
	TextDocumentSyncKind,
	InitializeResult,
    CodeAction,
    WorkspaceEdit
} from 'vscode-languageserver/node';

import {CharStreams, CommonTokenStream, Token} from "antlr4ts";
import {CodeCompletionCore, ScopedSymbol, SymbolTable, VariableSymbol} from "antlr4-c3";

import {
	TextDocument,
    TextEdit
} from 'vscode-languageserver-textdocument';
import {ebnfLexer} from "./antlr/ebnfLexer";
import {ebnfParser} from "./antlr/ebnfParser";
import { computeTokenPosition } from './compute-token-position';
import { throws } from 'assert';

// Create a connection for the server, using Node's IPC as a transport.
// Also include all preview / proposed LSP features.
const connection = createConnection(ProposedFeatures.all);

// Create a simple text document manager.
const documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

let hasConfigurationCapability = false;
let hasWorkspaceFolderCapability = false;
let hasDiagnosticRelatedInformationCapability = false;

connection.onInitialize((params: InitializeParams) => {
	const capabilities = params.capabilities;

	// Does the client support the `workspace/configuration` request?
	// If not, we fall back using global settings.
	hasConfigurationCapability = !!(
		capabilities.workspace && !!capabilities.workspace.configuration
	);
	hasWorkspaceFolderCapability = !!(
		capabilities.workspace && !!capabilities.workspace.workspaceFolders
	);
	hasDiagnosticRelatedInformationCapability = !!(
		capabilities.textDocument &&
		capabilities.textDocument.publishDiagnostics &&
		capabilities.textDocument.publishDiagnostics.relatedInformation
	);

	const result: InitializeResult = {
		capabilities: {
			textDocumentSync: TextDocumentSyncKind.Incremental,
			// Tell the client that this server supports code completion.
			completionProvider: {
				resolveProvider: true
			}
		}
	};
	if (hasWorkspaceFolderCapability) {
		result.capabilities.workspace = {
			workspaceFolders: {
				supported: true
			}
		};
	}
	return result;
});

connection.onInitialized(() => {
	if (hasConfigurationCapability) {
		// Register for all configuration changes.
		connection.client.register(DidChangeConfigurationNotification.type, undefined);
	}
	if (hasWorkspaceFolderCapability) {
		connection.workspace.onDidChangeWorkspaceFolders(_event => {
			connection.console.log('Workspace folder change event received.');
		});
	}
});

// The example settings
interface ExampleSettings {
	maxNumberOfProblems: number;
}

// The global settings, used when the `workspace/configuration` request is not supported by the client.
// Please note that this is not the case when using this server with the client provided in this example
// but could happen with other clients.
const defaultSettings: ExampleSettings = { maxNumberOfProblems: 1000 };
let globalSettings: ExampleSettings = defaultSettings;

// Cache the settings of all open documents
const documentSettings: Map<string, Thenable<ExampleSettings>> = new Map();

connection.onDidChangeConfiguration(change => {
	if (hasConfigurationCapability) {
		// Reset all cached document settings
		documentSettings.clear();
	} else {
		globalSettings = <ExampleSettings>(
			(change.settings.languageServerExample || defaultSettings)
		);
	}

	// Revalidate all open text documents
	documents.all().forEach(validateTextDocument);
});

function getDocumentSettings(resource: string): Thenable<ExampleSettings> {
	if (!hasConfigurationCapability) {
		return Promise.resolve(globalSettings);
	}
	let result = documentSettings.get(resource);
	if (!result) {
		result = connection.workspace.getConfiguration({
			scopeUri: resource,
			section: 'languageServerExample'
		});
		documentSettings.set(resource, result);
	}
	return result;
}

// Only keep settings for open documents
documents.onDidClose(e => {
	documentSettings.delete(e.document.uri);
});

// The content of a text document has changed. This event is emitted
// when the text document first opened or when its content has changed.
documents.onDidChangeContent(change => {
	validateTextDocument(change.document);
});

async function validateTextDocument(_textDocumentPosition: TextDocumentPositionParams): Promise<void> {
	// In this simple example we get the settings for every validate run.
	const settings = await getDocumentSettings(_textDocumentPosition.uri);

	// The validator creates diagnostics for all uppercase words length 2 and more
	const text = _textDocumentPosition.getText();
    const t = documents.get(_textDocumentPosition.uri)?.getText() || "";
    const input = CharStreams.fromString(t);
    const lexer = new ebnfLexer(input);
    const tokenStream = new CommonTokenStream(lexer);
    const parser = new ebnfParser(tokenStream);
    parser.start();
    const core = new CodeCompletionCore(parser);
	let ts = tokenStream.getTokens();
	const rules = [];
	const diagnostics: Diagnostic[] = [];

    const pos = _textDocumentPosition.position;
	let tok = 0;
	for(let i=0;i<ts.length;i++){
		if(ts[i].line < pos.line){
			tok=i;
		} else {
			if(ts[i].line == pos.line && ts[i].charPositionInLine < pos.character){
			tok=i;
			}
		}
	}
	let ts_copy_save = ts;

	let level_counter: number | undefined;
	level_counter = 0;
	

	for(let i=tok;i>=0;i--){
		if(ts[i].line == pos.line && ts[i].type == ebnfLexer.SP_M && ts[i].text!=undefined) {
			level_counter = ts[i].text?.length;
		}
	}

	const ar = ts_copy_save.splice(0, tok);
	ts_copy_save = ar;
	

	const new_ts : Token[] = [];

	if(level_counter == 0){
		for(let i = 0; i < tok; i++){
			let sec_pos = i;
			if(ts_copy_save[i].type == ebnfLexer.WORD && ts_copy_save[i-1].type == ebnfLexer.NEW_L){
				while(ts_copy_save[sec_pos] != ebnfLexer.NEW_L) sec_pos++;
			}
			const needed_line = ts_copy_save.splice(i-1, sec_pos - i + 1);
			new_ts.concat(needed_line);
		}
	} else {
		for(let i = 0; i < tok; i++){
			let sec_pos = i;
			if(ts_copy_save[i].type == ebnfLexer.WORD && ts_copy_save[i-1].type == ebnfLexer.SP_M && level_counter != undefined && ts_copy_save[i].text?.length == level_counter){
				while(ts_copy_save[sec_pos] != ebnfLexer.NEW_L) sec_pos++;
			}
			const needed_line = ts_copy_save.splice(i-2, sec_pos - i + 2);
			new_ts.concat(needed_line);
		}
	}

	ts = new_ts;


	for(let i=0;i<ts.length;i++){
		if(ts[i].type==ebnfLexer.WORD){
			if(ts[i-1].type==ebnfLexer.SP_N && ts[i-1].text?.length == level_counter){
				rules.push(ts[i].text);
				console.log(ts[i].text);
			} else if(ts[i-1].type==ebnfLexer.NEW_L && level_counter == 0){
				rules.push(ts[i].text);
				console.log(ts[i].text);
			} else if(ts[i+1].type==ebnfLexer.SP_N && rules.indexOf( ts[i].text ) == -1 ){
				const diagnostic: Diagnostic = {
					range: {
						start: TextDocumentPositionParams.positionAt(ts[i].startIndex),
						end: TextDocumentPositionParams.positionAt(ts[i].stopIndex)
					},
					message: `there is no such rule with identificator: `+ts[i].text,
				};
				diagnostics.push(diagnostic);
			}
		}
	}

	// Send the computed diagnostics to VSCode.
	connection.sendDiagnostics({ uri: TextDocumentPositionParams.uri, diagnostics });
    
}

connection.onDidChangeWatchedFiles(_change => {
	// Monitored files have change in VSCode
	connection.console.log('We received an file change event');
});

// This handler provides the initial list of the completion items.
connection.onCompletion(
	(_textDocumentPosition: TextDocumentPositionParams): CompletionItem[] => {
		// The pass parameter contains the position of the text document in
		// which code complete got requested. For the example we ignore this
		// info and always provide the same completion items.

    const t = documents.get(_textDocumentPosition.textDocument.uri)?.getText() || "";
    const input = CharStreams.fromString(t);
    const lexer = new ebnfLexer(input);
    const tokenStream = new CommonTokenStream(lexer);
    const parser = new ebnfParser(tokenStream);
	
    const parseTree = parser.start();
    parser.start();
    const core = new CodeCompletionCore(parser);

    const pos = _textDocumentPosition.position;
    const tokens:string[] = [];
    
    const keywords: string[] = [];
    
	const ts = tokenStream.getTokens();
	const rules = [];
	let tok = 0;
	for(let i=0;i<ts.length;i++){
		if(ts[i].line < pos.line){
			tok=i;
		} else {
			if(ts[i].line == pos.line && ts[i].charPositionInLine < pos.character){
			tok=i;
			}
		}
	}

	// let myMap = new Map();
	// myMap.set( (ts[0].type, 0), 1);
	const candidates = core.collectCandidates(tok);
	const sugg: CompletionItem[] = [];
	let level_counter: number | undefined;
	level_counter = 0;
	for(let i=tok;i>=0;i--){
		if(ts[i].line == pos.line && ts[i].type == ebnfLexer.SP_M && ts[i].text!=undefined) {
			level_counter = ts[i].text?.length;
		}
	}


	for(let i=0;i<=tok;i++){
		if(ts[i].line < pos.line){
			let SP_M__counter: number | undefined;
			SP_M__counter = 0;
			if(ts[i-1].type == ebnfLexer.SP_M && ts[i-1].text!=undefined){
				SP_M__counter = ts[i].text?.length;
				if(SP_M__counter == level_counter){
					if(ts[i].text == ebnfLexer.WORD){
						rules.push(ts[i].text);
						console.log(ts[i].text+" :"+ts[i].line+ " : "+ts[i].charPositionInLine);
					}
				}
			} else if(level_counter == 0 && ts[i].type == ebnfLexer.WORD){
				rules.push(ts[i].text);
						console.log(ts[i].text+" :"+ts[i].line+ " : "+ts[i].charPositionInLine);
			}
			if(ts[i-1].type == ebnfLexer.NEW_L){
				while(ts[i-1].type == ebnfLexer.NEW_L){
					i++;
				}

			}
		}
	}


	for (const candidate of candidates.tokens) {
		console.log(parser.vocabulary.getSymbolicName(candidate[0]));
		if(parser.vocabulary.getSymbolicName(candidate[0])=="WORD"){
			rules.forEach(n => {
				if(n!=undefined)
				sugg.push({
					label: n,
					kind: CompletionItemKind.Value
				});

		});
		}
	}

	console.log("pos_l:"+pos.line+" pos_c:"+pos.character);

		const tokenReg = /(?:[()[\]:]|['\w])+/g;

		const text = documents.get(_textDocumentPosition.textDocument.uri)?.getText() || "";
		const lines = text.split(/\r\n|\r|\n/);

		const line = lines[_textDocumentPosition.position.line];

		return sugg;

	}
);


// This handler resolves additional information for the item selected in
// the completion list.
connection.onCompletionResolve((item: CompletionItem): CompletionItem => {
    return item;
}
);


// Make the text document manager listen on the connection
// for open, change and close text document events
documents.listen(connection);

// Listen on the connection
connection.listen();
