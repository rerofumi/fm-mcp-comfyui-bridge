import datetime
import importlib
import io
import json
import random
import time

import requests
from PIL import Image

from fm_mcp_comfyui_bridge.lora_yaml import SdLoraYaml

# default config value
## API endpoint of ComfyUI
COMFYUI_URL = "http://127.0.0.1:8188/"
## ComfyUI output node
COMFYUI_NODE_OUTPUT = "26"

## Default Workflow
COMFYUI_NODE_CHECKPOINT = "4"
COMFYUI_NODE_LORA_CHECKPOINT = "19"
COMFYUI_NODE_PROMPT = "6"
COMFYUI_NODE_NEGATIVE = "7"
COMFYUI_NODE_SEED = "10"
COMFYUI_NODE_OUTPUT = "26"
COMFYUI_NODE_SIZE = "15"
COMFYUI_NODE_SAMPLING_DISCRETE = "16"
COMFYUI_NODE_SAMPLING_STEPS = "12"
COMFYUI_NODE_SAMPLING_CFG = "10"


class ComfyuiBridge:
    @staticmethod
    def send_request(prompt: str, server_url: str = None) -> str | None:
        # APIにリクエスト送信
        headers = {"Content-Type": "application/json"}
        data = {"prompt": prompt}
        url = server_url if server_url else COMFYUI_URL
        response = requests.post(
            f"{url}prompt",
            headers=headers,
            data=json.dumps(data).encode("utf-8"),
        )
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
        return response.json()["prompt_id"]

    @staticmethod
    def await_request(
        check_interval: float, retry_interval: float, server_url: str = None
    ):
        # 一定時間ごとにリクエストの状態を確認
        url = server_url if server_url else COMFYUI_URL
        while True:
            time.sleep(check_interval)
            headers = {"Content-Type": "application/json"}
            response = requests.get(f"{url}queue", headers=headers)
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.text)
                time.sleep(retry_interval)
                continue
            json_data = response.json()
            if (
                len(json_data.get("queue_running", [])) == 0
                and len(json_data.get("queue_pending", [])) == 0
            ):
                break

    @staticmethod
    def get_image(id: any, server_url: str = None, output_node: str = None):
        url = server_url if server_url else COMFYUI_URL
        if not output_node:
            output_node = COMFYUI_NODE_OUTPUT
        # リクエストヒストリからファイル名を取得
        headers = {"Content-Type": "application/json"}
        response = requests.get(f"{url}history/{id}", headers=headers)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
        subdir = response.json()[id]["outputs"][output_node]["images"][0]["subfolder"]
        filename = response.json()[id]["outputs"][output_node]["images"][0]["filename"]
        headers = {"Content-Type": "application/json"}
        params = {"subfolder": subdir, "filename": filename}
        response = requests.get(f"{url}view", headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
        return Image.open(io.BytesIO(response.content))

    @staticmethod
    def free(server_url: str = None):
        url = server_url if server_url else COMFYUI_URL
        data = {
            "unload_models": True,
            "free_memory": True,
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{url}free", headers=headers, json=data)
        return response

    @staticmethod
    def t2i_request_build(
        prompt: str,
        negative: str,
        lora: SdLoraYaml,
        image_size: tuple[int, int],
    ) -> any:
        with importlib.resources.open_text(
            "fm_mcp_comfyui_bridge.config.workflow", "SDXL_LoRA_Base_API.json"
        ) as f:
            prompt_path = json.load(f)
        # パラメータ埋め込み(workflowによって異なる処理)
        prompt_path[COMFYUI_NODE_CHECKPOINT]["inputs"]["ckpt_name"] = lora.checkpoint
        prompt_path[COMFYUI_NODE_PROMPT]["inputs"]["text"] = prompt
        prompt_path[COMFYUI_NODE_NEGATIVE]["inputs"]["text"] = negative
        prompt_path[COMFYUI_NODE_SEED]["inputs"]["noise_seed"] = random.randint(
            1, 10000000000
        )
        prompt_path[COMFYUI_NODE_SIZE]["inputs"]["width"] = image_size[0]
        prompt_path[COMFYUI_NODE_SIZE]["inputs"]["height"] = image_size[1]
        prompt_path[COMFYUI_NODE_LORA_CHECKPOINT]["inputs"]["lora_name"] = lora.model
        prompt_path[COMFYUI_NODE_LORA_CHECKPOINT]["inputs"]["strength_model"] = (
            lora.strength
        )
        prompt_path[COMFYUI_NODE_LORA_CHECKPOINT]["inputs"]["strength_clip"] = (
            lora.strength
        )
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        prompt_path[COMFYUI_NODE_OUTPUT]["inputs"]["filename_prefix"] = (
            f"{current_date}/Bridge"
        )
        # lora, prediction
        if not lora.lora_enabled:
            prompt_path[COMFYUI_NODE_LORA_CHECKPOINT]["inputs"]["strength_model"] = 0
            prompt_path[COMFYUI_NODE_LORA_CHECKPOINT]["inputs"]["strength_clip"] = 0
        if lora.vpred:
            prompt_path[COMFYUI_NODE_SAMPLING_DISCRETE]["inputs"]["sampling"] = (
                "v_prediction"
            )
        else:
            prompt_path[COMFYUI_NODE_SAMPLING_DISCRETE]["inputs"]["sampling"] = "eps"
        if lora.steps is not None:
            prompt_path[COMFYUI_NODE_SAMPLING_STEPS]["inputs"]["steps"] = lora.steps
        if lora.cfg is not None:
            prompt_path[COMFYUI_NODE_SAMPLING_CFG]["inputs"]["cfg"] = lora.cfg
        return prompt_path

    @staticmethod
    def t2i_custom_request_build(prompt: str, custom_config: any) -> any:
        with importlib.resources.open_text(
            "fm_mcp_comfyui_bridge.config.workflow", custom_config["workflow"]
        ) as f:
            prompt_path = json.load(f)
        # text prompt
        tree = custom_config["text_prompt"].split(":")
        prompt_path[tree[0]][tree[1]][tree[2]] = prompt
        # seed
        tree = custom_config["seed"].split(":")
        prompt_path[tree[0]][tree[1]][tree[2]] = random.randint(1, 10000000000)
        # output prefix
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        tree = custom_config["filename_prefix"].split(":")
        prompt_path[tree[0]][tree[1]][tree[2]] = f"{current_date}/Bridge"
        return prompt_path
