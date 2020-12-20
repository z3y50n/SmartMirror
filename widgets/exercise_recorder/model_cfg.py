import os

model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
pretrained_path = os.path.join(model_dir, 'model.ckpt-667589')
smpl_model_path = os.path.join(model_dir, 'neutral_smpl_with_cocoplus_reg.pkl')
smpl_faces_path = os.path.join(model_dir, 'smpl_faces.npy')

model_type = 'resnet_fc3_dropout'
data_format = 'NHWC'
joint_type = 'cocoplus'
batch_size = 1
img_size = 224
num_stage = 3
