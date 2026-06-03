import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    
    // 1. Log to confirm the extension loaded
    console.log('AI Code Review extension is active');

    // 2. Register a listener for text document changes
    //    This is where suggestion detection will live
    const changeListener = vscode.workspace.onDidChangeTextDocument(event => {
        // for now just log that a change happened
        // we'll fill in the real logic in the next task
        console.log('Document changed:', event.document.fileName);
    });

    // 3. Register the listener so VS Code cleans it up
    //    when the extension is deactivated
    context.subscriptions.push(changeListener);
}

export function deactivate() {
    // VS Code calls this when the extension is disabled or VS Code closes
    // cleanup logic will go here later
}