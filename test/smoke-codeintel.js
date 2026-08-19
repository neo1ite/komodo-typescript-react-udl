'use strict';

/* Build-time smoke test for the TypeScript bridges. */

const childProcess = require('child_process');

const codeintelBridge = process.argv[2];
const lintBridge = process.argv[3];
const typescriptJs = process.argv[4];

if (!codeintelBridge || !lintBridge || !typescriptJs) {
    console.error('usage: node smoke-codeintel.js CODEINTEL_BRIDGE LINT_BRIDGE TYPESCRIPT_JS');
    process.exit(2);
}

function fail(message) {
    console.error('smoke-codeintel: ' + message);
    process.exit(1);
}

function oneShot(request) {
    const result = childProcess.spawnSync(
        process.execPath,
        [codeintelBridge, typescriptJs],
        {input: JSON.stringify(request), encoding: 'utf8'}
    );
    if (result.error) fail(String(result.error));
    if (!result.stdout) fail('CodeIntel bridge returned no stdout: ' + result.stderr);
    let payload;
    try { payload = JSON.parse(result.stdout); }
    catch (e) { fail('invalid CodeIntel JSON: ' + result.stdout); }
    if (payload.error) fail(payload.error);
    return payload;
}

const remoteFile = 'scp://Smoke/project/sample.ts';

const completionText = "const obj = { alpha: 1, beta: 'x' };\nobj.";
const completionRequest = {
    action: 'completion',
    file: remoteFile,
    text: completionText,
    pos: completionText.length
};
const completion = oneShot(completionRequest);
const completionNames = (completion.completions || []).map(function (item) { return item.name; });
if (completionNames.indexOf('alpha') === -1 || completionNames.indexOf('beta') === -1) {
    fail('member completion did not return alpha/beta: ' + JSON.stringify(completion));
}

const signatureText = 'function sum(a: number, b: number): number { return a + b; }\nsum(';
const signatureRequest = {
    action: 'signature',
    file: remoteFile,
    text: signatureText,
    pos: signatureText.length
};
const signature = oneShot(signatureRequest);
if (!(signature.calltips || []).some(function (tip) {
    return tip.indexOf('a: number') !== -1 && tip.indexOf('b: number') !== -1;
})) {
    fail('signature help did not return sum(a, b): ' + JSON.stringify(signature));
}

const definitionText = 'function sum(a: number, b: number): number { return a + b; }\nsum(1, 2);';
const callPos = definitionText.lastIndexOf('sum') + 1;
const definition = oneShot({
    action: 'definition',
    file: remoteFile,
    text: definitionText,
    pos: callPos
});
if (!(definition.definitions || []).length) {
    fail('definition request returned no definitions: ' + JSON.stringify(definition));
}
if (definition.definitions[0].file !== remoteFile) {
    fail('remote definition was not translated back to SCP URI: ' + JSON.stringify(definition));
}

const lintSource = "import React from 'react';\nconst broken: = 1;\n";
const lintResult = childProcess.spawnSync(
    process.execPath,
    [lintBridge, typescriptJs, '/tmp/__komodo_remote__.ts', '--syntax-only'],
    {input: lintSource, encoding: 'utf8'}
);
if (lintResult.error) fail(String(lintResult.error));
let lintPayload;
try { lintPayload = JSON.parse(lintResult.stdout || '{}'); }
catch (e) { fail('invalid linter JSON: ' + lintResult.stdout); }
const diagnostics = lintPayload.diagnostics || [];
if (!diagnostics.length) {
    fail('syntax-only linter did not report the deliberate syntax error');
}
if (diagnostics.some(function (item) {
    return /cannot find module/i.test(String(item.message || ''));
})) {
    fail('syntax-only linter returned semantic module diagnostics: ' + JSON.stringify(lintPayload));
}

function validateServerResponses(responses) {
    if (responses.length !== 2) {
        fail('persistent bridge returned ' + responses.length + ' responses, expected 2');
    }

    const names = (responses[0].completions || []).map(function (item) { return item.name; });
    if (names.indexOf('alpha') === -1 || names.indexOf('beta') === -1) {
        fail('persistent completion did not return alpha/beta: ' + JSON.stringify(responses[0]));
    }

    if (!(responses[1].calltips || []).some(function (tip) {
        return tip.indexOf('a: number') !== -1 && tip.indexOf('b: number') !== -1;
    })) {
        fail('persistent signature help failed: ' + JSON.stringify(responses[1]));
    }
}

const server = childProcess.spawn(
    process.execPath,
    [codeintelBridge, typescriptJs, '--server'],
    {stdio: ['pipe', 'pipe', 'pipe']}
);

server.stdout.setEncoding('utf8');
server.stderr.setEncoding('utf8');
let stdoutBuffer = '';
let stderrBuffer = '';
const serverResponses = [];
let finished = false;

const timeout = setTimeout(function () {
    if (finished) return;
    server.kill();
    fail('persistent bridge timed out; stderr=' + stderrBuffer);
}, 5000);

server.stderr.on('data', function (chunk) { stderrBuffer += chunk; });
server.stdout.on('data', function (chunk) {
    stdoutBuffer += chunk;
    while (stdoutBuffer.indexOf('\n') !== -1) {
        const idx = stdoutBuffer.indexOf('\n');
        const line = stdoutBuffer.slice(0, idx);
        stdoutBuffer = stdoutBuffer.slice(idx + 1);
        if (!line) continue;

        let payload;
        try { payload = JSON.parse(line); }
        catch (e) {
            server.kill();
            fail('invalid persistent bridge JSON: ' + line);
        }
        if (payload.error) {
            server.kill();
            fail('persistent bridge error: ' + payload.error);
        }
        serverResponses.push(payload);

        if (serverResponses.length === 2) {
            finished = true;
            clearTimeout(timeout);
            validateServerResponses(serverResponses);
            server.kill();
            console.log('smoke-codeintel: OK');
        }
    }
});

server.on('error', function (err) {
    if (!finished) fail(String(err));
});

server.stdin.write(JSON.stringify(completionRequest) + '\n');
server.stdin.write(JSON.stringify(signatureRequest) + '\n');
server.stdin.flush && server.stdin.flush();
