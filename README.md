# mmd-auto-trace-3-linux
This repository is forked from https://github.com/miu200521358/mmd-auto-trace-3  
And I am NOT program author. The original author is [miu200521358](https://github.com/miu200521358/).
Thank you for creating this tools!

## Enviroment
```
CUDA:
	nvcc: NVIDIA (R) Cuda compiler driver
	Copyright (c) 2005-2020 NVIDIA Corporation
	Built on Thu_Jun_11_22:26:38_PDT_2020
	Cuda compilation tools, release 11.0, V11.0.194
	Build cuda_11.0_bu.TC445_37.28540450_0

CuDNN:
	Executing: mnistCUDNN
	cudnnGetVersion() : 8500 , CUDNN_VERSION from cudnn.h : 8500 (8.5.0)
	Host compiler version : GCC 9.4.0
```

## Setup
```
conda create -n mat3 pip python=3.9
conda activate mat3
pip install torch==1.7.1+cu110 torchvision==0.8.2+cu110 torchaudio==0.7.2 -f https://download.pytorch.org/whl/torch_stable.html
pip install -r requirements.txt
git submodule add https://github.com/admidori/AlphaPose src/AlphaPose 
git submodule add https://github.com/miu200521358/3D-Multi-Person-Pose src/MultiPose
git submodule add https://github.com/miu200521358/PoseTriplet src/PoseTriplet
cd src/Alphapose
python setup.py build install
```

## Downloading model
`bash ./model_setup.sh`
