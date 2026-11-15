"""Câu 3: lượng tử hóa và thử nén, giải mã ở ba mức 0.5, 1.0, 3.0."""
import csv

import cv2
import matplotlib.pyplot as plt
import numpy as np

from cau1_chia_khoi import arguments, read_image, split_blocks
from cau2_dct import dct_blocks
from jpeg_support import encode, decode


def quantize(coefficients, quant_scale):
    """Tạo Q theo đề, trả về hệ số nguyên và bảng Q float32."""
    if not np.isscalar(quant_scale) or not np.isfinite(quant_scale) or quant_scale <= 0:
        raise ValueError("quant_scale phải là số hữu hạn > 0.")
    coefficients = np.asarray(coefficients)
    if coefficients.ndim != 3 or coefficients.shape[1:] != (8, 8) or len(coefficients) == 0:
        raise ValueError("coefficients phải có kích thước (N, 8, 8), N > 0.")
    u, v = np.indices((8, 8))
    Q0 = 8 + 4 * (u + v)
    Q = np.maximum(1, np.rint(Q0 * quant_scale)).astype(np.float32)
    quantized = np.rint(coefficients / Q).astype(np.int32)
    return quantized, Q


def save_image(path, image):
    success, data = cv2.imencode(".png", image)
    if not success:
        raise RuntimeError(f"Không mã hóa được ảnh: {path}")
    data.tofile(path)


def run_experiment(image, output, prefix):
    blocks, original_shape, padded_shape = split_blocks(image)
    coefficients = dct_blocks(blocks)
    print(f"\n{prefix}: ảnh gốc {original_shape}, sau đệm {padded_shape}, {len(blocks)} khối")
    print("Scale | MSE | Số bit dữ liệu | Tỉ lệ hệ số 0")
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    axes[0].imshow(image, cmap="gray", vmin=0, vmax=255)
    axes[0].set_title("Ảnh gốc")
    save_image(output / f"{prefix}_goc.png", image)
    rows = []
    for i, scale in enumerate([0.5, 1.0, 3.0], start=1):
        quantized, Q = quantize(coefficients, scale)
        bits, codes = encode(quantized)
        restored = decode(bits, codes, Q, original_shape, padded_shape)
        assert restored.shape == image.shape
        assert restored.dtype == np.uint8
        error = image.astype(np.float32) - restored.astype(np.float32)
        mse = float(np.mean(error ** 2))
        zero_ratio = float(np.mean(quantized == 0))
        print(f"{scale:.1f} | {mse:.2f} | {len(bits)} | {zero_ratio:.1%}")
        rows.append([scale, mse, len(bits), zero_ratio])
        if scale == 1.0:
            print("Bảng Q tại scale = 1.0:\n", Q)
            print("Khối mẫu sau lượng tử hóa:\n", quantized[0])
            np.savetxt(output / f"{prefix}_Q.txt", Q, fmt="%.0f")
            np.savetxt(output / f"{prefix}_khoi_luong_tu.txt", quantized[0], fmt="%d")
        save_image(output / f"{prefix}_scale_{scale:.1f}.png", restored)
        axes[i].imshow(restored, cmap="gray", vmin=0, vmax=255)
        axes[i].set_title(f"Scale {scale} — MSE {mse:.2f}")
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(output / f"{prefix}_so_sanh.png", dpi=180)
    with (output / f"{prefix}_ket_qua.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["quant_scale", "MSE", "so_bit_du_lieu", "ti_le_he_so_0"])
        writer.writerows(rows)
    return fig


def main():
    args = arguments(__doc__, "cau3")
    image = read_image(args.image)
    if image.shape[0] < 13 or image.shape[1] < 19:
        raise ValueError("Cần ảnh ít nhất 13 × 19 để kiểm tra ảnh cắt theo đề.")
    figures = [run_experiment(image, args.output, "anh_day_du"),
               run_experiment(image[:13, :19], args.output, "anh_cat_13x19")]
    remarks = (
        "Khi tăng quant_scale, bước lượng tử lớn hơn, các hệ số AC nhỏ thường trở thành 0.\n"
        "Ảnh dựng lại thường mất chi tiết hơn, MSE tăng và số bit dữ liệu giảm; "
        "hãy đối chiếu xu hướng với bảng kết quả thực tế, không coi là quy luật tuyệt đối.\n"
        "Lượng tử hóa là bước chủ yếu làm mất thông tin: phép làm tròn hệ số/Q không đảo ngược được.\n"
        "DCT/IDCT có sai số số học; làm tròn và giới hạn điểm ảnh khi xuất ảnh cũng có thể thêm sai số.\n"
        "Zigzag, RLE và Huffman bảo toàn các hệ số nguyên đã lượng tử hóa.\n"
        "Số bit chỉ tính chuỗi Huffman, chưa gồm bảng mã, Q và metadata; không phải dung lượng JPEG chuẩn.\n"
        "Ảnh giải mã được cắt bỏ phần đệm và kiểm tra có cùng kích thước, kiểu uint8 như ảnh đầu vào.\n"
    )
    print("\n" + remarks)
    (args.output / "nhan_xet.txt").write_text(remarks, encoding="utf-8")
    if not args.no_show:
        plt.show()
    for fig in figures:
        plt.close(fig)


if __name__ == "__main__":
    main()
