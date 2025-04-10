import io
from pathlib import Path

import ollama
import requests
from PIL import Image


class OllamaCaption:
    """
    OllamaのVisionモデルを使用して画像からキャプションを生成するクラス。

    Attributes:
        model_name (str): 使用するOllamaのVisionモデル名 (デフォルト: "llava")。
    """

    def __init__(self, model_name: str = "llama3.2-vision:latest"):
        """
        OllamaCaptionクラスのインスタンスを初期化します。

        Args:
            model_name (str): 使用するOllamaのVisionモデル名。
                               デフォルトは "llava" です。
                               指定するモデルは事前にOllamaにインストールされている必要があります。
                               (例: `ollama run llava`)
        """
        self.model_name = model_name
        # モデルが存在するか簡単なチェック（オプション）
        try:
            ollama.show(model_name)
        except ollama.ResponseError as e:
            print(
                f"警告: モデル '{model_name}' がOllamaに見つからないか、アクセスできません。"
            )
            print(f"エラー詳細: {e}")
            print(
                "続行しますが、captionメソッド呼び出し時にエラーが発生する可能性があります。"
            )
        except Exception as e:
            print(f"Ollamaとの通信中に予期せぬエラーが発生しました: {e}")

    def _load_image(self, image_source: str) -> Image.Image | None:
        """
        指定されたソース（URLまたはファイルパス）から画像を読み込み、
        Pillow Imageオブジェクトを返します。

        Args:
            image_source (str): 画像のURLまたはローカルファイルパス。

        Returns:
            Image.Image | None: 読み込まれたPillow Imageオブジェクト。
                                読み込みに失敗した場合はNone。
        """
        try:
            if image_source.startswith(("http://", "https://")):
                # URLから画像をダウンロード
                response = requests.get(
                    image_source, stream=True, timeout=10
                )  # タイムアウトを追加
                response.raise_for_status()  # HTTPエラーがあれば例外を発生
                # BytesIOを使ってメモリ上でファイルとして扱う
                img = Image.open(io.BytesIO(response.content))
                print(f"画像URLから読み込み成功: {image_source}")
                return img
            else:
                # ローカルファイルパスから画像を読み込み
                image_path = Path(image_source)
                if not image_path.is_file():
                    print(f"エラー: ファイルが見つかりません: {image_path}")
                    return None
                img = Image.open(image_path)
                print(f"画像ファイルから読み込み成功: {image_path}")
                return img
        except requests.exceptions.RequestException as e:
            print(
                f"エラー: URLからの画像ダウンロードに失敗しました: {image_source}, 詳細: {e}"
            )
            return None
        except FileNotFoundError:
            print(f"エラー: ファイルが見つかりません: {image_source}")
            return None
        except IOError as e:
            print(
                f"エラー: 画像ファイルの読み込みまたは形式が無効です: {image_source}, 詳細: {e}"
            )
            return None
        except Exception as e:
            print(
                f"エラー: 画像読み込み中に予期せぬエラーが発生しました: {image_source}, 詳細: {e}"
            )
            return None

    def caption(
        self, image_source: str, prompt: str = "Describe this image in detail:"
    ) -> str | None:
        """
        指定された画像ソースからキャプションを生成します。

        Args:
            image_source (str): 画像のURLまたはローカルファイルパス。
            prompt (str): Ollamaモデルに渡すプロンプト。
                          デフォルトは "Describe this image in detail:"。

        Returns:
            str | None: 生成されたキャプション文字列。エラーが発生した場合はNone。
        """
        img = self._load_image(image_source)
        if img is None:
            return None  # 画像読み込み失敗

        # Pillow Imageオブジェクトをバイト列に変換 (PNG形式)
        buffer = io.BytesIO()
        try:
            # 画像をRGBに変換（アルファチャンネルがある場合などに対応）
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(buffer, format="PNG")
        except Exception as e:
            print(f"エラー: 画像をバイト列に変換中にエラーが発生しました: {e}")
            return None
        image_bytes = buffer.getvalue()

        try:
            print(
                f"Ollamaモデル '{self.model_name}' を使用してキャプション生成を開始します..."
            )
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image_bytes],  # バイト列を渡す
                    }
                ],
            )
            print("キャプション生成成功。")
            # レスポンスからキャプションテキストを抽出
            if response and "message" in response and "content" in response["message"]:
                return response["message"]["content"].strip()
            else:
                print(
                    "エラー: Ollamaからのレスポンス形式が予期されたものではありません。"
                )
                print(f"レスポンス: {response}")
                return None
        except ollama.ResponseError as e:
            print("エラー: Ollama API呼び出し中にエラーが発生しました。")
            print(f"ステータスコード: {e.status_code}")
            print(f"エラー詳細: {e.error}")
            # モデルが存在しない場合などの具体的なエラーメッセージを表示
            if "model not found" in e.error.lower():
                print(
                    f"ヒント: モデル '{self.model_name}' がOllamaに存在しません。`ollama run {self.model_name}` を実行してダウンロードしてください。"
                )
            elif "connection refused" in e.error.lower():
                print(
                    "ヒント: Ollamaサーバーが実行されていないか、アクセスできません。Ollamaが起動していることを確認してください。"
                )
            return None
        except Exception as e:
            print(f"エラー: キャプション生成中に予期せぬエラーが発生しました: {e}")
            return None


# --- 使用例 ---
if __name__ == "__main__":
    # OllamaCaption インスタンスを作成 (デフォルトモデル "llava" を使用)
    # もし別のモデルを使いたい場合は model_name="your_model_name" のように指定
    captioner = OllamaCaption()
    # captioner = OllamaCaption(model_name="llava:latest") # 特定バージョン指定も可能

    # 1. URLからキャプション生成
    # 例: 有名な画像URL (動作確認用)
    image_url = "https://ollama.com/public/ollama.png"
    print(f"\n--- URLからのキャプション生成 ({image_url}) ---")
    caption_from_url = captioner.caption(image_url)
    if caption_from_url:
        print("\n生成されたキャプション:")
        print(caption_from_url)
    else:
        print("\nURLからのキャプション生成に失敗しました。")

    # 2. ローカルファイルからキャプション生成
    # この例を実行するには、カレントディレクトリに 'test_image.jpg' のような
    # 画像ファイルを配置してください。
    local_image_path = "test_image.jpg"  # 存在しないパスや画像でないファイルを指定してエラーテストも可能
    print(f"\n--- ローカルファイルからのキャプション生成 ({local_image_path}) ---")

    # ダミーファイルの作成 (テスト用、もしファイルがなければ)
    dummy_file_created = False
    if not Path(local_image_path).exists():
        try:
            print(
                f"'{local_image_path}' が見つからないため、ダミーの単色画像を生成します..."
            )
            dummy_img = Image.new("RGB", (60, 30), color="red")
            dummy_img.save(local_image_path)
            dummy_file_created = True
            print("ダミー画像を生成しました。")
        except Exception as e:
            print(f"ダミー画像の生成に失敗しました: {e}")

    caption_from_file = captioner.caption(
        local_image_path, prompt="What is in this picture?"
    )  # プロンプトも変更可能
    if caption_from_file:
        print("\n生成されたキャプション:")
        print(caption_from_file)
    else:
        print("\nローカルファイルからのキャプション生成に失敗しました。")

    # ダミーファイルを削除
    if dummy_file_created:
        try:
            Path(local_image_path).unlink()
            print(f"\nダミーファイル '{local_image_path}' を削除しました。")
        except Exception as e:
            print(f"ダミーファイルの削除に失敗しました: {e}")

    # 3. 存在しないファイルパスでのエラーテスト
    non_existent_path = "path/to/non_existent_image.png"
    print(f"\n--- 存在しないファイルパスでのテスト ({non_existent_path}) ---")
    caption_non_existent = captioner.caption(non_existent_path)
    if caption_non_existent is None:
        print("期待通り、存在しないファイルからのキャプション生成は失敗しました。")

    # 4. 無効なURLでのエラーテスト
    invalid_url = "http://invalid-url-that-does-not-exist-abcxyz.com/image.jpg"
    print(f"\n--- 無効なURLでのテスト ({invalid_url}) ---")
    caption_invalid_url = captioner.caption(invalid_url)
    if caption_invalid_url is None:
        print("期待通り、無効なURLからのキャプション生成は失敗しました。")
