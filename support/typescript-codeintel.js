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

function isRemoteUri(fileName) {
    return /^[A-Za-z][A-Za-z0-9+.-]*:\/\/+/.test(String(fileName || ''));
}

function virtualRemoteFileName(uri) {
    const match = /^([A-Za-z][A-Za-z0-9+.-]*):\/\/(.*)$/.exec(String(uri || ''));
    if (!match) return '/__komodo_remote__/remote.ts';

    const scheme = match[1].replace(/[^A-Za-z0-9._-]/g, '_');
    const parts = match[2].split('/').filter(Boolean).map(part =>
        part.replace(/[^A-Za-z0-9._-]/g, '_')
    );

    if (!parts.length) parts.push('remote.ts');
    return path.posix.join('/__komodo_remote__', scheme, ...parts);
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
    // Node cannot read Komodo SCP/SFTP URIs. For remote buffers we therefore
    // build a single-file virtual project from the editor contents. This keeps
    // completion/calltips/definitions within the current remote file working
    // without pretending that the remote URI is a local filesystem path.
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
        getCompilationSettings: () => project.options,
        getScriptFileNames: () => project.fileNames,
        getScriptVersion: name => versions[resolveName(name)] || '0',
        getScriptSnapshot: name => {
            const resolved = resolveName(name);
            if (resolved === fileName) return ts.ScriptSnapshot.fromString(currentText);
            try { return ts.ScriptSnapshot.fromString(fs.readFileSync(resolved, 'utf8')); }
            catch (e) { return undefined; }
        },
        getCurrentDirectory: () => currentDir,
        getDefaultLibFileName: options => ts.getDefaultLibFilePath(options),
        fileExists: name => isCurrent(name) || ts.sys.fileExists(name),
        readFile: name => isCurrent(name) ? currentText : ts.sys.readFile(name),
        readDirectory: ts.sys.readDirectory,
        directoryExists: name => {
            const resolved = resolveName(name);
            if (remote && resolved === currentDir) return true;
            return ts.sys.directoryExists ? ts.sys.directoryExists(name) : fs.existsSync(name);
        },
        getDirectories: ts.sys.getDirectories,
        realpath: name => {
            if (isCurrent(name)) return fileName;
            return ts.sys.realpath ? ts.sys.realpath(name) : resolveName(name);
        },
        useCaseSensitiveFileNames: () => ts.sys.useCaseSensitiveFileNames,
        getNewLine: () => ts.sys.newLine
    };

    return {
        service: ts.createLanguageService(host, ts.createDocumentRegistry()),
        fileName,
        originalFile,
        remote
    };
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

function definition(ctx, pos) {
    const defs = ctx.service.getDefinitionAtPosition(ctx.fileName, pos) || [];
    return {
        definitions: defs.map(def => {
            let line = 1;
            try {
                const program = ctx.service.getProgram();
                const sf = program && program.getSourceFile(def.fileName);
                if (sf) line = sf.getLineAndCharacterOfPosition(def.textSpan.start).line + 1;
            } catch (e) {}

            // TypeScript sees an SCP/SFTP buffer under a synthetic local path.
            // Translate definitions in the current virtual file back to the
            // original Komodo URI so Go to Definition reuses the remote buffer
            // instead of prompting to create '/home/.../scp:/...'.
            const definitionFile = ctx.remote && path.resolve(def.fileName) === ctx.fileName
                ? ctx.originalFile
                : def.fileName;

            return {
                name: def.name || '',
                kind: def.kind || 'variable',
                file: definitionFile,
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
        case 'definition': result = definition(ctx, pos); break;
        default: result = {error: 'unknown action: ' + req.action};
    }
    process.stdout.write(JSON.stringify(result));
}).catch(err => {
    process.stdout.write(JSON.stringify({error: String(err && err.stack || err)}));
    process.exitCode = 1;
});
