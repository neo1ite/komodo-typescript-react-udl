'use strict';

/*
 * TypeScript LanguageService bridge for Komodo 9 CodeIntel.
 *
 * Usage:
 *   node typescript-codeintel.js /path/to/typescript.js
 *
 * Request is JSON on stdin:
 *   {action, file, text, pos}
 *
 * Response is JSON on stdout.
 */

const fs = require('fs');
const path = require('path');

const tsPath = process.argv[2];
if (!tsPath) {
    process.stdout.write(JSON.stringify({error: 'typescript.js path is required'}));
    process.exit(2);
}

const ts = require(tsPath);

function readStdin() {
    return new Promise((resolve, reject) => {
        let data = '';
        process.stdin.setEncoding('utf8');
        process.stdin.on('data', chunk => { data += chunk; });
        process.stdin.on('end', () => {
            try { resolve(JSON.parse(data || '{}')); }
            catch (e) { reject(e); }
        });
        process.stdin.on('error', reject);
    });
}

function findConfig(fileName) {
    let dir = path.dirname(path.resolve(fileName));
    while (true) {
        const candidate = path.join(dir, 'tsconfig.json');
        if (fs.existsSync(candidate)) return candidate;
        const parent = path.dirname(dir);
        if (parent === dir) return null;
        dir = parent;
    }
}

function parseProject(fileName) {
    const config = findConfig(fileName);
    if (!config) {
        return {
            fileNames: [path.resolve(fileName)],
            options: {
                allowJs: true,
                allowSyntheticDefaultImports: true,
                esModuleInterop: true,
                jsx: ts.JsxEmit.ReactJSX || ts.JsxEmit.React,
                module: ts.ModuleKind.ESNext,
                moduleResolution: ts.ModuleResolutionKind.NodeJs,
                target: ts.ScriptTarget.ESNext
            }
        };
    }

    const raw = ts.readConfigFile(config, ts.sys.readFile);
    if (raw.error) throw new Error(ts.flattenDiagnosticMessageText(raw.error.messageText, '\n'));
    const parsed = ts.parseJsonConfigFileContent(raw.config, ts.sys, path.dirname(config));
    return {fileNames: parsed.fileNames, options: parsed.options};
}

function displayParts(parts) {
    return ts.displayPartsToString(parts || []);
}

function makeService(req) {
    const fileName = path.resolve(req.file);
    const project = parseProject(fileName);
    if (project.fileNames.indexOf(fileName) === -1) project.fileNames.push(fileName);

    const currentText = String(req.text || '');
    const versions = Object.create(null);
    versions[fileName] = '1';

    const host = {
        getCompilationSettings: () => project.options,
        getScriptFileNames: () => project.fileNames,
        getScriptVersion: name => versions[path.resolve(name)] || '0',
        getScriptSnapshot: name => {
            const resolved = path.resolve(name);
            if (resolved === fileName) return ts.ScriptSnapshot.fromString(currentText);
            try { return ts.ScriptSnapshot.fromString(fs.readFileSync(resolved, 'utf8')); }
            catch (e) { return undefined; }
        },
        getCurrentDirectory: () => path.dirname(fileName),
        getDefaultLibFileName: options => ts.getDefaultLibFilePath(options),
        fileExists: ts.sys.fileExists,
        readFile: ts.sys.readFile,
        readDirectory: ts.sys.readDirectory,
        directoryExists: ts.sys.directoryExists,
        getDirectories: ts.sys.getDirectories,
        realpath: ts.sys.realpath,
        useCaseSensitiveFileNames: () => ts.sys.useCaseSensitiveFileNames,
        getNewLine: () => ts.sys.newLine
    };

    return {service: ts.createLanguageService(host, ts.createDocumentRegistry()), fileName};
}

function completion(service, fileName, pos) {
    const info = service.getCompletionsAtPosition(fileName, pos, {
        includeExternalModuleExports: true,
        includeInsertTextCompletions: false
    });
    if (!info) return {completions: []};
    return {
        completions: info.entries.map(entry => ({
            name: entry.name,
            kind: entry.kind || 'variable',
            sortText: entry.sortText || entry.name
        }))
    };
}

function signature(service, fileName, pos) {
    const help = service.getSignatureHelpItems(fileName, pos, undefined);
    if (!help || !help.items || !help.items.length) return {calltips: []};
    const calltips = help.items.map(item => {
        const params = item.parameters.map(p => displayParts(p.displayParts));
        return displayParts(item.prefixDisplayParts) +
            params.join(displayParts(item.separatorDisplayParts)) +
            displayParts(item.suffixDisplayParts);
    });
    return {calltips};
}

function definition(service, fileName, pos) {
    const defs = service.getDefinitionAtPosition(fileName, pos) || [];
    return {
        definitions: defs.map(def => {
            let line = 1;
            try {
                const program = service.getProgram();
                const sf = program && program.getSourceFile(def.fileName);
                if (sf) line = sf.getLineAndCharacterOfPosition(def.textSpan.start).line + 1;
            } catch (e) {}
            return {
                name: def.name || '',
                kind: def.kind || 'variable',
                file: def.fileName,
                line
            };
        })
    };
}

readStdin().then(req => {
    const ctx = makeService(req);
    const pos = Math.max(0, Number(req.pos) || 0);
    let result;
    switch (req.action) {
        case 'completion': result = completion(ctx.service, ctx.fileName, pos); break;
        case 'signature': result = signature(ctx.service, ctx.fileName, pos); break;
        case 'definition': result = definition(ctx.service, ctx.fileName, pos); break;
        default: result = {error: 'unknown action: ' + req.action};
    }
    process.stdout.write(JSON.stringify(result));
}).catch(err => {
    process.stdout.write(JSON.stringify({error: String(err && err.stack || err)}));
    process.exitCode = 1;
});
