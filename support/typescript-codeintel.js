'use strict';

/*
 * TypeScript LanguageService bridge for Komodo 9 CodeIntel.
 *
 * One-shot mode:
 *   node typescript-codeintel.js /path/to/typescript.js
 *
 * Persistent mode used by Komodo 0.3.2+:
 *   node typescript-codeintel.js /path/to/typescript.js --server
 *
 * Requests are JSON objects with {action, file, text, pos}. In server mode
 * requests and responses are one JSON object per line. The TypeScript runtime
 * is loaded once and reused across implicit completion/calltip requests.
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const tsPath = process.argv[2];
const serverMode = process.argv.indexOf('--server') !== -1;

if (!tsPath) {
    process.stdout.write(JSON.stringify({error: 'typescript.js path is required'}));
    process.exit(2);
}

const ts = require(tsPath);
const registry = ts.createDocumentRegistry();

function isRemoteUri(fileName) {
    return /^[A-Za-z][A-Za-z0-9+.-]*:\/\/+/.test(String(fileName || ''));
}

function virtualRemoteFileName(uri) {
    const match = /^([A-Za-z][A-Za-z0-9+.-]*):\/\/(.*)$/.exec(String(uri || ''));
    if (!match) return '/__komodo_remote__/remote.ts';

    const scheme = match[1].replace(/[^A-Za-z0-9._-]/g, '_');
    const parts = match[2].split('/').filter(Boolean).map(function (part) {
        return part.replace(/[^A-Za-z0-9._-]/g, '_');
    });

    if (!parts.length) parts.push('remote.ts');
    return path.posix.join.apply(path.posix, ['/__komodo_remote__', scheme].concat(parts));
}

function defaultOptions() {
    return {
        allowJs: true,
        allowSyntheticDefaultImports: true,
        esModuleInterop: true,
        jsx: ts.JsxEmit.ReactJSX || ts.JsxEmit.React,
        module: ts.ModuleKind.ESNext,
        moduleResolution: ts.ModuleResolutionKind.NodeJs,
        target: ts.ScriptTarget.ESNext
    };
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

function parseProject(fileName, remote) {
    if (remote) {
        return {fileNames: [fileName], options: defaultOptions()};
    }

    const config = findConfig(fileName);
    if (!config) {
        return {fileNames: [path.resolve(fileName)], options: defaultOptions()};
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
    const originalFile = String(req.file || '');
    const remote = isRemoteUri(originalFile);
    const fileName = remote ? virtualRemoteFileName(originalFile) : path.resolve(originalFile);
    const project = parseProject(fileName, remote);
    if (project.fileNames.indexOf(fileName) === -1) project.fileNames.push(fileName);

    const currentText = String(req.text || '');
    const versions = Object.create(null);
    versions[fileName] = '1';
    const currentDir = path.dirname(fileName);

    function resolveName(name) {
        return path.resolve(name);
    }

    function isCurrent(name) {
        return resolveName(name) === fileName;
    }

    const host = {
        getCompilationSettings: function () { return project.options; },
        getScriptFileNames: function () { return project.fileNames; },
        getScriptVersion: function (name) { return versions[resolveName(name)] || '0'; },
        getScriptSnapshot: function (name) {
            const resolved = resolveName(name);
            if (resolved === fileName) return ts.ScriptSnapshot.fromString(currentText);
            try { return ts.ScriptSnapshot.fromString(fs.readFileSync(resolved, 'utf8')); }
            catch (e) { return undefined; }
        },
        getCurrentDirectory: function () { return currentDir; },
        getDefaultLibFileName: function (options) { return ts.getDefaultLibFilePath(options); },
        fileExists: function (name) { return isCurrent(name) || ts.sys.fileExists(name); },
        readFile: function (name) { return isCurrent(name) ? currentText : ts.sys.readFile(name); },
        readDirectory: ts.sys.readDirectory,
        directoryExists: function (name) {
            const resolved = resolveName(name);
            if (remote && resolved === currentDir) return true;
            return ts.sys.directoryExists ? ts.sys.directoryExists(name) : fs.existsSync(name);
        },
        getDirectories: ts.sys.getDirectories,
        realpath: function (name) {
            if (isCurrent(name)) return fileName;
            return ts.sys.realpath ? ts.sys.realpath(name) : resolveName(name);
        },
        useCaseSensitiveFileNames: function () { return ts.sys.useCaseSensitiveFileNames; },
        getNewLine: function () { return ts.sys.newLine; }
    };

    return {
        service: ts.createLanguageService(host, registry),
        fileName: fileName,
        originalFile: originalFile,
        remote: remote
    };
}

function completion(service, fileName, pos) {
    const info = service.getCompletionsAtPosition(fileName, pos, {
        includeExternalModuleExports: true,
        includeInsertTextCompletions: false
    });
    if (!info) return {completions: []};
    return {
        completions: info.entries.map(function (entry) {
            return {
                name: entry.name,
                kind: entry.kind || 'variable',
                sortText: entry.sortText || entry.name
            };
        })
    };
}

function signature(service, fileName, pos) {
    const help = service.getSignatureHelpItems(fileName, pos, undefined);
    if (!help || !help.items || !help.items.length) return {calltips: []};
    const calltips = help.items.map(function (item) {
        const params = item.parameters.map(function (p) {
            return displayParts(p.displayParts);
        });
        return displayParts(item.prefixDisplayParts) +
            params.join(displayParts(item.separatorDisplayParts)) +
            displayParts(item.suffixDisplayParts);
    });
    return {calltips: calltips};
}

function definition(ctx, pos) {
    const defs = ctx.service.getDefinitionAtPosition(ctx.fileName, pos) || [];
    return {
        definitions: defs.map(function (def) {
            let line = 1;
            try {
                const program = ctx.service.getProgram();
                const sf = program && program.getSourceFile(def.fileName);
                if (sf) line = sf.getLineAndCharacterOfPosition(def.textSpan.start).line + 1;
            } catch (e) {}

            const definitionFile = ctx.remote && path.resolve(def.fileName) === ctx.fileName
                ? ctx.originalFile
                : def.fileName;

            return {
                name: def.name || '',
                kind: def.kind || 'variable',
                file: definitionFile,
                line: line
            };
        })
    };
}

function handleRequest(req) {
    const ctx = makeService(req);
    const pos = Math.max(0, Number(req.pos) || 0);

    switch (req.action) {
        case 'completion': return completion(ctx.service, ctx.fileName, pos);
        case 'signature': return signature(ctx.service, ctx.fileName, pos);
        case 'definition': return definition(ctx, pos);
        default: return {error: 'unknown action: ' + req.action};
    }
}

function safeHandle(req) {
    try {
        return handleRequest(req);
    } catch (err) {
        return {error: String(err && err.stack || err)};
    }
}

function runServer() {
    const rl = readline.createInterface({input: process.stdin});
    rl.on('line', function (line) {
        if (!line) return;
        let req;
        try {
            req = JSON.parse(line);
        } catch (err) {
            process.stdout.write(JSON.stringify({error: String(err)}) + '\n');
            return;
        }
        process.stdout.write(JSON.stringify(safeHandle(req)) + '\n');
    });
}

function runOneShot() {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', function (chunk) { data += chunk; });
    process.stdin.on('end', function () {
        let req;
        try {
            req = JSON.parse(data || '{}');
        } catch (err) {
            process.stdout.write(JSON.stringify({error: String(err)}));
            process.exitCode = 1;
            return;
        }
        const result = safeHandle(req);
        process.stdout.write(JSON.stringify(result));
        if (result.error) process.exitCode = 1;
    });
}

if (serverMode) runServer();
else runOneShot();
