"""Kiểm tra ghép khối, DCT và mã hóa/giải mã với dữ liệu thực tế."""
from pathlib import Path
import json
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'code'))
from cau1_chia_khoi import read_image, split_blocks
from cau2_dct import dct_blocks
from cau3_luong_tu_hoa import quantize
from jpeg_support import encode, decode, decode_quantized

image = read_image(ROOT / 'code/RaceHorses_416x240_frame001.png')
checks = []
for name, source in [('anh_day_du', image), ('anh_cat_13x19', image[:13, :19])]:
    blocks, original, padded = split_blocks(source)
    rebuilt = blocks.reshape(padded[0]//8, padded[1]//8, 8, 8).transpose(0, 2, 1, 3).reshape(padded)
    expected = np.pad(source, ((0, padded[0]-original[0]), (0, padded[1]-original[1])), mode='edge')
    assert np.array_equal(rebuilt, expected), 'Sai thứ tự khối hoặc giá trị đệm'
    coeff = dct_blocks(blocks)
    restored_blocks = np.array([cv2.idct(c) + 128 for c in coeff])
    max_error = float(np.max(np.abs(restored_blocks - blocks)))
    assert max_error < 0.001
    for scale in [0.5, 1.0, 3.0]:
        quantized, Q = quantize(coeff, scale)
        bits, codes = encode(quantized)
        assert np.array_equal(quantized, decode_quantized(bits, codes, padded))
        restored = decode(bits, codes, Q, original, padded)
        assert restored.shape == source.shape and restored.dtype == np.uint8
        saved = read_image(ROOT / f'code/ket_qua/cau3/{name}_scale_{scale:.1f}.png')
        assert np.array_equal(restored, saved)
        checks.append({'image': name, 'scale': scale, 'original_shape': original,
                       'padded_shape': padded, 'block_order_and_padding': True,
                       'lossless_quantized_roundtrip': True, 'output_shape_and_dtype': True,
                       'saved_image_matches': True, 'dct_idct_max_abs_error': max_error,
                       'MSE': float(np.mean((source.astype(np.float32)-restored.astype(np.float32))**2)),
                       'bits': len(bits), 'zero_ratio': float(np.mean(quantized == 0))})
out = ROOT / 'bao_cao'
out.mkdir(exist_ok=True)
(out / 'kiem_tra.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'PASS: {len(checks)} cases; block order, padding, DCT/IDCT, Huffman roundtrip, output images.')
