import * as vscode from 'vscode';
import * as fs from "fs";

function readAIMap(workspaceRoot: string){
    const path = workspaceRoot + "/.aimap.json";
    if(fs.existsSync(path)){
        const text = fs.readFileSync(path, "utf8");
        return JSON.parse(text);
    } else {
        return {};
    }
}

export function activate(context: vscode.ExtensionContext) {
    
    // 1. Log to confirm the extension loaded
    console.log('AI Code Review extension is active');

    // 2. Register a listener for text document changes
    //    This is where suggestion detection will live
    const changeListener = vscode.workspace.onDidChangeTextDocument(event => {
        for(const change of event.contentChanges){
            if(change.text.includes('\n')){
                console.log("AI Suggestion in: ", event.document.fileName);
                console.log("Inserted Text: ", change.text);
            }
        }
    });

    // 3. Register the listener so VS Code cleans it up
    //    when the extension is deactivated
    context.subscriptions.push(changeListener);
}

export function deactivate() {
    // VS Code calls this when the extension is disabled or VS Code closes
    // cleanup logic will go here later
}