/*
 * Live-buffer TypeScript diagnostics bridge for Komodo 9.
 *
 * Usage:
 *   node typescript-bridge.js /path/to/typescript.js /path/to/current.ts
 * Source text is read from stdin. JSON diagnostics are written to stdout.
 */
"use strict";

var fs = require("fs");
var path = require("path");

var tsPath = process.argv[2];
var fileName = path.resolve(process.argv[3]);
var sourceChunks = [];

function fatal(message) {
    process.stdout.write(JSON.stringify({ fatal: String(message), diagnostics: [] }));
}

function norm(p) {
    var resolved = path.resolve(p);
    if (process.platform === "win32") {
        return resolved.toLowerCase();
    }
    return resolved;
}

function flatten(ts, messageText) {
    return ts.flattenDiagnosticMessageText(messageText, "\n");
}

function categoryName(ts, category) {
    return category === ts.DiagnosticCategory.Error ? "error" : "warning";
}

function diagnosticToJson(ts, diagnostic, currentFile) {
    var result = {
        line: 1,
        column: 1,
        endLine: 1,
        endColumn: 2,
        category: categoryName(ts, diagnostic.category),
        code: diagnostic.code,
        message: flatten(ts, diagnostic.messageText)
    };

    if (!diagnostic.file || diagnostic.start === undefined || diagnostic.start === null) {
        return result;
    }

    if (norm(diagnostic.file.fileName) !== norm(currentFile)) {
        return null;
    }

    var start = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start);
    var length = diagnostic.length || 1;
    var end = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start + length);

    result.line = start.line + 1;
    result.column = start.character + 1;
    result.endLine = end.line + 1;
    result.endColumn = end.character + 1;
    return result;
}

process.stdin.setEncoding("utf8");
process.stdin.on("data", function (chunk) {
    sourceChunks.push(chunk);
});

process.stdin.on("end", function () {
    var ts;
    try {
        ts = require(tsPath);
    } catch (e) {
        fatal("Cannot load TypeScript compiler from " + tsPath + ": " + e.message);
        return;
    }

    var sourceText = sourceChunks.join("");
    var configFile = ts.findConfigFile(path.dirname(fileName), ts.sys.fileExists, "tsconfig.json");
    var options = {};
    var declarationRoots = [];
    var configDiagnostics = [];

    if (configFile) {
        try {
            var readResult = ts.readConfigFile(configFile, ts.sys.readFile);
            if (readResult.error) {
                configDiagnostics.push(readResult.error);
            } else {
                var parsed = ts.parseJsonConfigFileContent(
                    readResult.config,
                    ts.sys,
                    path.dirname(configFile),
                    undefined,
                    configFile
                );
                options = parsed.options || {};
                configDiagnostics = configDiagnostics.concat(parsed.errors || []);
                declarationRoots = (parsed.fileNames || []).filter(function (name) {
                    return /\.d\.(?:ts|mts|cts)$/i.test(name);
                });
            }
        } catch (e) {
            fatal("Cannot read " + configFile + ": " + e.message);
            return;
        }
    }

    options.noEmit = true;

    var originalCurrent = norm(fileName);
    var host = ts.createCompilerHost(options, true);
    var originalGetSourceFile = host.getSourceFile;

    host.fileExists = (function (originalFileExists) {
        return function (name) {
            if (norm(name) === originalCurrent) {
                return true;
            }
            return originalFileExists.call(host, name);
        };
    }(host.fileExists));

    host.readFile = (function (originalReadFile) {
        return function (name) {
            if (norm(name) === originalCurrent) {
                return sourceText;
            }
            return originalReadFile.call(host, name);
        };
    }(host.readFile));

    host.getSourceFile = function (name, languageVersion, onError, shouldCreateNewSourceFile) {
        if (norm(name) === originalCurrent) {
            var scriptKind = undefined;
            if (ts.getScriptKindFromFileName) {
                scriptKind = ts.getScriptKindFromFileName(name);
            } else if (/\.tsx$/i.test(name)) {
                scriptKind = ts.ScriptKind.TSX;
            } else {
                scriptKind = ts.ScriptKind.TS;
            }
            return ts.createSourceFile(name, sourceText, languageVersion, true, scriptKind);
        }
        return originalGetSourceFile.call(host, name, languageVersion, onError, shouldCreateNewSourceFile);
    };

    var rootNames = [fileName];
    declarationRoots.forEach(function (name) {
        if (norm(name) !== originalCurrent) {
            rootNames.push(name);
        }
    });

    var program;
    try {
        program = ts.createProgram(rootNames, options, host);
    } catch (e) {
        fatal("TypeScript createProgram failed: " + e.message);
        return;
    }

    var diagnostics = configDiagnostics.concat(ts.getPreEmitDiagnostics(program));
    var output = [];
    diagnostics.forEach(function (diagnostic) {
        var item = diagnosticToJson(ts, diagnostic, fileName);
        if (item) {
            output.push(item);
        }
    });

    process.stdout.write(JSON.stringify({
        typescriptVersion: ts.version || null,
        configFile: configFile || null,
        diagnostics: output
    }));
});
