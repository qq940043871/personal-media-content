#!/usr/bin/env python3
"""
测试图像生成功能
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.generate_image import get_image_generator


def test_image_generation():
    """测试图像生成"""
    print("="*60)
    print("🔍 测试图像生成功能")
    print("="*60)
    
    # 初始化生成器
    print("\n1️⃣ 初始化图像生成器...")
    try:
        generator = get_image_generator()
        print(f"   ✅ 生成器初始化成功")
        print(f"   模型: {generator.model}")
        print(f"   API URL: {generator.base_url}")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        return
    
    # 测试生成
    print("\n2️⃣ 测试图像生成...")
    test_prompt = "一张科技风格的封面图，蓝色调，电路板纹理，未来感"
    
    try:
        result = generator.generate(test_prompt, size="2K")
        
        print(f"\n3️⃣ 生成结果:")
        if result["success"]:
            print("   ✅ 生成成功!")
            if result.get("b64_json"):
                print(f"   Base64数据长度: {len(result['b64_json'])}")
            if result.get("url"):
                print(f"   图像URL: {result['url']}")
            if result.get("revised_prompt"):
                print(f"   优化后的提示词: {result['revised_prompt'][:50]}...")
            
            # 尝试保存
            if result.get("b64_json"):
                import base64
                output_path = Path("test_output.png")
                image_data = base64.b64decode(result["b64_json"])
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"   💾 测试图像已保存到: {output_path}")
        else:
            print(f"   ❌ 生成失败: {result.get('error')}")
    
    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)


if __name__ == "__main__":
    test_image_generation()
