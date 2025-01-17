# Stable Diffusion ControlNet Training

You can also check [`configs/stable_diffusion_controlnet/README.md`](../../../configs/stable_diffusion_controlnet/README.md) file.

## Configs

All configuration files are placed under the [`configs/stable_diffusion_controlnet`](../../../configs/stable_diffusion_controlnet/) folder.

Following is the example config fixed from the stable_diffusion_v15_controlnet_fill50k config file in [`configs/stable_diffusion_controlnet/stable_diffusion_v15_controlnet_fill50k.py`](../../../configs/stable_diffusion_controlnet/stable_diffusion_v15_controlnet_fill50k.py):

```
_base_ = [
    '../_base_/models/stable_diffusion_v15_controlnet.py',
    '../_base_/datasets/fill50k_controlnet.py',
    '../_base_/schedules/stable_diffusion_1e.py',
    '../_base_/default_runtime.py'
]
```

#### Finetuning with Min-SNR Weighting Strategy

The script also allows you to finetune with [Min-SNR Weighting Strategy](https://arxiv.org/abs/2303.09556).

```
_base_ = [
    '../_base_/models/stable_diffusion_v15_controlnet.py',
    '../_base_/datasets/fill50k_controlnet.py',
    '../_base_/schedules/stable_diffusion_1e.py',
    '../_base_/default_runtime.py'
]

model = dict(loss=dict(type='SNRL2Loss', snr_gamma=5.0, loss_weight=1.0))  # setup Min-SNR Weighting Strategy
```

## Run training

Run train

```
# single gpu
$ docker compose exec diffengine mim train diffengine ${CONFIG_FILE}
# Example
$ docker compose exec diffengine mim train diffengine configs/stable_diffusion_controlnet/stable_diffusion_v15_controlnet_fill50k.py

# multi gpus
$ docker compose exec diffengine mim train diffengine ${CONFIG_FILE} --gpus 2 --launcher pytorch
```

## Inference with diffusers

Once you have trained a model, specify the path to the saved model and utilize it for inference using the `diffusers.pipeline` module.

```py
import torch
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from diffusers.utils import load_image

checkpoint = 'work_dirs/stable_diffusion_v15_controlnet_fill50k/step6250'
prompt = 'cyan circle with brown floral background'
condition_image = load_image(
    'https://datasets-server.huggingface.co/assets/fusing/fill50k/--/default/train/74/conditioning_image/image.jpg'
)

controlnet = ControlNetModel.from_pretrained(
        checkpoint, subfolder='controlnet', torch_dtype=torch.float16)
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    'runwayml/stable-diffusion-v1-5', controlnet=controlnet, torch_dtype=torch.float16)
pipe.to('cuda')

image = pipe(
    prompt,
    condition_image,
    num_inference_steps=50,
).images[0]
image.save('demo.png')
```

We also provide inference demo scripts:

```
$ mim run diffengine demo_controlnet ${PROMPT} ${CONDITION_IMAGE} ${CHECKPOINT}
# Example
$ mim run diffengine demo_controlnet "cyan circle with brown floral background" https://datasets-server.huggingface.co/assets/fusing/fill50k/--/default/train/74/conditioning_image/image.jpg work_dirs/stable_diffusion_v15_controlnet_fill50k/step6250
```

## Results Example

#### stable_diffusion_v15_controlnet_fill50k

![input1](https://datasets-server.huggingface.co/assets/fusing/fill50k/--/default/train/74/conditioning_image/image.jpg)

![example1](https://github.com/okotaku/diffengine/assets/24734142/a14cc9a6-3a40-4577-bd5a-2ddbab60970d)

You can check [`configs/stable_diffusion_controlnet/README.md`](../../../configs/stable_diffusion_controlnet/README.md#results-example) for more deitals.
