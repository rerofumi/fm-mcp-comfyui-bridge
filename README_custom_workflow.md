# Custom Workflow についての解説と使い方

## ComfyUI API の仕様について

ComfyUI API を使用して画像を生成するには、API 形式の Workflow JSON ファイルが必要です。
この JSON ファイルを ComfyUI API に POST することで画像が生成されます。

Workflow JSON ファイルには、画像生成に必要な全てのパラメータ（テキストプロンプト、Seed値、出力ファイル名など）が含まれています。
そのため、異なるパラメータで画像を生成したい場合、例えばテキストプロンプトを変更したい場合は、JSON ファイル内の該当箇所を書き換えてから API に POST する必要があります。
Seed 値も同様に、毎回 JSON ファイルに設定する必要があります。
つまり、ComfyUI API を利用するということは、この Workflow JSON ファイルを動的に編集して利用するということです。

## ComfyUI で API 形式の Workflow JSON を作成する

1.  ComfyUI の設定画面で「Enable Dev mode Options」を有効にします。
2.  Workflow を作成または読み込みます。
3.  画面下部のメニューに表示される「Save (API Format)」ボタンをクリックして、API 形式の Workflow JSON ファイルを保存します。

## Workflow JSON を確認する

カスタムワークフロー機能では、API 形式の Workflow JSON ファイル内の以下の3つのパラメータを、実行時に指定した値で書き換えます。

*   テキストプロンプト (Text Prompt)
*   乱数シード (Random Seed)
*   出力ファイル名のプレフィックス (Output Prefix)

テキストエディタなどで Workflow JSON ファイルを開き、これらのパラメータが JSON 内のどの場所にあるかを確認し、その位置情報を `custom.yaml` に設定します。

### テキストプロンプト (Text Prompt) の場所

以下のような場所に記述されています。

```json:例: flux1-dev-API.json
  },
  "6": {
    "inputs": {
      "text": "A high-quality 3D avatar image, resembling a VRChat screenshot. The avatar is a popular kemono-ear (animal ear) girl model in Japan. The design is elaborate and decorative, with a pastel color scheme accented by vibrant pink, light blue, lavender, and yellow.  Detailed decorations such as ribbons, ruffles, lace, and beads are meticulously applied. The background is a 3D-modeled room with warm-toned lighting, creating a cute and inviting atmosphere. The avatar is winking with one eye and giving a peace sign with the other hand, smiling broadly at the camera. The expression is lively and approachable. Soft, diffused lighting is used to gently illuminate the avatar and the entire room.",
      "clip": [
        "11",
```

この場合、`custom.yaml` には以下のように記述します。

```yaml
text_prompt: "6:inputs:text"
```

`:` 区切りで JSON 内の階層構造を指定します。この例では、ノード `6` の `inputs` オブジェクト内の `text` フィールドを指しています。

### 乱数シード (Random Seed) の場所

以下のような場所に記述されています。

```json:例: flux1-dev-API.json
  "25": {
    "inputs": {
      "noise_seed": 322280786095220
    },
```

この場合、`custom.yaml` には以下のように記述します。

```yaml
seed: "25:inputs:noise_seed"
```

ノード `25` の `inputs` オブジェクト内の `noise_seed` フィールドを指しています。

### 出力ファイル名のプレフィックス (Filename Prefix) の場所

以下のような場所に記述されています。

```json:例: flux1-dev-API.json
  "9": {
    "inputs": {
      "filename_prefix": "2025-04-17/flux",
      "images": [
```

この場合、`custom.yaml` には以下のように記述します。

```yaml
filename_prefix: "9:inputs:filename_prefix"
```

ノード `9` の `inputs` オブジェクト内の `filename_prefix` フィールドを指しています。

## custom.yaml の設定

確認した Workflow JSON ファイル名と、各パラメータの位置情報を `custom.yaml` というファイルに記述します。
作成した `custom.yaml` ファイルは、`src/fm_mcp_comfyui_bridge/config/` ディレクトリ、または `example/` ディレクトリなどに設置してください。
（プログラムは起動時にこれらの場所から `custom.yaml` を探します）

```yaml:例: custom.yaml
workflow: "flux1-dev-API.json" # 使用するWorkflow JSONファイル名
text_prompt: "6:inputs:text"     # テキストプロンプトの場所
seed: "25:inputs:noise_seed"     # Seed値の場所
filename_prefix: "9:inputs:filename_prefix" # ファイル名プレフィックスの場所
