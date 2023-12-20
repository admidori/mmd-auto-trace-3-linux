# mmd-auto-trace-3-linux
This repository is forked from https://github.com/miu200521358/mmd-auto-trace-3  
And I am NOT program author. The original author is [miu200521358](https://github.com/miu200521358/).
Thank you for creating this tools!

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

## Download model
bash ./model_setup.sh
