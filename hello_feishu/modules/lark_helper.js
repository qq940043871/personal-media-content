const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const LARK_CLI_RUN = path.join(process.env.ProgramFiles || 'C:\\Program Files', 'nodejs', 'node_modules', '@larksuite', 'cli', 'scripts', 'run.js');

const args = process.argv.slice(2);
const action = args[0];

function runLarkCli(larkArgs, cwd) {
    const opts = {
        encoding: 'utf-8',
        maxBuffer: 10 * 1024 * 1024,
        windowsHide: true
    };
    if (cwd) opts.cwd = cwd;
    const r = spawnSync(process.execPath, [LARK_CLI_RUN, ...larkArgs], opts);
    if (r.stdout) process.stdout.write(r.stdout);
    if (r.stderr) process.stdout.write(r.stderr);
    if (r.status !== 0) process.exit(r.status || 1);
}

try {
    if (action === 'create-doc') {
        const contentFile = args[1];
        const title = args[2];
        const content = fs.readFileSync(contentFile, 'utf-8').replace(/^\n+/, '');
        
        runLarkCli([
            'docs', '+create',
            '--api-version', 'v2', '--as', 'user',
            '--title', title,
            '--doc-format', 'markdown',
            '--content', content
        ]);
    } else if (action === 'insert-image') {
        const docId = args[1];
        const imageFile = args[2];
        const caption = args[3] || '';
        const selection = args[4] || '';
        
        const imageDir = path.dirname(imageFile);
        const imageName = path.basename(imageFile);
        
        const larkArgs = [
            'docs', '+media-insert',
            '--doc', docId,
            '--file', imageName,
            '--type', 'image',
            '--width', '800'
        ];
        if (caption) larkArgs.push('--caption', caption);
        if (selection) larkArgs.push('--selection-with-ellipsis', selection);
        
        runLarkCli(larkArgs, imageDir);
    } else {
        process.stdout.write('Unknown action: ' + action + '\n');
        process.exit(1);
    }
} catch (err) {
    process.stdout.write('FATAL: ' + err.message + '\n');
    process.exit(1);
}
