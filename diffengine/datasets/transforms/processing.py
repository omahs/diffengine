import inspect
import random
import re
from enum import EnumMeta
from typing import Dict, List, Optional, Sequence, Tuple, Union

import torchvision
from torchvision.transforms.functional import crop
from torchvision.transforms.transforms import InterpolationMode

from diffengine.datasets.transforms.base import BaseTransform
from diffengine.registry import TRANSFORMS


def _str_to_torch_dtype(t: str):
    """mapping str format dtype to torch.dtype."""
    import torch  # noqa: F401,F403
    return eval(f'torch.{t}')


def _interpolation_modes_from_str(t: str):
    """mapping str format to Interpolation."""
    t = t.lower()
    inverse_modes_mapping = {
        'nearest': InterpolationMode.NEAREST,
        'bilinear': InterpolationMode.BILINEAR,
        'bicubic': InterpolationMode.BICUBIC,
        'box': InterpolationMode.BOX,
        'hammimg': InterpolationMode.HAMMING,
        'lanczos': InterpolationMode.LANCZOS,
    }
    return inverse_modes_mapping[t]


class TorchVisonTransformWrapper:
    """TorchVisonTransformWrapper.

    We can use torchvision.transforms like `dict(type='torchvision/Resize',
    size=512)`

    Args:
        transform (str): The name of transform. For example
            `torchvision/Resize`.
        keys (List[str]): `keys` to apply augmentation from results.
    """

    def __init__(self, transform, *args, keys: List[str] = ['img'], **kwargs):
        self.keys = keys
        if 'interpolation' in kwargs and isinstance(kwargs['interpolation'],
                                                    str):
            kwargs['interpolation'] = _interpolation_modes_from_str(
                kwargs['interpolation'])
        if 'dtype' in kwargs and isinstance(kwargs['dtype'], str):
            kwargs['dtype'] = _str_to_torch_dtype(kwargs['dtype'])
        self.t = transform(*args, **kwargs)

    def __call__(self, results):
        for k in self.keys:
            results[k] = self.t(results[k])
        return results

    def __repr__(self) -> str:
        return f'TorchVision{repr(self.t)}'


def register_vision_transforms() -> List[str]:
    """Register transforms in ``torchvision.transforms`` to the ``TRANSFORMS``
    registry.

    Returns:
        List[str]: A list of registered transforms' name.
    """
    vision_transforms = []
    for module_name in dir(torchvision.transforms):
        if not re.match('[A-Z]', module_name):
            # must startswith a capital letter
            continue
        _transform = getattr(torchvision.transforms, module_name)
        if inspect.isclass(_transform) and callable(
                _transform) and not isinstance(_transform, (EnumMeta)):
            from functools import partial
            TRANSFORMS.register_module(
                module=partial(
                    TorchVisonTransformWrapper, transform=_transform),
                name=f'torchvision/{module_name}')
            vision_transforms.append(f'torchvision/{module_name}')
    return vision_transforms


# register all the transforms in torchvision by using a transform wrapper
VISION_TRANSFORMS = register_vision_transforms()


@TRANSFORMS.register_module()
class SaveImageShape(BaseTransform):
    """Save image shape as 'ori_img_shape' in results."""

    def transform(self,
                  results: Dict) -> Optional[Union[Dict, Tuple[List, List]]]:
        """
        Args:
            results (dict): The result dict.

        Returns:
            dict: 'ori_img_shape' key is added as original image shape.
        """
        results['ori_img_shape'] = [
            results['img'].height, results['img'].width
        ]
        return results


@TRANSFORMS.register_module()
class RandomCrop(BaseTransform):
    """RandomCrop.

    The difference from torchvision/RandomCrop is
        1. save crop top left as 'crop_top_left' and `crop_bottom_right` in
        results
        2. apply same random parameters to multiple `keys` like ['img',
        'condition_img'].

    Args:
        size (sequence or int): Desired output size of the crop. If size is an
            int instead of sequence like (h, w), a square crop (size, size) is
            made. If provided a sequence of length 1, it will be interpreted
            as (size[0], size[0])
        keys (List[str]): `keys` to apply augmentation from results.
    """

    def __init__(self,
                 *args,
                 size: Union[Sequence[int], int],
                 keys: List[str] = ['img'],
                 **kwargs):
        self.size = size
        self.keys = keys
        self.pipeline = torchvision.transforms.RandomCrop(
            *args, size, **kwargs)

    def transform(self,
                  results: Dict) -> Optional[Union[Dict, Tuple[List, List]]]:
        """
        Args:
            results (dict): The result dict.

        Returns:
            dict: 'crop_top_left' and  `crop_bottom_right` key is added as crop
                point.
        """
        assert all(results['img'].size == results[k].size for k in self.keys)
        y1, x1, h, w = self.pipeline.get_params(results['img'],
                                                (self.size, self.size))
        for k in self.keys:
            results[k] = crop(results[k], y1, x1, h, w)
        results['crop_top_left'] = [y1, x1]
        results['crop_bottom_right'] = [y1 + h, x1 + w]
        return results


@TRANSFORMS.register_module()
class CenterCrop(BaseTransform):
    """CenterCrop.

    The difference from torchvision/CenterCrop is
        1. save crop top left as 'crop_top_left' and `crop_bottom_right` in
        results

    Args:
        size (sequence or int): Desired output size of the crop. If size is an
            int instead of sequence like (h, w), a square crop (size, size) is
            made. If provided a sequence of length 1, it will be interpreted
            as (size[0], size[0])
        keys (List[str]): `keys` to apply augmentation from results.
    """

    def __init__(self,
                 *args,
                 size: Union[Sequence[int], int],
                 keys: List[str] = ['img'],
                 **kwargs):
        self.size = size
        self.keys = keys
        self.pipeline = torchvision.transforms.CenterCrop(
            *args, size, **kwargs)

    def transform(self,
                  results: Dict) -> Optional[Union[Dict, Tuple[List, List]]]:
        """
        Args:
            results (dict): The result dict.

        Returns:
            dict: 'crop_top_left' key is added as crop points.
        """
        assert all(results['img'].size == results[k].size for k in self.keys)
        y1 = max(0, int(round((results['img'].height - self.size) / 2.0)))
        x1 = max(0, int(round((results['img'].width - self.size) / 2.0)))
        y2 = max(0, int(round((results['img'].height + self.size) / 2.0)))
        x2 = max(0, int(round((results['img'].width + self.size) / 2.0)))
        for k in self.keys:
            results[k] = self.pipeline(results[k])
        results['crop_top_left'] = [y1, x1]
        results['crop_bottom_right'] = [y2, x2]
        return results


@TRANSFORMS.register_module()
class RandomHorizontalFlip(BaseTransform):
    """RandomHorizontalFlip.

    The difference from torchvision/RandomHorizontalFlip is
        1. update 'crop_top_left' and `crop_bottom_right` if exists.
        2. apply same random parameters to multiple `keys` like ['img',
        'condition_img'].

    Args:
        p (float): probability of the image being flipped.
            Default value is 0.5.
        keys (List[str]): `keys` to apply augmentation from results.
    """

    def __init__(self, *args, p: float = 0.5, keys=['img'], **kwargs):
        self.p = p
        self.keys = keys
        self.pipeline = torchvision.transforms.RandomHorizontalFlip(
            *args, p=1.0, **kwargs)

    def transform(self,
                  results: Dict) -> Optional[Union[Dict, Tuple[List, List]]]:
        """
        Args:
            results (dict): The result dict.

        Returns:
            dict: 'crop_top_left' key is fixed.
        """
        if random.random() < self.p:
            assert all(results['img'].size == results[k].size
                       for k in self.keys)
            for k in self.keys:
                results[k] = self.pipeline(results[k])
            if 'crop_top_left' in results:
                y1 = results['crop_top_left'][0]
                x1 = results['img'].width - results['crop_bottom_right'][1]
                results['crop_top_left'] = [y1, x1]
        return results


@TRANSFORMS.register_module()
class ComputeTimeIds(BaseTransform):
    """Compute time ids as 'time_ids' in results."""

    def transform(self,
                  results: Dict) -> Optional[Union[Dict, Tuple[List, List]]]:
        """
        Args:
            results (dict): The result dict.

        Returns:
            dict: 'time_ids' key is added as original image shape.
        """
        assert 'ori_img_shape' in results
        assert 'crop_top_left' in results
        target_size = [results['img'].height, results['img'].width]
        time_ids = results['ori_img_shape'] + results[
            'crop_top_left'] + target_size
        results['time_ids'] = time_ids
        return results
