import os
from pathlib import Path
from config import config
from modules.video_processor import VideoProcessor
from modules.asr_processor import ASRProcessor
from modules.llm_processor import LLMProcessor


def get_existing_frames(video_name):
    """获取已存在的帧文件列表"""
    frames_dir = config.get_video_frames_dir(video_name)
    frames = []
    # 帧文件前缀使用 video_name 的最后一部分（不含子目录路径）
    frame_prefix = Path(video_name).name
    if os.path.exists(frames_dir):
        frame_files = [f for f in os.listdir(frames_dir) if f.startswith(frame_prefix) and f.endswith('.jpg')]
        frame_files.sort()
        frames = [os.path.join(frames_dir, f) for f in frame_files]
    return frames


def check_step_status(video_name):
    """检查视频各个处理步骤的完成状态
    
    返回各步骤的状态字典
    """
    frames_dir = config.get_video_frames_dir(video_name)
    # 帧文件前缀使用 video_name 的最后一部分
    frame_prefix = Path(video_name).name
    frames_exist = os.path.exists(frames_dir) and len([f for f in os.listdir(frames_dir) if f.startswith(frame_prefix) and f.endswith('.jpg')]) > 0
    
    # 音频、转写文本、文章文件名使用 video_name 的最后一部分
    base_name = Path(video_name).name
    audio_path = os.path.join(config.get_video_audio_dir(video_name), f"{base_name}.mp3")
    audio_exist = os.path.exists(audio_path)
    
    txt_path = os.path.join(config.get_video_audio_txt_dir(video_name), f"{base_name}.txt")
    txt_exist = os.path.exists(txt_path)
    
    article_path = os.path.join(config.get_video_articles_dir(video_name), f"{base_name}.md")
    article_exist = os.path.exists(article_path)
    
    return {
        'frames_done': frames_exist,
        'audio_done': audio_exist,
        'txt_done': txt_exist,
        'article_done': article_exist,
        'all_done': frames_exist and audio_exist and txt_exist and article_exist
    }


def get_processed_video_data(video_name, video_path):
    """获取已处理视频的完整数据"""
    base_name = Path(video_name).name
    audio_path = os.path.join(config.get_video_audio_dir(video_name), f"{base_name}.mp3")
    txt_path = os.path.join(config.get_video_audio_txt_dir(video_name), f"{base_name}.txt")
    
    frames = get_existing_frames(video_name)
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    return {
        'video_path': video_path,
        'video_name': video_name,
        'video_info': {},
        'frames': frames,
        'audio_path': audio_path,
        'text': text,
        'success': True
    }


def get_video_files(input_dir):
    """递归获取所有视频文件，返回 (绝对路径, 相对路径) 列表"""
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')
    video_files = []
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if f.lower().endswith(video_extensions):
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, input_dir)
                video_files.append((abs_path, rel_path))
    return video_files


def main():
    print('=== 教学视频分析与飞书知识库发布系统 ===\n')
    
    config.ensure_directories()
    
    video_processor = VideoProcessor()
    asr_processor = ASRProcessor()
    llm_processor = LLMProcessor()

    try:
        print('1/3 开始处理视频...')
        
        video_files_with_rel = get_video_files(config.INPUT_VIDEO_DIR)
        
        video_results = []
        skipped_frames = 0
        skipped_audio = 0
        
        for video_file, video_rel_path in video_files_with_rel:
            # video_name 使用相对路径（不含扩展名），与 output 子目录结构对应
            video_name = os.path.splitext(video_rel_path)[0]
            step_status = check_step_status(video_name)
            
            config.ensure_video_directories(video_name)
            
            frames_result = None
            if step_status['frames_done']:
                print(f"跳过已提取帧: {video_name}")
                frames_result = {
                    'success': True,
                    'frames': get_existing_frames(video_name),
                    'frame_count': len(get_existing_frames(video_name))
                }
                skipped_frames += 1
            else:
                print(f"提取帧: {video_name}")
                frames_dir = config.get_video_frames_dir(video_name)
                frames_result = video_processor.extract_key_frames(video_file, frames_dir)
            
            audio_result = None
            base_name = Path(video_name).name
            audio_path = os.path.join(config.get_video_audio_dir(video_name), f"{base_name}.mp3")
            if step_status['audio_done']:
                print(f"跳过已提取音频: {video_name}")
                audio_result = {'success': True, 'audio_path': audio_path}
                skipped_audio += 1
            else:
                print(f"提取音频: {video_name}")
                audio_dir = config.get_video_audio_dir(video_name)
                audio_result = video_processor.extract_audio(video_file, audio_dir)
            
            video_info = video_processor.get_video_info(video_file)
            
            video_results.append({
                'video_path': video_file,
                'video_name': video_name,
                'video_info': video_info,
                'frames': frames_result.get('frames', []),
                'frame_count': frames_result.get('frame_count', 0),
                'audio_path': audio_result.get('audio_path'),
                'success': frames_result.get('success') and audio_result.get('success')
            })
        
        success_videos = [r for r in video_results if r.get('success')]
        print(f"\n视频处理完成: {len(success_videos)}/{len(video_files_with_rel)} 个视频")
        if skipped_frames > 0:
            print(f"跳过已提取帧: {skipped_frames} 个")
        if skipped_audio > 0:
            print(f"跳过已提取音频: {skipped_audio} 个")

        print('2/3 开始语音转写...')
        
        need_transcribe = []
        already_transcribed = []
        
        for video_result in success_videos:
            video_name = video_result.get('video_name')
            base_name = Path(video_name).name
            audio_path = video_result.get('audio_path')
            txt_path = os.path.join(config.get_video_audio_txt_dir(video_name), f"{base_name}.txt")
            
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                already_transcribed.append({
                    'audio_path': audio_path,
                    'text': text,
                    'video_name': video_name,
                    'success': True
                })
                print(f"跳过已转写: {video_name}")
            else:
                need_transcribe.append(audio_path)
        
        asr_results = asr_processor.batch_transcribe(need_transcribe)
        
        # 建立 audio_path 到 video_result 的映射
        audio_to_video = {v['audio_path']: v for v in success_videos}
        
        success_asr = already_transcribed.copy()
        for i, asr_result in enumerate(asr_results):
            if asr_result.get('success'):
                audio_path = need_transcribe[i]
                video_result = audio_to_video.get(audio_path, {})
                video_name = video_result.get('video_name', Path(audio_path).stem)
                asr_processor.save_transcript_to_file(
                    audio_path, 
                    asr_result, 
                    video_name=video_name
                )
                success_asr.append({
                    **asr_result,
                    'video_name': video_name
                })
        
        newly_transcribed_count = len([r for r in asr_results if r.get('success')])
        print(f"\n语音转写完成: {len(success_asr)}/{len(success_videos)} 个音频")
        if already_transcribed:
            print(f"跳过已转写: {len(already_transcribed)} 个")
        print(f"新转写: {newly_transcribed_count} 个")

        print('3/3 开始生成文章...')
        
        article_inputs = []
        for asr_result in success_asr:
            video_result = next((v for v in success_videos if v['video_name'] == asr_result.get('video_name')), None)
            article_inputs.append({
                'audio_path': asr_result['audio_path'],
                'text': asr_result['text'],
                'frames': video_result.get('frames', []) if video_result else [],
                'video_info': video_result.get('video_info', {}) if video_result else {},
                'video_name': video_result.get('video_name') if video_result else None
            })
        
        need_generate = []
        skipped_articles = 0
        for input_data in article_inputs:
            video_name = input_data.get('video_name')
            base_name = Path(video_name).name
            article_path = os.path.join(config.get_video_articles_dir(video_name), f"{base_name}.md")
            if not os.path.exists(article_path):
                need_generate.append(input_data)
            else:
                print(f"跳过已生成: {video_name}")
                skipped_articles += 1
        
        article_results = llm_processor.batch_generate_articles(need_generate)

        success_articles = [r for r in article_results if r.get('success')]
        
        skipped_article_count = skipped_articles
        newly_generated_count = len(success_articles)
        print(f"\n文章生成完成: {newly_generated_count}/{len(article_inputs)} 篇文章")
        if skipped_article_count:
            print(f"跳过已生成: {skipped_article_count} 篇")
        print(f"新生成: {newly_generated_count} 篇")

        print('\n=== 处理流程全部完成 ===')

    except Exception as error:
        print(f'\n处理过程中发生错误: {error}')
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == '__main__':
    main()