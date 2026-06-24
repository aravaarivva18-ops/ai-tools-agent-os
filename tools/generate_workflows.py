import json
import os


class ComfyUIWorkflowBuilder:
    def __init__(self):
        self.nodes = {}
        self.links = []
        self.next_link_id = 1

    def add_node(self, node_id, node_type, pos, size, widgets=None):
        self.nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "pos": pos,
            "size": size,
            "flags": {},
            "order": node_id,
            "mode": 0,
            "inputs": [],
            "outputs": [],
            "properties": {"Node name for S&G": node_type},
            "widgets_values": widgets or [],
        }
        return node_id

    def add_input(self, node_id, name, type_, link=None):
        node = self.nodes[node_id]
        node["inputs"].append({"name": name, "type": type_, "link": link})

    def add_output(self, node_id, name, type_, links=None):
        node = self.nodes[node_id]
        node["outputs"].append(
            {
                "name": name,
                "type": type_,
                "links": links or [],
                "slot_index": len(node["outputs"]),
            }
        )

    def connect(
        self, from_node_id, from_output_name, to_node_id, to_input_name, type_string
    ):
        from_node = self.nodes[from_node_id]
        to_node = self.nodes[to_node_id]

        # Check if output exists, if not add it
        from_slot_idx = None
        for i, out in enumerate(from_node["outputs"]):
            if out["name"] == from_output_name:
                from_slot_idx = i
                break
        if from_slot_idx is None:
            self.add_output(from_node_id, from_output_name, type_string)
            from_slot_idx = len(from_node["outputs"]) - 1

        # Check if input exists, if not add it
        to_slot_idx = None
        for i, inp in enumerate(to_node["inputs"]):
            if inp["name"] == to_input_name:
                to_slot_idx = i
                break
        if to_slot_idx is None:
            self.add_input(to_node_id, to_input_name, type_string)
            to_slot_idx = len(to_node["inputs"]) - 1

        link_id = self.next_link_id
        self.next_link_id += 1

        self.links.append(
            [link_id, from_node_id, from_slot_idx, to_node_id, to_slot_idx, type_string]
        )

        from_node["outputs"][from_slot_idx]["links"].append(link_id)
        to_node["inputs"][to_slot_idx]["link"] = link_id

    def build(self):
        return {
            "last_node_id": max(self.nodes.keys()) if self.nodes else 0,
            "last_link_id": self.next_link_id - 1,
            "nodes": list(self.nodes.values()),
            "links": self.links,
            "groups": [],
            "config": {},
            "extra": {"ds": {"scale": 1.0, "offset": [0, 0]}},
            "version": 0.4,
        }


def create_photo_workflow():
    builder = ComfyUIWorkflowBuilder()

    # Checkpoint loader
    builder.add_node(
        1,
        "CheckpointLoaderSimple",
        [50, 150],
        [300, 120],
        ["juggernautXL_v9RdPhoto2Lightning.safetensors"],
    )
    # Reference image (Face)
    builder.add_node(2, "LoadImage", [50, 320], [300, 250], ["input_face.png", "image"])
    # Pose image
    builder.add_node(3, "LoadImage", [50, 620], [300, 250], ["input_pose.png", "image"])

    # CLIP text encodes
    builder.add_node(
        4,
        "CLIPTextEncode",
        [400, 50],
        [400, 150],
        [
            "a professional photo of a beautiful influencer girl, 8k resolution, photorealistic, highly detailed face, professional studio lighting, depth of field, looking at camera"
        ],
    )
    builder.add_node(
        5,
        "CLIPTextEncode",
        [400, 240],
        [400, 150],
        [
            "nsfw, deformed, bad anatomy, disfigured, poorly drawn face, blurry, low quality, worst quality, ugly, cartoon, painting, illustration"
        ],
    )

    # Latent image
    builder.add_node(6, "EmptyLatentImage", [850, 50], [300, 120], [1024, 1024, 1])

    # OpenPose loader and preprocessor
    builder.add_node(
        7,
        "ControlNetLoader",
        [400, 430],
        [300, 80],
        ["controlnet-openpose-sdxl.safetensors"],
    )
    builder.add_node(
        8, "OpenposePreprocessor", [400, 540], [300, 150], [512, "yes", "yes", "no"]
    )
    # Apply OpenPose ControlNet
    builder.add_node(
        9, "ControlNetApplyAdvanced", [750, 430], [300, 200], [1.0, 0.0, 1.0]
    )

    # InstantID Loaders
    builder.add_node(
        10, "InstantIDModelLoader", [1100, 400], [300, 80], ["ip-adapter.bin"]
    )
    builder.add_node(
        11,
        "ControlNetLoader",
        [1100, 500],
        [300, 80],
        ["control_instant_id_sdxl.safetensors"],
    )
    builder.add_node(
        12, "InsightFaceLoader", [1100, 600], [300, 80], ["provider", "CPU"]
    )
    # Apply InstantID
    builder.add_node(13, "ApplyInstantID", [1450, 400], [320, 240], [1.0, 0.0, 1.0])

    # IP-Adapter FaceID Loader
    builder.add_node(
        14,
        "IPAdapterModelLoader",
        [1100, 50],
        [300, 80],
        ["ip-adapter-faceid-plusv2_sdxl.bin"],
    )
    builder.add_node(
        15, "CLIPVisionLoader", [1100, 150], [300, 80], ["clip_vision_g.safetensors"]
    )
    # FaceID Lora loader
    builder.add_node(
        16,
        "LoraLoader",
        [1450, 50],
        [300, 140],
        ["ip-adapter-faceid-plusv2_sdxl_lora.safetensors", 0.6, 0.6],
    )
    # Apply IP-Adapter FaceID (IPAdapterAdvanced)
    builder.add_node(
        17,
        "IPAdapterAdvanced",
        [1800, 50],
        [300, 200],
        [0.7, "standard", "concat", 0.0, 1.0, "V only"],
    )

    # KSampler
    builder.add_node(
        18,
        "KSampler",
        [1850, 400],
        [300, 260],
        [123456789, "randomize", 30, 7.0, "euler", "normal", 1.0],
    )
    # VAE Decode
    builder.add_node(19, "VAEDecode", [2200, 400], [200, 100])

    # FaceDetailer (Impact Pack)
    builder.add_node(
        20,
        "UltralyticsDetectorProvider",
        [2150, 250],
        [300, 80],
        ["bbox/face_yolov8m.pt"],
    )
    builder.add_node(
        21,
        "FaceDetailer",
        [2500, 300],
        [320, 280],
        [
            1024,
            "bbox",
            1024,
            987654321,
            "randomize",
            20,
            6.0,
            "euler",
            "normal",
            0.45,
            10,
            "no",
            "no",
        ],
    )

    # Ultimate SD Upscale (4K)
    builder.add_node(
        22, "UpscaleModelLoader", [2500, 50], [300, 80], ["4x-UltraSharp.pth"]
    )
    builder.add_node(
        23,
        "UltimateSDUpscale",
        [2900, 50],
        [320, 300],
        [2.0, "linear", 512, 512, 32, 32, "None", "euler", "normal", 20, 0.35],
    )
    # Save Image
    builder.add_node(
        24, "SaveImage", [3270, 50], [300, 250], ["ComfyUI_influencer_photo"]
    )

    # CONNECTIONS
    # Pos/Neg conditioning chain through OpenPose
    builder.connect(4, "CONDITIONING", 9, "positive", "CONDITIONING")
    builder.connect(5, "CONDITIONING", 9, "negative", "CONDITIONING")
    builder.connect(7, "CONTROL_NET", 9, "control_net", "CONTROL_NET")
    builder.connect(3, "IMAGE", 8, "image", "IMAGE")
    builder.connect(8, "IMAGE", 9, "image", "IMAGE")

    # Connect OpenPose output to InstantID
    builder.connect(10, "INSTANTID", 13, "instantid", "INSTANTID")
    builder.connect(12, "INSIGHTFACE", 13, "insightface", "INSIGHTFACE")
    builder.connect(11, "CONTROL_NET", 13, "control_net", "CONTROL_NET")
    builder.connect(2, "IMAGE", 13, "image", "IMAGE")
    builder.connect(1, "MODEL", 13, "model", "MODEL")
    builder.connect(9, "positive", 13, "positive", "CONDITIONING")
    builder.connect(9, "negative", 13, "negative", "CONDITIONING")

    # Connect InstantID output model to FaceID Lora loader
    builder.connect(13, "model", 16, "model", "MODEL")
    builder.connect(1, "CLIP", 16, "clip", "CLIP")

    # Connect Lora CLIP to Prompts
    builder.connect(16, "clip", 4, "clip", "CLIP")
    builder.connect(16, "clip", 5, "clip", "CLIP")

    # Connect Lora model output to IP-Adapter FaceID Apply
    builder.connect(16, "model", 17, "model", "MODEL")
    builder.connect(14, "IPADAPTER", 17, "ipadapter", "IPADAPTER")
    builder.connect(2, "IMAGE", 17, "image", "IMAGE")
    builder.connect(15, "CLIP_VISION", 17, "clip_vision", "CLIP_VISION")

    # KSampler inputs
    builder.connect(17, "model", 18, "model", "MODEL")
    builder.connect(13, "positive", 18, "positive", "CONDITIONING")
    builder.connect(13, "negative", 18, "negative", "CONDITIONING")
    builder.connect(6, "LATENT", 18, "latent_image", "LATENT")

    # VAE Decode
    builder.connect(18, "LATENT", 19, "samples", "LATENT")
    builder.connect(1, "VAE", 19, "vae", "VAE")

    # FaceDetailer
    builder.connect(19, "IMAGE", 21, "image", "IMAGE")
    builder.connect(17, "model", 21, "model", "MODEL")
    builder.connect(16, "clip", 21, "clip", "CLIP")
    builder.connect(1, "VAE", 21, "vae", "VAE")
    builder.connect(20, "BBOX_DETECTOR", 21, "bbox_detector", "BBOX_DETECTOR")

    # Ultimate SD Upscale
    builder.connect(21, "image", 23, "image", "IMAGE")
    builder.connect(17, "model", 23, "model", "MODEL")
    builder.connect(13, "positive", 23, "positive", "CONDITIONING")
    builder.connect(13, "negative", 23, "negative", "CONDITIONING")
    builder.connect(1, "VAE", 23, "vae", "VAE")
    builder.connect(22, "UPSCALE_MODEL", 23, "upscale_model", "UPSCALE_MODEL")

    # Save Image
    builder.connect(23, "IMAGE", 24, "images", "IMAGE")

    return builder.build()


def create_video_workflow():
    builder = ComfyUIWorkflowBuilder()

    # Checkpoint Loader (SD 1.5)
    builder.add_node(
        1,
        "CheckpointLoaderSimple",
        [50, 150],
        [300, 120],
        ["dreamshaper_8.safetensors"],
    )
    # VHS Load Video
    builder.add_node(
        2,
        "VHS_LoadVideo",
        [50, 320],
        [300, 200],
        ["input_driving_video.mp4", 0, 0, 0, True, "image"],
    )
    # Reference Influencer Image (Face)
    builder.add_node(
        3, "LoadImage", [50, 570], [300, 250], ["influencer_face.png", "image"]
    )

    # CLIP prompts
    builder.add_node(
        4,
        "CLIPTextEncode",
        [400, 50],
        [400, 150],
        [
            "a professional video of a beautiful influencer girl, highly detailed face, realistic movement, smooth motion, high quality"
        ],
    )
    builder.add_node(
        5,
        "CLIPTextEncode",
        [400, 220],
        [400, 150],
        ["nsfw, deformed, bad anatomy, blurry, low quality, static, cartoon, painting"],
    )

    # IP-Adapter Unified Loader for FaceID v2 SD 1.5 (loads models)
    builder.add_node(
        6,
        "IPAdapterUnifiedLoader",
        [400, 400],
        [300, 150],
        ["FACEID PLUS V2", 0.6, "CUDA"],
    )

    # ControlNet Loader OpenPose
    builder.add_node(
        7,
        "ControlNetLoader",
        [400, 580],
        [300, 80],
        ["control_v11p_sd15_openpose.safetensors"],
    )
    # Openpose Preprocessor
    builder.add_node(
        8, "OpenposePreprocessor", [400, 680], [300, 150], [512, "yes", "yes", "no"]
    )
    # Apply OpenPose ControlNet
    builder.add_node(
        9, "ControlNetApplyAdvanced", [750, 580], [300, 200], [0.8, 0.0, 1.0]
    )

    # ControlNet Loader TemporalNet / Tile / Lineart
    builder.add_node(
        10,
        "ControlNetLoader",
        [400, 850],
        [300, 80],
        ["control_v11f1e_sd15_tile.safetensors"],
    )
    # Apply Tile/Temporal ControlNet
    builder.add_node(
        11, "ControlNetApplyAdvanced", [750, 850], [300, 200], [0.5, 0.0, 0.8]
    )

    # AnimateDiff Loader (Evolved)
    builder.add_node(
        12,
        "AnimateDiffLoaderWithContext",
        [850, 50],
        [300, 150],
        ["v3_sd15_mm.ckpt", "LCM", "standard_context"],
    )

    # VAE Encode (for Video-to-Video init)
    builder.add_node(13, "VAEEncode", [850, 240], [300, 120])

    # KSampler
    builder.add_node(
        14,
        "KSampler",
        [1200, 250],
        [300, 260],
        [987654321, "randomize", 20, 3.5, "lcm", "sgm_uniform", 0.5],
    )
    # VAE Decode
    builder.add_node(15, "VAEDecode", [1550, 250], [200, 100])

    # Download and Load LivePortrait Models
    builder.add_node(
        16,
        "DownloadAndLoadLivePortraitModels",
        [1200, 580],
        [300, 100],
        ["auto", "human"],
    )
    # LivePortrait Load Cropper (loads facial cropper model)
    builder.add_node(
        21, "LivePortraitLoadCropper", [1200, 710], [300, 100], ["CUDA", True]
    )
    # LivePortrait Cropper (detects and crops face from static influencer image)
    builder.add_node(22, "LivePortraitCropper", [1550, 710], [300, 150], [512, 2.3])

    # LivePortrait Process
    builder.add_node(
        17,
        "LivePortraitProcess",
        [1900, 580],
        [320, 240],
        [True, 0.03, True, 1.0, "constant", "relative", 0.000003, False, 1.0],
    )

    # FILM Frame Interpolation
    builder.add_node(18, "FILM_VFI", [2250, 250], [300, 120], [2])
    # VHS Video Combine
    builder.add_node(
        19,
        "VHS_VideoCombine",
        [2600, 250],
        [300, 280],
        ["influencer_video_output", "video/h264-mp4", 30, True],
    )

    # IP-Adapter Advanced Apply (applies FaceID model to influencer face)
    builder.add_node(
        20,
        "IPAdapterAdvanced",
        [850, 400],
        [300, 200],
        [0.7, "standard", "concat", 0.0, 1.0, "V only"],
    )

    # CONNECTIONS
    # Clip Prompt input
    builder.connect(1, "CLIP", 4, "clip", "CLIP")
    builder.connect(1, "CLIP", 5, "clip", "CLIP")

    # Apply OpenPose ControlNet to prompts
    builder.connect(4, "CONDITIONING", 9, "positive", "CONDITIONING")
    builder.connect(5, "CONDITIONING", 9, "negative", "CONDITIONING")
    builder.connect(7, "CONTROL_NET", 9, "control_net", "CONTROL_NET")
    builder.connect(2, "IMAGE", 8, "image", "IMAGE")
    builder.connect(8, "IMAGE", 9, "image", "IMAGE")

    # Apply Tile/Temporal ControlNet after OpenPose
    builder.connect(9, "positive", 11, "positive", "CONDITIONING")
    builder.connect(9, "negative", 11, "negative", "CONDITIONING")
    builder.connect(10, "CONTROL_NET", 11, "control_net", "CONTROL_NET")
    builder.connect(2, "IMAGE", 11, "image", "IMAGE")

    # AnimateDiff Loader
    builder.connect(1, "MODEL", 12, "model", "MODEL")

    # IP-Adapter Loader and Apply
    builder.connect(12, "model", 6, "model", "MODEL")
    builder.connect(6, "model", 20, "model", "MODEL")
    builder.connect(6, "ipadapter", 20, "ipadapter", "IPADAPTER")
    builder.connect(3, "IMAGE", 20, "image", "IMAGE")

    # VAE Encode driving video frames for Latent space
    builder.connect(2, "IMAGE", 13, "pixels", "IMAGE")
    builder.connect(1, "VAE", 13, "vae", "VAE")

    # KSampler inputs
    builder.connect(20, "model", 14, "model", "MODEL")
    builder.connect(11, "positive", 14, "positive", "CONDITIONING")
    builder.connect(11, "negative", 14, "negative", "CONDITIONING")
    builder.connect(13, "LATENT", 14, "latent_image", "LATENT")

    # VAE Decode to generate initial styled frames
    builder.connect(14, "LATENT", 15, "samples", "LATENT")
    builder.connect(1, "VAE", 15, "vae", "VAE")

    # LivePortrait Animation
    # 1. Feed pipeline, cropper and source image to cropper to get crop_info
    builder.connect(16, "pipeline", 22, "pipeline", "LIVEPORTRAITPIPE")
    builder.connect(21, "cropper", 22, "cropper", "LPCROPPER")
    builder.connect(3, "IMAGE", 22, "source_image", "IMAGE")

    # 2. Feed crop_info and cropped_image to process node, along with driving frames (Node 15)
    builder.connect(16, "pipeline", 17, "pipeline", "LIVEPORTRAITPIPE")
    builder.connect(22, "crop_info", 17, "crop_info", "CROPINFO")
    builder.connect(22, "cropped_image", 17, "source_image", "IMAGE")
    builder.connect(15, "IMAGE", 17, "driving_images", "IMAGE")

    # Frame Interpolation (FILM)
    builder.connect(17, "IMAGE", 18, "images", "IMAGE")

    # Video Combine (MP4)
    builder.connect(18, "IMAGE", 19, "images", "IMAGE")
    builder.connect(2, "audio", 19, "audio", "AUDIO")

    return builder.build()


def main():
    target_dir = "/Users/rus/ai-tools/vault/comfyui"
    os.makedirs(target_dir, exist_ok=True)

    photo_wf = create_photo_workflow()
    photo_path = os.path.join(target_dir, "influencer-photo-workflow.json")
    with open(photo_path, "w", encoding="utf-8") as f:
        json.dump(photo_wf, f, indent=2, ensure_ascii=False)
    print(f"Created Photo Workflow: {photo_path}")

    video_wf = create_video_workflow()
    video_path = os.path.join(target_dir, "influencer-video-workflow.json")
    with open(video_path, "w", encoding="utf-8") as f:
        json.dump(video_wf, f, indent=2, ensure_ascii=False)
    print(f"Created Video Workflow: {video_path}")


if __name__ == "__main__":
    main()
