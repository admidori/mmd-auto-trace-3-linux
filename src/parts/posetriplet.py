import argparse
import json
import os
import platform
import random
import shutil
import sys
import time
from glob import glob

sys.path.append(os.path.abspath(os.path.join(__file__, "../../PoseTriplet")))

sys.path.append(os.path.abspath(os.path.join(__file__, "../../PoseTriplet/estimator_inference")))

import numpy as np
import torch
from base.logger import MLogger
from PoseTriplet.estimator_inference.common.camera import \
    normalize_screen_coordinates
from PoseTriplet.estimator_inference.common.generators import \
    UnchunkedGenerator
from PoseTriplet.estimator_inference.common.model import TemporalModel
from PoseTriplet.estimator_inference.common.utils import evaluate
from tqdm import tqdm

from parts.config import DirName, FileName

logger = MLogger(__name__)

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"  # see issue #152

# COCO(17) + hip, spine, neck, head
# https://github.com/CMU-Perceptual-Computing-Lab/openpose/issues/1560
COCO_KEYPOINTS = {
    "Nose": 0,
    "LEye": 1,
    "REye": 2,
    "LEar": 3,
    "REar": 4,
    "LShoulder": 5,
    "RShoulder": 6,
    "LElbow": 7,
    "RElbow": 8,
    "LWrist": 9,
    "RWrist": 10,
    "LHip": 11,
    "RHip": 12,
    "LKnee": 13,
    "RKnee": 14,
    "LAnkle": 15,
    "RAnkle": 16,
    "Hip": 17,  # 計算して追加
    "Spine": 18,  # 計算して追加
    "Neck": 19,  # 計算して追加
    "Head": 20,  # 計算して追加
}

# https://github.com/Fang-Haoshu/Halpe-FullBody#keypoints-format
HALPE_KEYPOINTS = {
    "Nose": 0,
    "LEye": 1,
    "REye": 2,
    "LEar": 3,
    "REar": 4,
    "LShoulder": 5,
    "RShoulder": 6,
    "LElbow": 7,
    "RElbow": 8,
    "LWrist": 9,
    "RWrist": 10,
    "LHip": 11,
    "RHip": 12,
    "LKnee": 13,
    "RKnee": 14,
    "LAnkle": 15,
    "RAnkle": 16,
    "Head": 17,
    "Neck": 18,
    "Hip": 19,
    "LBigToe": 20,
    "RBigToe": 21,
    "LSmallToe": 22,
    "RSmallToe": 23,
    "LHeel": 24,
    "RHeel": 25,
    "Spine": 26,  # 計算して追加
}

# Halpe26 -> COCO
HALPE_2_COCO_ORDER = (
    HALPE_KEYPOINTS["Hip"],
    HALPE_KEYPOINTS["RHip"],
    HALPE_KEYPOINTS["RKnee"],
    HALPE_KEYPOINTS["RAnkle"],
    HALPE_KEYPOINTS["LHip"],
    HALPE_KEYPOINTS["LKnee"],
    HALPE_KEYPOINTS["LAnkle"],
    HALPE_KEYPOINTS["Spine"],
    HALPE_KEYPOINTS["Neck"],
    HALPE_KEYPOINTS["Head"],
    HALPE_KEYPOINTS["LShoulder"],
    HALPE_KEYPOINTS["LElbow"],
    HALPE_KEYPOINTS["LWrist"],
    HALPE_KEYPOINTS["RShoulder"],
    HALPE_KEYPOINTS["RElbow"],
    HALPE_KEYPOINTS["RWrist"],
)

# 左右のキー番号
KEYPOINTS_SYMMETRY = ((4, 5, 6, 10, 11, 12), (1, 2, 3, 13, 14, 15))

# PoseTripletのジョイント名
SIMPLE16_KEYPOINTS = (
    "pelvis",
    "right_hip",
    "right_knee",
    "right_ankle",
    "left_hip",
    "left_knee",
    "left_ankle",
    "spine2",
    "neck",
    "head",
    "left_shoulder",
    "left_elbow",
    "left_wrist",
    "right_shoulder",
    "right_elbow",
    "right_wrist",
)


def execute(args):
    try:
        logger.info(
            "深度推定 開始: {img_dir}",
            img_dir=args.img_dir,
            decoration=MLogger.DECORATION_BOX,
        )

        if not os.path.exists(args.img_dir):
            logger.error(
                "指定された処理用ディレクトリが存在しません。: {img_dir}",
                img_dir=args.img_dir,
                decoration=MLogger.DECORATION_BOX,
            )
            return False

        parser = get_args_parser()
        argv = parser.parse_args(args=[])

        # model 2d detection detail
        argv.detector_2d = "alpha_pose"

        # redering detail
        argv.pure_background = True  # False/True
        argv.add_trajectory = True  # False
        # argv.viz_limit = 200

        ###########################
        # model 2d-3d detail
        ###########################
        # argv.architecture = '3,1,3,1,3'  # model arch
        argv.test_time_augmentation = True  # False
        argv.pose2d_smoothing = True

        argv.frame_rate = 30

        output_dir_path = os.path.join(args.img_dir, DirName.POSETRIPLET.value)
        os.makedirs(output_dir_path, exist_ok=True)

        ckpt_path = "../data/posetriplet/ckpt_ep_045.bin"

        logger.info(
            "学習モデル準備開始",
            decoration=MLogger.DECORATION_LINE,
        )

        model = get_model(argv, ckpt_path)
        model_traj = get_model_traj(argv, ckpt_path)

        for json_path in glob(os.path.join(args.img_dir, DirName.ALPHAPOSE.value, "*.json")):
            if FileName.ALPHAPOSE_RESULT.value in json_path:
                continue

            json_datas = {}
            with open(json_path, "r") as f:
                json_datas = json.load(f)

            if len(json_datas) < 5:
                # 5F以内であればスルー
                continue

            # 人物INDEX
            pname = os.path.basename(json_path).split(".")[0]

            logger.info(
                "【No.{pname}】2D姿勢推定 結果取得",
                pname=pname,
                decoration=MLogger.DECORATION_LINE,
            )

            width = height = 0
            keypoints = {}
            for fno, json_data in tqdm(json_datas.items(), desc=f"No.{pname} ... "):
                fno = int(fno)
                width = int(json_data["image"]["width"])
                height = int(json_data["image"]["height"])
                keypoints[fno] = np.array(json_data["2d-keypoints"]).reshape(-1, 3)[:, :2]

            logger.info(
                "【No.{pname}】深度推定 開始",
                pname=pname,
                decoration=MLogger.DECORATION_LINE,
            )

            norm_keypoints = fetch_keypoint(np.array(list(keypoints.values())), width, height)
            data_loader = get_dataloader(model, norm_keypoints)
            data_loader_traj = get_dataloader(model_traj, norm_keypoints)

            prediction = evaluate(
                data_loader,
                model,
                return_predictions=True,
                joints_leftright=KEYPOINTS_SYMMETRY,
            )

            root_trajectory = evaluate(
                data_loader_traj,
                model_traj,
                return_predictions=True,
                joints_leftright=KEYPOINTS_SYMMETRY,
            )

            # add root trajectory
            prediction -= prediction[:, :1, :]
            prediction += root_trajectory

            logger.info(
                "【No.{pname}】深度推定 結果取得",
                pname=pname,
                decoration=MLogger.DECORATION_LINE,
            )

            personal_data = {}
            for fno, fjoints in tqdm(zip(keypoints.keys(), prediction.tolist()), desc=f"No.{pname} ... "):
                fidx = str(fno)
                personal_data[fno] = {
                    "image": json_datas[fidx]["image"],
                    "2d-keypoints": json_datas[fidx]["2d-keypoints"],
                    "bbox": json_datas[fidx]["bbox"],
                    "posetriplet-keypoints": {},
                }
                for jname, (jx, jy, jz) in zip(SIMPLE16_KEYPOINTS, fjoints):
                    personal_data[fno]["posetriplet-keypoints"][jname] = {
                        "x": float(jx),
                        "y": -float(jy),
                        "z": float(jz),
                    }
                    if jname == "pelvis":
                        personal_data[fno]["posetriplet-keypoints"]["spine"] = {
                            "x": float(jx),
                            "y": -float(jy),
                            "z": float(jz),
                        }
                personal_data[fno]["posetriplet-keypoints"]["pelvis2"] = {
                    "x": float(
                        np.mean(
                            [
                                personal_data[fno]["posetriplet-keypoints"]["left_knee"]["x"],
                                personal_data[fno]["posetriplet-keypoints"]["right_knee"]["x"],
                                personal_data[fno]["posetriplet-keypoints"]["left_hip"]["x"],
                                personal_data[fno]["posetriplet-keypoints"]["right_hip"]["x"],
                            ]
                        )
                    ),
                    "y": float(
                        np.mean(
                            [
                                personal_data[fno]["posetriplet-keypoints"]["left_knee"]["y"],
                                personal_data[fno]["posetriplet-keypoints"]["right_knee"]["y"],
                                personal_data[fno]["posetriplet-keypoints"]["left_hip"]["y"],
                                personal_data[fno]["posetriplet-keypoints"]["right_hip"]["y"],
                            ]
                        )
                    ),
                    "z": float(
                        np.mean(
                            [
                                personal_data[fno]["posetriplet-keypoints"]["left_knee"]["z"],
                                personal_data[fno]["posetriplet-keypoints"]["right_knee"]["z"],
                                personal_data[fno]["posetriplet-keypoints"]["left_hip"]["z"],
                                personal_data[fno]["posetriplet-keypoints"]["right_hip"]["z"],
                            ]
                        )
                    ),
                }

            logger.info(
                "【No.{pname}】深度推定 結果保存",
                pname=pname,
                decoration=MLogger.DECORATION_LINE,
            )

            with open(os.path.join(output_dir_path, os.path.basename(json_path)), "w") as f:
                json.dump(personal_data, f, indent=4)

        logger.info(
            "深度推定 結果保存完了: {output_dir_path}",
            output_dir_path=output_dir_path,
            decoration=MLogger.DECORATION_BOX,
        )

        return True
    except Exception as e:
        logger.critical("深度推定で予期せぬエラーが発生しました。", e, decoration=MLogger.DECORATION_BOX)
        return False


def fetch_keypoint(keypoints: np.ndarray, width: int, height: int):
    # Keypointの並び順を調整する
    spine = 0.5 * (keypoints[:, HALPE_KEYPOINTS["Neck"]] + keypoints[:, HALPE_KEYPOINTS["Hip"]])
    combine = np.transpose([spine], (1, 0, 2))
    combine_kp = np.concatenate([keypoints, combine], axis=1)
    keypoints_imgunnorm = combine_kp[:, HALPE_2_COCO_ORDER].copy()

    # 正方形に合わせる
    if width > height:  # up down padding
        pad = int((width - height) * 0.5)
        keypoints_imgunnorm[:, :, 1] = keypoints_imgunnorm[:, :, 1] + pad
        height = width
    elif width < height:  # left right padding
        pad = int((height - width) * 0.5)
        keypoints_imgunnorm[:, :, 0] = keypoints_imgunnorm[:, :, 0] + pad
        width = height
    else:
        pass

    return normalize_screen_coordinates(keypoints_imgunnorm[..., :2], width, height)


def get_dataloader(model, keypoints: np.ndarray):
    #  Receptive field: 243 frames for args.arc [3, 3, 3, 3, 3]
    receptive_field = model.receptive_field()
    pad = (receptive_field - 1) // 2  # Padding on each side
    causal_shift = 0
    data_loader = UnchunkedGenerator(
        None,
        None,
        [keypoints],
        pad=pad,
        causal_shift=causal_shift,
        augment=False,
        kps_left=KEYPOINTS_SYMMETRY[0],
        kps_right=KEYPOINTS_SYMMETRY[1],
        joints_left=KEYPOINTS_SYMMETRY[0],
        joints_right=KEYPOINTS_SYMMETRY[1],
    )
    return data_loader


def get_model(argv, ckpt_path):
    model = TemporalModel(
        16,
        2,
        16,
        filter_widths=[3, 3, 3],
        causal=argv.causal,
        dropout=argv.dropout,
        channels=argv.channels,
        dense=argv.dense,
    ).cuda()
    checkpoint = torch.load(ckpt_path, map_location=lambda storage, loc: storage)
    model.load_state_dict(checkpoint["model_pos"])
    return model

def get_model_traj(argv, ckpt_path):
    model_traj = TemporalModel(
        16,
        2,
        1,
        filter_widths=[3, 3, 3],
        causal=argv.causal,
        dropout=argv.dropout,
        channels=argv.channels,
        dense=argv.dense,
    ).cuda()

    # load trained model
    checkpoint = torch.load(ckpt_path, map_location=lambda storage, loc: storage)
    model_traj.load_state_dict(checkpoint["model_traj"])
    return model_traj

def get_args_parser():
    parser = argparse.ArgumentParser(description='Training script')

    # General arguments
    parser.add_argument('-d', '--dataset', default='h36m', type=str, metavar='NAME', help='target dataset')  # h36m or humaneva
    parser.add_argument('-k', '--keypoints', default='gt', type=str, metavar='NAME', help='2D detections to use')
    parser.add_argument('-str', '--subjects-train', default='S1,S5,S6,S7,S8', type=str, metavar='LIST',
                        help='training subjects separated by comma')
    parser.add_argument('-ste', '--subjects-test', default='S9,S11', type=str, metavar='LIST', help='test subjects separated by comma')
    parser.add_argument('-sun', '--subjects-unlabeled', default='', type=str, metavar='LIST',
                        help='unlabeled subjects separated by comma for self-supervision')
    parser.add_argument('-a', '--actions', default='*', type=str, metavar='LIST',
                        help='actions to train/test on, separated by comma, or * for all')
    parser.add_argument('-c', '--checkpoint', default='checkpoint', type=str, metavar='PATH',
                        help='checkpoint directory')
    parser.add_argument('--checkpoint-frequency', default=10, type=int, metavar='N',
                        help='create a checkpoint every N epochs')
    parser.add_argument('-r', '--resume', default='', type=str, metavar='FILENAME',
                        help='checkpoint to resume (file name)')
    parser.add_argument('--evaluate', default='pretrained_h36m_detectron_coco.bin', type=str, metavar='FILENAME', help='checkpoint to evaluate (file name)')
    parser.add_argument('--render', action='store_true', help='visualize a particular video')
    parser.add_argument('--by-subject', action='store_true', help='break down error by subject (on evaluation)')
    parser.add_argument('--export-training-curves', action='store_true', help='save training curves as .png images')

    # Model arguments
    parser.add_argument('-s', '--stride', default=1, type=int, metavar='N', help='chunk size to use during training')
    parser.add_argument('-e', '--epochs', default=60, type=int, metavar='N', help='number of training epochs')
    parser.add_argument('-b', '--batch-size', default=1024, type=int, metavar='N', help='batch size in terms of predicted frames')
    parser.add_argument('-drop', '--dropout', default=0.25, type=float, metavar='P', help='dropout probability')
    parser.add_argument('-lr', '--learning-rate', default=0.001, type=float, metavar='LR', help='initial learning rate')
    parser.add_argument('-lrd', '--lr-decay', default=0.95, type=float, metavar='LR', help='learning rate decay per epoch')
    parser.add_argument('-no-da', '--no-data-augmentation', dest='data_augmentation', action='store_false',
                        help='disable train-time flipping')
    parser.add_argument('-no-tta', '--no-test-time-augmentation', dest='test_time_augmentation', action='store_false',
                        help='disable test-time flipping')
    parser.add_argument('-arc', '--architecture', default='3,3,3,3,3', type=str, metavar='LAYERS', help='filter widths separated by comma')
    parser.add_argument('--causal', action='store_true', help='use causal convolutions for real-time processing')
    parser.add_argument('-ch', '--channels', default=1024, type=int, metavar='N', help='number of channels in convolution layers')

    # Experimental
    parser.add_argument('--subset', default=1, type=float, metavar='FRACTION', help='reduce dataset size by fraction')
    parser.add_argument('--downsample', default=1, type=int, metavar='FACTOR', help='downsample frame rate by factor (semi-supervised)')
    parser.add_argument('--warmup', default=1, type=int, metavar='N', help='warm-up epochs for semi-supervision')
    parser.add_argument('--no-eval', action='store_true', help='disable epoch evaluation while training (small speed-up)')
    parser.add_argument('--dense', action='store_true', help='use dense convolutions instead of dilated convolutions')
    parser.add_argument('--disable-optimizations', action='store_true', help='disable optimized model for single-frame predictions')
    parser.add_argument('--linear-projection', action='store_true', help='use only linear coefficients for semi-supervised projection')
    parser.add_argument('--no-bone-length', action='store_false', dest='bone_length_term',
                        help='disable bone length term in semi-supervised settings')
    parser.add_argument('--no-proj', action='store_true', help='disable projection for semi-supervised setting')

    # Visualization
    parser.add_argument('--viz-subject', type=str, metavar='STR', help='subject to render')
    parser.add_argument('--viz-action', type=str, metavar='STR', help='action to render')
    parser.add_argument('--viz-camera', type=int, default=0, metavar='N', help='camera to render')
    parser.add_argument('--viz-video', type=str, metavar='PATH', help='path to input video')
    parser.add_argument('--viz-skip', type=int, default=0, metavar='N', help='skip first N frames of input video')
    parser.add_argument('--viz-output', type=str, metavar='PATH', help='output file name (.gif or .mp4)')
    parser.add_argument('--viz-bitrate', type=int, default=30000, metavar='N', help='bitrate for mp4 videos')
    parser.add_argument('--viz-no-ground-truth', action='store_true', help='do not show ground-truth poses')
    parser.add_argument('--viz-limit', type=int, default=-1, metavar='N', help='only render first N frames')
    parser.add_argument('--viz-downsample', type=int, default=1, metavar='N', help='downsample FPS by a factor N')
    parser.add_argument('--viz-size', type=int, default=5, metavar='N', help='image size')
    # self add
    parser.add_argument('--input-npz', dest='input_npz', type=str, default='', help='input 2d numpy file')
    parser.add_argument('--video', dest='input_video', type=str, default='', help='input video name')

    parser.set_defaults(bone_length_term=True)
    parser.set_defaults(data_augmentation=True)
    parser.set_defaults(test_time_augmentation=True)

    return parser
    