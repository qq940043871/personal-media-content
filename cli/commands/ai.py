"""ai 命令域 — ASR 转写 / LLM 对话"""

import os
import sys


def cmd_asr_transcribe(args):
    """语音转写"""
    from core.asr_client import ASRClient

    asr = ASRClient()

    if args.local:
        result = asr.transcribe_local(args.audio)
        if args.srt and result.get('success'):
            srt_path = os.path.splitext(args.audio)[0] + '.srt'
            result = asr.transcribe_with_srt(args.audio, srt_path)
    else:
        result = asr.transcribe(args.audio)

    if result.get('success'):
        text = result.get('text', '')
        print(f"✅ 转写完成（{len(text)} 字符）")
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"已保存到: {args.output}")
        else:
            print()
            print("--- 转写文本 ---")
            print(text[:500] + ("..." if len(text) > 500 else ""))
    else:
        print(f"❌ 转写失败: {result.get('error', '未知错误')}")
        sys.exit(1)


def cmd_llm_chat(args):
    """调用大模型"""
    from core.llm_client import LLMClient

    llm = LLMClient(system_prompt=args.system or '你是一个专业的AI助手。')

    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            prompt = f.read()
    else:
        prompt = args.prompt

    if args.stream:
        print("--- 流式输出 ---")
        result = llm.chat_stream(prompt)
    else:
        result = llm.chat(prompt)
        print(result)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"\n已保存到: {args.output}")


def register(subparsers):
    # ---- asr ----
    p_asr = subparsers.add_parser('asr', help='语音转写相关')
    asr_sub = p_asr.add_subparsers(dest='asr_cmd', help='ASR 子命令')

    p_at = asr_sub.add_parser('transcribe', help='语音转写')
    p_at.add_argument('audio', help='音频文件路径')
    p_at.add_argument('--local', action='store_true', help='使用本地 faster-whisper')
    p_at.add_argument('--srt', action='store_true', help='生成 SRT 字幕（仅本地模式）')
    p_at.add_argument('-o', '--output', help='输出文本文件路径')
    p_at.set_defaults(func=cmd_asr_transcribe)

    # ---- llm ----
    p_llm = subparsers.add_parser('llm', help='大模型调用')
    llm_sub = p_llm.add_subparsers(dest='llm_cmd', help='LLM 子命令')

    p_lc = llm_sub.add_parser('chat', help='单轮对话')
    p_lc.add_argument('prompt', nargs='?', help='提示词')
    p_lc.add_argument('-f', '--file', help='从文件读取提示词')
    p_lc.add_argument('-s', '--system', help='系统提示词')
    p_lc.add_argument('--stream', action='store_true', help='流式输出')
    p_lc.add_argument('-o', '--output', help='输出文件路径')
    p_lc.set_defaults(func=cmd_llm_chat)
