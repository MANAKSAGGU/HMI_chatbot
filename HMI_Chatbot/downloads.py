import os
import urllib.request
import zipfile

# Helper function to download file
def download_file(url, destination):
    if not os.path.exists(destination):
        print(f"Downloading: {destination}")
        urllib.request.urlretrieve(url, destination)
    else:
        print(f"Already exists: {destination}")

# Create necessary directories
os.makedirs('./checkpoints', exist_ok=True)
os.makedirs('./gfpgan/weights', exist_ok=True)

# URLs and destinations
files_to_download = [
    # SadTalker original links (optional / legacy)
    # ("https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/auido2exp_00300-model.pth", "./checkpoints/auido2exp_00300-model.pth"),
    # ("https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/auido2pose_00140-model.pth", "./checkpoints/auido2pose_00140-model.pth"),
    # ("https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/epoch_20.pth", "./checkpoints/epoch_20.pth"),
    # ("https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/facevid2vid_00189-model.pth.tar", "./checkpoints/facevid2vid_00189-model.pth.tar"),
    # ("https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/shape_predictor_68_face_landmarks.dat", "./checkpoints/shape_predictor_68_face_landmarks.dat"),
    # ("https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/wav2lip.pth", "./checkpoints/wav2lip.pth"),

    # Updated SadTalker model links
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar", "./checkpoints/mapping_00109-model.pth.tar"),
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar", "./checkpoints/mapping_00229-model.pth.tar"),
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors", "./checkpoints/SadTalker_V0.0.2_256.safetensors"),
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors", "./checkpoints/SadTalker_V0.0.2_512.safetensors"),

    # Optional BFM fitting model
    # ("https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/BFM_Fitting.zip", "./checkpoints/BFM_Fitting.zip"),

    # Face enhancement weights
    ("https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth", "./gfpgan/weights/alignment_WFLW_4HG.pth"),
    ("https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth", "./gfpgan/weights/detection_Resnet50_Final.pth"),
    ("https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth", "./gfpgan/weights/GFPGANv1.4.pth"),
    ("https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth", "./gfpgan/weights/parsing_parsenet.pth"),
]

# Start downloading
for url, dest in files_to_download:
    download_file(url, dest)

# Optional: Unzip hub.zip or BFM_Fitting.zip if needed
# hub_zip_path = "./checkpoints/hub.zip"
# if os.path.exists(hub_zip_path):
#     with zipfile.ZipFile(hub_zip_path, 'r') as zip_ref:
#         zip_ref.extractall("./checkpoints")

# BFM zip example
# bfm_zip_path = "./checkpoints/BFM_Fitting.zip"
# if os.path.exists(bfm_zip_path):
#     with zipfile.ZipFile(bfm_zip_path, 'r') as zip_ref:
#         zip_ref.extractall("./checkpoints")

print("All downloads completed.")
