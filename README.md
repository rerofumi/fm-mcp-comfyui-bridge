# fm-mcp-comfyui-bridge

![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

ComfyUIにアクセスするためのMCPサーバー実装です。このサーバーは[fm_comfyui_bridge](https://github.com/rerofumi/fm_comfyui_bridge)モジュールを使用してComfyUIとの連携を行い、画像生成機能を提供します。

## 🌟 機能

- 🖼️ ComfyUIを利用した画像生成機能
- 📝 生成画像のキャプション生成機能
- 🏷️ 生成画像のタグ解析機能
- 🔄 uvによる簡単なセットアップと起動
- 🌐 MCPサーバーとしてAPIエンドポイントを提供

## 🔧 要件

- Python 3.13以上
- ローカルで動作するComfyUI（デフォルト: http://localhost:8188）
- [uv](https://github.com/astral-sh/uv) パッケージマネージャ

## 📥 インストール

uv がインストールされた環境を用意してください。

### uvを使用したインストール

```bash
# リポジトリをクローン
git clone https://github.com/rerofumi/fm-mcp-comfyui-bridge.git
cd fm-mcp-comfyui-bridge

# uvを使用して依存関係をインストール
uv pip install -e .
```


## 🚀 使用方法

### MCPサーバーとして設定

利用するエージェントツールのMCP設定に以下のように設定してください

```
{
  "mcpServers": {
    "fm-mcp-comfyui-bridge": {
      "command": "uv",
      "args": [
        "--directory",
        "(インストールしたディレクトリ)/fm-mcp-comfyui-bridge",
        "run",
        "fm-mcp-comfyui-bridge"
      ],
    }
  }
}
```

### ComfyUIのエンドポイント設定

デフォルトでは、ComfyUIのエンドポイントは `http://localhost:8188` に設定されています。必要に応じて `main.py` 内の設定を変更してください。

### Loraの設定

画像生成に使用するモデル設定ファイルを作成する必要があります。以下の手順で設定を行ってください：

1. サンプル設定ファイルをコピーします：
   ```bash
   cp src/fm_mcp_comfyui_bridge/config/sample_lora.yaml src/fm_mcp_comfyui_bridge/config/lora.yaml
   ```

2. コピーした `lora.yaml` ファイルを編集して、使用するモデル名を設定します：
   ```yaml
   checkpoint: (使いたいチェックポイントモデル名).safetensors
   image-size:
     height: 1024
     width: 1024
   lora:
   - enabled: false
     model: (使いたいLoRAモデル名).safetensors
     strength: 1.0
     trigger: 
   sampling:
     cfg: 5
     steps: 24
   vpred: true
   vision_model: gemma3:27b
   ```

3. 設定項目の説明：
   - `checkpoint`: 使用する基本モデルのファイル名（例：`animagine-xl-3.0.safetensors`）
   - `image-size`: 生成する画像のサイズ設定
   - `lora`: LoRAモデルの設定
     - `enabled`: LoRAを有効にするかどうか（`true`または`false`）
     - `model`: 使用するLoRAモデルのファイル名
     - `strength`: LoRAの適用強度（0.0〜1.0）
     - `trigger`: LoRAのトリガーワード
   - `sampling`: サンプリング設定
     - `cfg`: CFGスケール値
     - `steps`: 生成ステップ数
   - `vpred`: v-predictionを使用するかどうか
   - `vision_model`: 画像解析でキャプションを生成する ollama の vision 対応モデル名


モデルファイルはComfyUIの適切なディレクトリに配置されている必要があります。

### 利用可能なツール

1. **generate_picture** - プロンプトに基づいて画像を生成
   ```python
   @mcp.tool()
   def generate_picture(prompt: str) -> str:
       """生成したいプロンプトを渡すことで画像生成を依頼し、生成された image の url を返す"""
   ```

2. **get_picture** - 指定された画像のPNGバイナリデータを取得
   ```python
   @mcp.tool()
   def get_picture(subfolder: str, filename: str) -> Image:
       """subfolder と filename を指定して画像の PNG バイナリを取得する"""
   ```

3. **get_caption** - 画像のキャプションをテキスト形式で取得
   ```python
   @mcp.tool()
   def get_caption(subfolder: str, filename: str) -> str:
       """subfolder と filename を指定して生成した画像のキャプションをテキスト形式で取得する"""
   ```

4. **get_tag** - 画像からWD1.4タグを解析して取得
   ```python
   @mcp.tool()
   def get_tag(subfolder: str, filename: str) -> str:
       """subfolder と filename を指定して生成した画像からWD1.4タグを解析してテキスト形式で取得する"""
   ```

### APIリソース

```python
@mcp.resource("info://about")
def get_info() -> str:
    """サーバー情報"""

@mcp.resource("help://tools")
def get_tools_help() -> str:
    """ツールのヘルプ"""

@mcp.resource("docs://{topic}")
def get_documents(topic: str) -> str:
    """tool のドキュメント"""
```

## 📚 依存関係

主な依存関係は以下の通りです：

- `fm-comfyui-bridge>=0.7.0` - ComfyUIとの連携モジュール
- `mcp[cli]>=1.6.0` - MCPサーバーフレームワーク
- `requests>=2.32.3` - HTTPリクエスト処理
- `huggingface-hub>=0.25.2` - Hugging Faceモデルリポジトリアクセス
- `numpy>=2.1.2` - 数値計算ライブラリ
- `ollama>=0.3.3` - ローカルLLMサポート
- `onnxruntime>=1.19.2` - ONNXモデル実行環境
- `pandas>=2.2.3` - データ分析ライブラリ

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細については[LICENSE](LICENSE)ファイルを参照してください。

## 👤 作者

- **rerofumi** - [GitHub](https://github.com/rerofumi) - rero2@yuumu.org

---

**fm-mcp-comfyui-bridge** は[fm_comfyui_bridge](https://github.com/rerofumi/fm_comfyui_bridge)モジュールを活用したプロジェクトです。

WD1.4タグ解析部分は SmilingWolf 氏作成の [wd-tagger](https://huggingface.co/spaces/SmilingWolf/wd-tagger/tree/main) のソースコードとモデルデータを使用しています。モデルデータは初回実行時にダウンロードされます。


