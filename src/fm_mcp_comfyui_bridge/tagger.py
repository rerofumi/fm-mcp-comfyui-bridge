# This code was created with reference to the following source code:
#   Predict.py in the SmilingWolf/wd-tagger repository of HaggingFace
#   https://huggingface.co/spaces/SmilingWolf/wd-tagger/tree/main
#
# The model used is from SmilingWolf.
# The necessary models will be downloaded at runtime.

import huggingface_hub
import numpy as np
import onnxruntime as rt
import pandas as pd
import requests
import io
from PIL import Image

# Dataset v3 series of models:
SWINV2_MODEL_DSV3_REPO = "SmilingWolf/wd-swinv2-tagger-v3"
CONV_MODEL_DSV3_REPO = "SmilingWolf/wd-convnext-tagger-v3"
VIT_MODEL_DSV3_REPO = "SmilingWolf/wd-vit-tagger-v3"
VIT_LARGE_MODEL_DSV3_REPO = "SmilingWolf/wd-vit-large-tagger-v3"
EVA02_LARGE_MODEL_DSV3_REPO = "SmilingWolf/wd-eva02-large-tagger-v3"

# Dataset v2 series of models:
MOAT_MODEL_DSV2_REPO = "SmilingWolf/wd-v1-4-moat-tagger-v2"
SWIN_MODEL_DSV2_REPO = "SmilingWolf/wd-v1-4-swinv2-tagger-v2"
CONV_MODEL_DSV2_REPO = "SmilingWolf/wd-v1-4-convnext-tagger-v2"
CONV2_MODEL_DSV2_REPO = "SmilingWolf/wd-v1-4-convnextv2-tagger-v2"
VIT_MODEL_DSV2_REPO = "SmilingWolf/wd-v1-4-vit-tagger-v2"

# Files to download from the repos
MODEL_FILENAME = "model.onnx"
LABEL_FILENAME = "selected_tags.csv"


class WD14Tagger:
    def __init__(self, model_repo):
        self.model_target_size = None
        self.last_loaded_repo = None
        # model download
        csv_path = huggingface_hub.hf_hub_download(
            model_repo,
            LABEL_FILENAME,
        )
        model_path = huggingface_hub.hf_hub_download(
            model_repo,
            MODEL_FILENAME,
        )
        tags_df = pd.read_csv(csv_path)
        name_series = tags_df["name"]
        self.tag_names = name_series.tolist()
        self.general_indexes = list(np.where(tags_df["category"] == 0)[0])
        model = rt.InferenceSession(model_path)
        _, height, width, _ = model.get_inputs()[0].shape
        self.model_target_size = max(height, width)
        self.last_loaded_repo = model_repo
        self.model = model

    def prepare_image(self, image_path):
        # URLからの画像読み込みに対応
        if image_path.startswith(('http://', 'https://')):
            # URLから画像をダウンロード
            response = requests.get(image_path, stream=True)
            response.raise_for_status()  # エラーがあれば例外を発生
            # BytesIOを使ってメモリ上でファイルとして扱う
            image = Image.open(io.BytesIO(response.content))
        else:
            # 通常のファイルパスからの読み込み
            image = Image.open(image_path)
            
        original_width, original_height = image.size
        # image resizing and padding to fit model input size (256x256 is a typical value for ResNet-like models, but it can be any other)
        aspect_ratio = min(
            self.model_target_size / original_width,
            self.model_target_size / original_height,
        )
        new_size = (
            int(original_width * aspect_ratio),
            int(original_height * aspect_ratio),
        )
        resized_image = image.resize(new_size, Image.LANCZOS)
        square_image = Image.new(
            "RGB", (self.model_target_size, self.model_target_size), (255, 255, 255)
        )
        paste_position = (
            (self.model_target_size - new_size[0]) // 2,
            (self.model_target_size - new_size[1]) // 2,
        )
        square_image.paste(resized_image, paste_position)
        # Convert to numpy array
        image_array = np.asarray(square_image, dtype=np.float32)
        # Convert PIL-native RGB to BGR
        image_array = image_array[:, :, ::-1]
        return np.expand_dims(image_array, axis=0)

    def tagging(self, input, threshold=0.35):
        # run model
        input_name = self.model.get_inputs()[0].name
        label_name = self.model.get_outputs()[0].name
        preds = self.model.run([label_name], {input_name: input})[0]
        # collect labels
        labels = list(zip(self.tag_names, preds[0].astype(float)))
        general_names = [labels[i] for i in self.general_indexes]
        general_res = [x for x in general_names if x[1] > threshold]
        general_res = dict(general_res)
        sorted_general_strings = sorted(
            general_res.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        #
        sorted_general_strings = [x[0] for x in sorted_general_strings]
        sorted_general_strings = (
            ", ".join(sorted_general_strings).replace("(", "\(").replace(")", "\)")
        )
        return sorted_general_strings

    def image_tag(self, image_path, threshold=0.35):
        image = self.prepare_image(image_path)
        return self.tagging(image, threshold)
