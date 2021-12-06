import os

model_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "pretrained_models_data"
)
pretrained_path = os.path.join(model_dir, "model.ckpt-667589")
smpl_model_path = os.path.join(model_dir, "neutral_smpl_with_cocoplus_reg.pkl")
smpl_faces_path = os.path.join(model_dir, "smpl_faces.npy")

model_type = "resnet_fc3_dropout"
data_format = "NHWC"
joint_type = "cocoplus"
batch_size = 1
img_size = 224
num_stage = 3

keypoints_spec = [
    {"name": "jaw", "parent": "neck", "smpl_indx": 15, "hradius": 0.10},
    {"name": "neck", "parent": "upper chest", "smpl_indx": 12, "hradius": 0.10},
    {"name": "upper chest", "parent": "lower chest", "smpl_indx": 9, "hradius": 0.17},
    {"name": "lower chest", "parent": "abdomen", "smpl_indx": 6, "hradius": 0.18},
    {"name": "abdomen", "parent": "pelvis", "smpl_indx": 3, "hradius": 0.20},
    {"name": "pelvis", "parent": "", "smpl_indx": 0, "hradius": 0.15},
    {
        "name": "left upper chest",
        "parent": "upper chest",
        "smpl_indx": 13,
        "hradius": 0.12,
    },
    {
        "name": "left shoulder",
        "parent": "left upper chest",
        "smpl_indx": 16,
        "hradius": 0.10,
    },
    {"name": "left elbow", "parent": "left shoulder", "smpl_indx": 18, "hradius": 0.10},
    {"name": "left wrist", "parent": "left elbow", "smpl_indx": 20, "hradius": 0.08},
    {"name": "left palm", "parent": "left wrist", "smpl_indx": 22, "hradius": 0.10},
    {"name": "left hip", "parent": "pelvis", "smpl_indx": 1, "hradius": 0.14},
    {"name": "left knee", "parent": "left hip", "smpl_indx": 4, "hradius": 0.12},
    {"name": "left ankle", "parent": "left knee", "smpl_indx": 7, "hradius": 0.10},
    {"name": "left toe", "parent": "left ankle", "smpl_indx": 10, "hradius": 0.10},
    {
        "name": "right upper chest",
        "parent": "upper chest",
        "smpl_indx": 14,
        "hradius": 0.12,
    },
    {
        "name": "right shoulder",
        "parent": "right upper chest",
        "smpl_indx": 17,
        "hradius": 0.10,
    },
    {
        "name": "right elbow",
        "parent": "right shoulder",
        "smpl_indx": 19,
        "hradius": 0.10,
    },
    {"name": "right wrist", "parent": "right elbow", "smpl_indx": 21, "hradius": 0.08},
    {"name": "right palm", "parent": "right wrist", "smpl_indx": 23, "hradius": 0.10},
    {"name": "right hip", "parent": "pelvis", "smpl_indx": 2, "hradius": 0.14},
    {"name": "right knee", "parent": "right hip", "smpl_indx": 5, "hradius": 0.12},
    {"name": "right ankle", "parent": "right knee", "smpl_indx": 8, "hradius": 0.10},
    {"name": "right toe", "parent": "right ankle", "smpl_indx": 11, "hradius": 0.10},
]
