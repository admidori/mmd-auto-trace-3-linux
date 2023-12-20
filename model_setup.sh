# /bin/bash

mkdir -p data/alphapose/detector/yolo/data
mkdir -p data/alphapose/detector/yolox
mkdir -p data/alphapose/pretrained_models
mkdir -p data/alphapose/trackers/weights
mkdir -p data/alphapose/detector/tracker/data


wget -O "yolov3-spp.weights" "https://drive.google.com/u/0/uc?id=1D47msNOOiJKvPOXlnpyzdKA3k6E97NTC&export=download&confirm=t&uuid=64af6dea-7e57-4829-aa9d-ec60c3887481"
mv yolov3-spp.weights data/alphapose/detector/yolo/data/

wget -O "yolox_l.pth" "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_l.pth"
mv yolox_l.pth data/alphapose/detector/yolox/

wget -O "yolox_x.pth" "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_x.pth"
mv yolox_x.pth data/alphapose/detector/yolox/

wget -O "simple_res50_256x192.pth" "https://drive.google.com/u/0/uc?id=1nxyfUbvWDaaT9eDM7Y31ScSVPlGy6gfw&export=download&confirm=t&uuid=9b93e5a7-c23d-45a0-b445-abd796fa8fb9"
mv simple_res50_256x192.pth data/alphapose/pretrained_models/

wget -O "hrnet_w32_256x192.pth" "https://drive.google.com/u/0/uc?id=1i63BPlOnp2vSjIZ7ni4Yp3RCPQwqe922&export=download&confirm=t&uuid=6f5709d6-449f-4eee-b09b-0923a109fff5"
mv hrnet_w32_256x192.pth data/alphapose/pretrained_models/

wget -O "fast_res50_256x192.pth" "https://drive.google.com/u/0/uc?id=1kQhnMRURFiy7NsdS8EFL-8vtqEXOgECn&export=download&confirm=t&uuid=7ebbd705-fb85-41a1-8583-bea9b95087fc"
mv fast_res50_256x192.pth data/alphapose/pretrained_models

wget -O "osnet_ain_x1_0_msmt17_256x128_amsgrad_ep50_lr0.0015_coslr_b64_fb10_softmax_labsmth_flip_jitter.pth " "https://drive.google.com/uc?export=download&id=1SigwBE6mPdqiJMqhuIY4aqC7--5CsMal"
mv osnet_ain_x1_0_msmt17_256x128_amsgrad_ep50_lr0.0015_coslr_b64_fb10_softmax_labsmth_flip_jitter.pth data/alphapose/tracker/

wget -O "jde.1088x608.uncertainty.pt" "https://drive.google.com/u/0/uc?id=1nlnuYfGNuHWZztQHXwVZSL_FvfE551pA&export=download&confirm=t&uuid=e4343bb6-2297-4aa1-8171-acf53e2855bd"
mv jde.1088x608.uncertainty.pt data/alphapose/detector/tracker/data/

wget -O "halpe136_fast50_256x192.pth" "https://drive.google.com/u/0/uc?id=1LbKM2TOxKdpIZoDxCo6ldmOf62pw6z8A&export=download&confirm=t&uuid=907123f1-3257-4e55-9039-cc74e18fcbb9"
mv halpe136_fast50_256x192.pth data/alphapose/pretrained_models/

wget -O "halpe136_fast50_regression_256x192.pth" "https://drive.google.com/u/0/uc?id=1_10JYI3O-VbrAiONfL36UxLf9UXMoUYA&export=download&confirm=t&uuid=ba8e0e7e-c5ec-4284-856d-6ef0de5e2a75"
mv halpe136_fast50_regression_256x192.pth data/alphapose/pretrained_models/

wget -O "multi_domain_fast50_regression_256x192.pth" "https://drive.google.com/u/0/uc?id=1Bb3kPoFFt-M0Y3ceqNO8DTXi1iNDd4gI&export=download&confirm=t&uuid=c18d9fc6-5f99-4331-b518-649a0a8f1756"
mv multi_domain_fast50_regression_256x192.pth data/alphapose/pretrained_models/

wget -O "pretrained_w_cam.pth" "https://drive.google.com/u/0/uc?id=16Y_MGUynFeEzV8GVtKTE5AtkHSi3xsF9&export=download&confirm=t&uuid=0c92b045-e680-4932-ab0b-5cfdae534983"
mv pretrained_w_cam.pth data/alphapose/checkpoint/

wget -O "basicModel_neutral_lbs_10_207_0_v1.0.0.pkl" "https://github.com/classner/up/raw/master/models/3D/basicModel_neutral_lbs_10_207_0_v1.0.0.pkl"
mv basicModel_neutral_lbs_10_207_0_v1.0.0.pkl data/alphapose/model_files/
