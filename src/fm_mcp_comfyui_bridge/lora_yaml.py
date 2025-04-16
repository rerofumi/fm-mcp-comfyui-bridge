from dataclasses import dataclass, field
from typing import Tuple

import yaml


@dataclass
class SdLoraYaml:
    data: dict = field(default_factory=dict)
    recent_file: str = None

    def read_from_yaml(self, file_path: str):
        """YAMLファイルからデータを読み込む"""
        with open(file_path, "r", encoding="utf-8") as file:
            self.data = yaml.safe_load(file)
        self.recent_file = file_path

    def write_to_yaml(self, file_path: str = None):
        """データをYAMLファイルに書き込む"""
        if file_path is None:
            if self.recent_file is None:
                raise ValueError(
                    "recent_file が設定されていません。file_path を指定してください。"
                )
            file_path = self.recent_file

        with open(file_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(
                self.data, file, default_flow_style=False, allow_unicode=True
            )

    @property
    def lora_enabled(self) -> bool:
        """LoRA モデルの利用スイッチ"""
        return self.data["lora"][0]["enabled"] if "lora" in self.data else False

    @property
    def model(self) -> str:
        """LoRA model filename"""
        return self.data["lora"][0]["model"]

    @property
    def trigger(self) -> str:
        """LoRA trigger word"""
        return self.data["lora"][0]["trigger"]

    @property
    def strength(self) -> float:
        """LoRA strength"""
        return self.data["lora"][0]["strength"]

    @property
    def checkpoint(self) -> str:
        """SDXL checkpoint model"""
        return self.data["checkpoint"]

    @property
    def image_size(self) -> Tuple[int, int]:
        """出力イメージサイズ"""
        image_size = (1024, 1024)
        if "image-size" in self.data:
            image_size = (
                self.data["image-size"]["width"],
                self.data["image-size"]["height"],
            )
        return image_size

    @property
    def vpred(self) -> bool:
        """Vpred mode flag"""
        if "vpred" in self.data:  # Check if 'vpred' key exists in the data dictionary
            return self.data["vpred"]
        else:
            self.data["vpred"] = False  # Set default value to False if not present
            return False

    @property
    def steps(self) -> int:
        """Sampling steps"""
        if "sampling" in self.data and "steps" in self.data["sampling"]:
            return self.data["sampling"]["steps"]
        else:
            return None

    @property
    def cfg(self) -> float:
        """CFG scale"""
        if "sampling" in self.data and "cfg" in self.data["sampling"]:
            return self.data["sampling"]["cfg"]
        else:
            return None
