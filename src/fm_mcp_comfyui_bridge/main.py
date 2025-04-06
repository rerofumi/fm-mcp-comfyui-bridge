import io
from mcp.server.fastmcp import FastMCP, Image
from fm_comfyui_bridge.bridge import (
    free,
    generate,
)
from fm_comfyui_bridge.lora_yaml import SdLoraYaml

NEGATIVE = '''
worst quality, bad quality, low quality, lowres, scan artifacts, jpeg artifacts, sketch,
light particles, jpeg artifacts, unfinished, oldest, old, abstract, signature
'''

HOST = "http://localhost:8188"

# MCPサーバーを作成
mcp = FastMCP("fm-mcp-comfyui-bridge")


@mcp.tool()
def generate_picture(prompt: str) -> Image:
    """ 生成したいプロンプトを渡すことで画像生成を依頼し、生成された png image の byteformat を返します。英語のプロンプトのみ受け付けるので、他言語は英語に翻訳してから渡してください。 """
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
    img = generate(
        prompt,
        NEGATIVE,
        lora,
        (1024, 1024)
    )
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return Image(data=buffer.getvalue(), format="png")


# リソースを追加
@mcp.resource("info://about")
def get_info() -> str:
    """サーバー情報"""
    return """
    この MCP server は、ComfyUI へのブリッジ機能を提供します。プロンプトを渡すことで画像バイナリデータを返します。
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
        プロンプトを渡すことで画像生成を依頼します、生成された png image の byteformat を返します:
        - iuput
            - prompt: 生成する画像のプロンプト文字列。英語のプロンプトのみ受け付けるので、他言語は英語に翻訳してから渡してください。
        - output
            - image: 生成された png image の byteformat
        """
    else:
        return ""
        

def main():
    mcp.run()

if __name__ == "__main__":
    main()
