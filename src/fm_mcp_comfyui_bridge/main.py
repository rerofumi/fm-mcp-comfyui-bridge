import fm_comfyui_bridge.config as config
import requests
from fm_comfyui_bridge.bridge import (
    await_request,
    free,
    send_request,
    t2i_request_build,
)
from fm_comfyui_bridge.lora_yaml import SdLoraYaml
from mcp.server.fastmcp import FastMCP, Image

NEGATIVE = """
worst quality, bad quality, low quality, lowres, scan artifacts, jpeg artifacts, sketch,
light particles, jpeg artifacts, unfinished, oldest, old, abstract, signature
"""

HOST = "http://localhost:8188"

# MCPサーバーを作成
mcp = FastMCP("fm-mcp-comfyui-bridge")


@mcp.tool()
def generate_picture(prompt: str) -> str:
    """生成したいプロンプトを渡すことで画像生成を依頼し、生成された image の url を返すのでユーザーに提示してください。英語のプロンプトのみ受け付けるので、他言語は英語に翻訳してから渡してください。"""
    lora = SdLoraYaml()
    lora.data = {
        "checkpoint": "zukiAnimeILL_v40.safetensors",
        "vpred": False,
        "image-size": {
            "width": 1024,
            "height": 1024,
        },
        "lora": [
            {
                "enabled": False,
                "model": "lora-ix-momoshiro_mix-v1.safetensors",
                "trigger": "momoshiro_mix",
                "strength": 1.0,
            }
        ],
    }
    # image generate
    id = send_request(t2i_request_build(prompt, NEGATIVE, lora, (1024, 1024)))
    if id:
        await_request(1, 3)
        free()
    else:
        return "Generate error."
    url = config.COMFYUI_URL
    output_node = config.COMFYUI_NODE_OUTPUT
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
    url = config.COMFYUI_URL
    headers = {"Content-Type": "application/json"}
    params = {"subfolder": subfolder, "filename": filename}
    response = requests.get(f"{url}view", headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    return Image(data=response.content, format="png")


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
