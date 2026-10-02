/**
 * 飞书 Lark CLI 桥接脚本 — 通过 @larksuite/cli 操作飞书文档
 *
 * 用法：
 *   node lark_helper.js auth-status
 *   node lark_helper.js create-doc <contentFile> <title>
 *   node lark_helper.js insert-image <docId> <imageFile> [caption] [selection]
 *
 * 注意：需提前安装 @larksuite/cli 并完成登录授权
 */

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// lark-cli run.js 路径（可通过环境变量 LARK_CLI_RUN_JS 覆盖）
const LARK_CLI_RUN = process.env.LARK_CLI_RUN_JS ||
    path.join(process.env.ProgramFiles || 'C:\\Program Files',
        'nodejs', 'node_modules', '@larksuite', 'cli', 'scripts', 'run.js');

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
    if (r.stderr) process.stderr.write(r.stderr);
    if (r.status !== 0) process.exit(r.status || 1);
}

try {
    if (action === 'auth-status') {
        // 授权状态检查（供 health_check 使用）
        runLarkCli(['auth', 'status']);

    } else if (action === 'create-doc') {
        // 创建飞书文档
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
        // 在文档中插入图片
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

    } else if (action === 'move-to-wiki') {
        // 移动文档到知识空间（预留接口）
        const docToken = args[1];
        const wikiSpaceId = args[2];
        const parentNodeToken = args[3] || '';

        const larkArgs = [
            'wiki', '+move',
            '--doc', docToken,
            '--space', wikiSpaceId
        ];
        if (parentNodeToken) larkArgs.push('--parent', parentNodeToken);

        runLarkCli(larkArgs);

    } else {
        process.stdout.write('Unknown action: ' + action + '\n');
        process.stdout.write('Available: auth-status, create-doc, insert-image, move-to-wiki\n');
        process.exit(1);
    }
} catch (err) {
    process.stderr.write('FATAL: ' + err.message + '\n');
    process.exit(1);
}
