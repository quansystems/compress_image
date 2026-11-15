"""Câu 1: chia ảnh xám thành các khối 8 x 8, đệm bằng giá trị biên."""
from pathlib import Path
import argparse

import cv2
import matplotlib.pyplot as plt
import numpy as np


def split_blocks(image):
    """Trả về blocks (N, 8, 8), original_shape, padded_shape theo thứ tự hàng."""
    image = np.asarray(image)
    if image.ndim != 2 or image.size == 0:
        raise ValueError("Ảnh phải là ma trận xám hai chiều, không rỗng.")
    height, width = image.shape
    padded = np.pad(image, ((0, (-height) % 8), (0, (-width) % 8)), mode="edge")
    ph, pw = padded.shape
    blocks = padded.reshape(ph // 8, 8, pw // 8, 8).transpose(0, 2, 1, 3)
    return blocks.reshape(-1, 8, 8).copy(), (height, width), (ph, pw)


def read_image(path):
    """Đọc được cả đường dẫn chứa ký tự tiếng Việt trên Windows."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy ảnh: {path}. Hãy truyền đường dẫn ảnh vào lệnh chạy.")
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Không đọc được ảnh: {path}")
    return image


def arguments(description, folder):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("image", nargs="?", type=Path,
                        default=Path(__file__).parent / "RaceHorses_416x240_frame001.png")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "ket_qua" / folder)
    parser.add_argument("--no-show", action="store_true", help="Chỉ lưu hình, không mở cửa sổ.")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    return args


def draw_grid(ax, image, title):
    ax.imshow(image, cmap="gray", vmin=0, vmax=255)
    ax.set_xticks(np.arange(7.5, image.shape[1], 8))
    ax.set_yticks(np.arange(7.5, image.shape[0], 8))
    ax.grid(color="red", linewidth=0.4)
    ax.tick_params(labelbottom=False, labelleft=False, length=0)
    ax.set_title(title)


def main():
    args = arguments(__doc__, "cau1")
    image = read_image(args.image)
    blocks, original_shape, padded_shape = split_blocks(image)
    print(f"Kích thước H × W: {original_shape}; sau đệm: {padded_shape}")
    print(f"Số khối: {len(blocks)}; kích thước blocks: {blocks.shape}")
    print("Khối mẫu (khối 0, góc trên trái):\n", blocks[0])
    np.savetxt(args.output / "khoi_mau.txt", blocks[0], fmt="%d")
    crop = image[:13, :19]
    if crop.shape != (13, 19):
        raise ValueError("Cần ảnh ít nhất 13 × 19 để thực hiện phép thử cắt ảnh trong đề.")
    crop_blocks, crop_shape, crop_padded_shape = split_blocks(crop)
    print(f"Ảnh cắt: {crop_shape}; sau đệm: {crop_padded_shape}; số khối: {len(crop_blocks)}")
    print("Khối cuối ảnh cắt (có đệm biên):\n", crop_blocks[-1])
    padded_crop = np.pad(crop, ((0, 3), (0, 5)), mode="edge")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].imshow(image, cmap="gray", vmin=0, vmax=255)
    axes[0].set_title(f"Ảnh gốc {original_shape[0]} × {original_shape[1]}")
    axes[0].axis("off")
    draw_grid(axes[1], image, "Lưới khối 8 × 8")
    draw_grid(axes[2], padded_crop, "Ảnh cắt 13 × 19, đệm thành 16 × 24")
    fig.tight_layout()
    fig.savefig(args.output / "chia_khoi.png", dpi=180)
    if not args.no_show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
