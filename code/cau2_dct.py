"""Câu 2: dịch mức -128 và biến đổi DCT cho từng khối 8 x 8."""
import cv2
import matplotlib.pyplot as plt
import numpy as np

from cau1_chia_khoi import arguments, read_image, split_blocks


def dct_blocks(blocks):
    """Trả về hệ số float32 (N, 8, 8); mỗi khối được trừ 128 trước DCT."""
    blocks = np.asarray(blocks)
    if blocks.ndim != 3 or blocks.shape[1:] != (8, 8) or len(blocks) == 0:
        raise ValueError("blocks phải có kích thước (N, 8, 8), N > 0.")
    coefficients = np.empty(blocks.shape, dtype=np.float32)
    for index, block in enumerate(blocks):
        coefficients[index] = cv2.dct(block.astype(np.float32) - 128.0)
    return coefficients


def main():
    args = arguments(__doc__, "cau2")
    image = read_image(args.image)
    blocks, _, _ = split_blocks(image)
    coefficients = dct_blocks(blocks)
    sample = coefficients[0]
    np.set_printoptions(precision=2, suppress=True)
    print("Khối mẫu (khối 0):\n", blocks[0])
    print("Ma trận DCT của khối mẫu:\n", sample)
    print(f"Hệ số DC tại (0, 0): {sample[0, 0]:.4f}")
    print("DC = 8 × (trung bình khối - 128), biểu diễn mức sáng trung bình sau dịch mức.")
    print("63 hệ số AC còn lại biểu diễn biến thiên độ sáng theo các tần số ngang/dọc.")
    np.savetxt(args.output / "dct_khoi_mau.txt", sample, fmt="%.4f")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].imshow(blocks[0], cmap="gray", vmin=0, vmax=255)
    axes[0].set_title("Khối ảnh mẫu 8 × 8")
    plot = axes[1].imshow(np.log1p(np.abs(sample)), cmap="magma")
    axes[1].set_title("log(1 + |DCT|) của khối mẫu")
    axes[1].set_xlabel("Tần số ngang v →")
    axes[1].set_ylabel("Tần số dọc u →")
    fig.colorbar(plot, ax=axes[1], label="log(1 + |DCT|)")
    fig.tight_layout()
    fig.savefig(args.output / "dct.png", dpi=180)
    print("Nhận xét: ảnh tự nhiên thường tập trung hệ số lớn ở vùng tần số thấp (góc trên trái).")
    print("Các hệ số tần số cao biểu diễn chi tiết, biên và nhiễu; phân bố phụ thuộc khối được chọn.")
    if not args.no_show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
