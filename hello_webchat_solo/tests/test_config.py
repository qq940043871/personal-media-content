#!/usr/bin/env python3
"""
测试配置加载功能
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import load_article_config, get_config


def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试配置加载功能")
    print("=" * 60)

    # 测试加载配置
    config = load_article_config()

    print("\n配置内容：")
    for key, value in config.items():
        if isinstance(value, list) and len(value) > 3:
            print(f"  {key}: {value[:3]}... ({len(value)} items)")
        else:
            print(f"  {key}: {value}")

    # 验证关键配置
    print("\n验证关键配置：")
    assert "article_category" in config, "缺少 article_category"
    assert "target_reader" in config, "缺少 target_reader"
    assert "tone" in config, "缺少 tone"
    assert "forbidden_words" in config, "缺少 forbidden_words"
    print("  所有关键配置项都存在")

    # 测试 get_config 函数
    config2 = get_config()
    assert config == config2, "get_config() 返回值不一致"
    print("  get_config() 函数正常")

    print("\n" + "=" * 60)
    print("配置加载测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_config_loading()
