import os
import re
import torch
import numpy as np
import hashlib
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo
import folder_paths
from pathlib import Path
import json

from ..utils import log
class LoadImageSequence:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING",{"default":"videos/####.png"}),
                "current_frame": ("INT",{"default":0, "min":0, "max": 9999999},),
            }
        }

    CATEGORY = "video"
    FUNCTION = "load_image"
    RETURN_TYPES = ("IMAGE", "MASK", "INT",)
    RETURN_NAMES = ("image", "mask", "current_frame",)

    def load_image(self, path=None, current_frame=0):
        log.debug(f"Loading image: {path}, {current_frame}")
        print(f"Loading image: {path}, {current_frame}")
        resolved_path = resolve_path(path, current_frame)
        image_path = folder_paths.get_annotated_filepath(resolved_path)
        i = Image.open(image_path)
        i = ImageOps.exif_transpose(i)
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        if 'A' in i.getbands():
            mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        else:
            mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
        return (image, mask, current_frame,)

    @staticmethod
    def IS_CHANGED(path="", current_frame=0):
        print(f"Checking if changed: {path}, {current_frame}")
        resolved_path = resolve_path(path, current_frame)
        image_path = folder_paths.get_annotated_filepath(resolved_path)
        if os.path.exists(image_path): 
            m = hashlib.sha256()
            with open(image_path, 'rb') as f:
                m.update(f.read())
            return m.digest().hex()
        return "NONE"

    # @staticmethod
    # def VALIDATE_INPUTS(path="", current_frame=0):
        
    #     print(f"Validating inputs: {path}, {current_frame}")
    #     resolved_path = resolve_path(path, current_frame)
    #     if not folder_paths.exists_annotated_filepath(resolved_path):
    #         return f"Invalid image file: {resolved_path}"
    #     return True

def resolve_path(path, frame):
    hashes = path.count("#")
    padded_number = str(frame).zfill(hashes)
    return re.sub("#+", padded_number, path)

class SaveImageSequence:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
                    "images": ("IMAGE", ),
                    "filename_prefix": ("STRING", {"default": "Sequence"}),
                    "current_frame": ("INT", {"default": 0, "min": 0, "max": 9999999}),
                    },
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }

    RETURN_TYPES = ()
    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "image"

    def save_images(self, images, filename_prefix="Sequence", current_frame=0, prompt=None, extra_pnginfo=None):
        # full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        # results = list()
        # for image in images:
        #     i = 255. * image.cpu().numpy()
        #     img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        #     metadata = PngInfo()
        #     if prompt is not None:
        #         metadata.add_text("prompt", json.dumps(prompt))
        #     if extra_pnginfo is not None:
        #         for x in extra_pnginfo:
        #             metadata.add_text(x, json.dumps(extra_pnginfo[x]))

        #     file = f"{filename}_{counter:05}_.png"
        #     img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=4)
        #     results.append({
        #         "filename": file,
        #         "subfolder": subfolder,
        #         "type": self.type
        #     })
        #     counter += 1
    
        if len(images) > 1:
            raise ValueError("Can only save one image at a time")
        
        resolved_path = Path(self.output_dir) / filename_prefix
        resolved_path.mkdir(parents=True, exist_ok=True)
        
        resolved_img = resolved_path / f"{filename_prefix}_{current_frame:05}.png"
        
        output_image = images[0].cpu().numpy()
        img = Image.fromarray(np.clip(output_image * 255., 0, 255).astype(np.uint8))
        metadata = PngInfo()
        if prompt is not None:
            metadata.add_text("prompt", json.dumps(prompt))
        if extra_pnginfo is not None:
            for x in extra_pnginfo:
                metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                
        img.save(resolved_img, pnginfo=metadata, compress_level=4)
        return { "ui": { "images": [ { "filename": resolved_img.name, "subfolder": resolved_path.name, "type": self.type } ] } }
                
                
        