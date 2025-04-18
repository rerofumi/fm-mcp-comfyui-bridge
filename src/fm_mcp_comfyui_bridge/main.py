from pathlib import Path

import requests
import yaml
from mcp.server.fastmcp import FastMCP, Image

import fm_mcp_comfyui_bridge.ollama_caption as OllamaCaption
import fm_mcp_comfyui_bridge.tagger as Tagger
from fm_mcp_comfyui_bridge.comfyui_bridge import (
    COMFYUI_NODE_OUTPUT,
    COMFYUI_URL,
    ComfyuiBridge,
)
from fm_mcp_comfyui_bridge.lora_yaml import SdLoraYaml

NEGATIVE = """
worst quality, bad quality, low quality, lowres, scan artifacts, jpeg artifacts, sketch,
light particles, jpeg artifacts, unfinished, oldest, old, abstract, signature
"""

VISION_PROMPT = """
# 指示
以下のイラストについて、詳細なテキストキャプションを生成してください。

# 注目してほしい点
*   全体的な雰囲気（例：暖かく穏やか、神秘的で静かなど）
*   主要な被写体（人物の場合：外見、服装、表情、ポーズ、何をしているか。物の場合：種類、状態、特徴）
*   背景（場所、時間帯、天候、描かれている要素）
*   構図と構成要素（主要なオブジェクトの位置関係、前景・中景・後景の要素）
*   色使い（全体的なトーン、印象的な色）
*   画風（例：アニメスタイル、写実的、水彩風など）
*   イラストから感じられる感情やストーリー

# 出力形式
自然な文章で、上記の注目点を網羅するように、できるだけ詳しく記述してください。
"""

HOST = "http://localhost:8188"

# MCPサーバーを作成
mcp = FastMCP("fm-mcp-comfyui-bridge")


def get_lora() -> SdLoraYaml:
    # main.py のあるディレクトリを取得
    current_dir = Path(__file__).parent
    # config ディレクトリ内の lora.yaml へのパスを構築
    lora_yaml_path = current_dir / "config" / "config.yaml"
    lora = SdLoraYaml()
    lora.read_from_yaml(lora_yaml_path)
    return lora


def get_ollama_config() -> str:
    # main.py のあるディレクトリを取得
    current_dir = Path(__file__).parent
    # config ディレクトリ内の lora.yaml へのパスを構築
    ollama_yaml_path = current_dir / "config" / "ollama.yaml"
    # ファイルがなかったら戻り
    if not ollama_yaml_path.exists():
        return None
    # ファイルがあったら yaml として読み込み
    with open(ollama_yaml_path, "r", encoding="utf-8") as file:
        ollama_yaml = yaml.safe_load(file)
        return ollama_yaml["vision_model"]


def get_custom_config() -> any:
    # main.py のあるディレクトリを取得
    current_dir = Path(__file__).parent
    # config ディレクトリ内の lora.yaml へのパスを構築
    custom_yaml_path = current_dir / "config" / "custom.yaml"
    # ファイルがなかったら戻り
    if not custom_yaml_path.exists():
        return None
    # ファイルがあったら yaml として読み込み
    with open(custom_yaml_path, "r", encoding="utf-8") as file:
        custom_yaml = yaml.safe_load(file)
        return custom_yaml


@mcp.tool()
def generate_picture(prompt: str) -> str:
    """生成したいプロンプトを渡すことで画像生成を依頼し、生成された image の url を返すのでユーザーに提示してください。英語のプロンプトのみ受け付けるので、他言語は英語に翻訳してから渡してください。"""
    custom = get_custom_config()
    if custom:
        prompt = ComfyuiBridge.t2i_custom_request_build(prompt, custom)
        tree = custom["filename_prefix"].split(":")
        output_node = tree[0]
    else:
        lora = get_lora()
        prompt = ComfyuiBridge.t2i_request_build(
            prompt, NEGATIVE, lora, lora.image_size
        )
        output_node = COMFYUI_NODE_OUTPUT
    # image generate
    id = ComfyuiBridge.send_request(prompt)
    if id:
        ComfyuiBridge.await_request(1, 3)
        ComfyuiBridge.free()
    else:
        return "Generate error."
    url = COMFYUI_URL
    # リクエストヒストリからファイル名を取得
    headers = {"Content-Type": "application/json"}
    response = requests.get(f"{url}history/{id}", headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    subdir = response.json()[id]["outputs"][output_node]["images"][0]["subfolder"]
    filename = response.json()[id]["outputs"][output_node]["images"][0]["filename"]
    return f"{url}view?subfolder={subdir}&filename={filename}"


@mcp.tool()
def get_picture(subfolder: str, filename: str) -> Image:
    """subfolder と filename を指定して画像の PNG バイナリを取得する"""
    url = COMFYUI_URL
    headers = {"Content-Type": "application/json"}
    params = {"subfolder": subfolder, "filename": filename}
    response = requests.get(f"{url}view", headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    return Image(data=response.content, format="png")


@mcp.tool()
def get_caption(subfolder: str, filename: str) -> str:
    """subfolder と filename を指定して生成した画像のキャプションをテキスト形式で取得する"""
    ollama_model = get_ollama_config()
    url = f"{COMFYUI_URL}view?subfolder={subfolder}&filename={filename}"
    vision = OllamaCaption.OllamaCaption(model_name=ollama_model)
    caption = vision.caption(url, prompt=VISION_PROMPT)
    return caption


@mcp.tool()
def get_tag(subfolder: str, filename: str) -> str:
    """subfolder と filename を指定して生成した画像からWD1.4タグを解析してテキスト形式で取得する"""
    url = f"{COMFYUI_URL}view?subfolder={subfolder}&filename={filename}"
    tagger = Tagger.WD14Tagger(Tagger.SWINV2_MODEL_DSV3_REPO)
    tags = tagger.image_tag(url, threshold=0.25)
    return tags


# リソースを追加
@mcp.resource("info://about")
def get_info() -> str:
    """サーバー情報"""
    return """
    この MCP server は、ComfyUI へのブリッジ機能を提供します。プロンプトを渡すことで画像URLを返します。ユーザーには markdown 画像リンクで URL を表示してください。
    このサーバーはデモ用のMCPサーバーです。
    name: fm-mcp-comfyui-bridge
    version: 0.1.0
    auther: rerofumi
    """


@mcp.resource("help://tools")
def get_tools_help() -> str:
    """ツールのヘルプ"""
    return """
    以下のツールが存在します:
    - generate_picture: 画像生成。プロンプト文字列を渡します。英語のプロンプトのみ受け付けるので、他言語は英語に翻訳してから渡してください。
    """


@mcp.resource("docs://{topic}")
def get_documents(topic: str) -> str:
    """tool のドキュメント"""
    if topic == "generate_picture":
        return """
        プロンプトを渡すことで画像生成を依頼します、生成された画像のURLを返します:
        - iuput
            - prompt: 生成する画像のプロンプト文字列。英語のプロンプトのみ受け付けるので、他言語は英語に翻訳してから渡してください。
        - output
            - image: 生成された画像URLを返します。ユーザーにURLを提示してください。
        """
    else:
        return ""


def main():
    mcp.run()


if __name__ == "__main__":
    main()
