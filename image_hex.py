#!/usr/bin/env python3
"""
Chuyển ảnh <-> chuỗi hex (không cần cài thư viện nào).

Cách dùng:
    # Ảnh -> hex
    python image_hex.py encode anh.png anh.txt
    python image_hex.py encode anh.png            # in ra màn hình
    python image_hex.py encode anh.png anh.txt --width 64   # xuống dòng mỗi 64 byte

    # Hex -> ảnh
    python image_hex.py decode anh.txt anh_moi.png
    python image_hex.py decode anh.txt            # tự đoán đuôi file (anh.png...)
"""

import argparse
import binascii
import os
import re
import sys

# Chữ ký (magic bytes) để tự đoán định dạng ảnh khi giải mã
SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
    (b"BM", ".bmp"),
    (b"II*\x00", ".tiff"),
    (b"MM\x00*", ".tiff"),
    (b"\x00\x00\x01\x00", ".ico"),
]


def detect_extension(data: bytes) -> str:
    for sig, ext in SIGNATURES:
        if data.startswith(sig):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".bin"


def image_to_hex(path: str, width: int = 0) -> str:
    """Đọc file ảnh và trả về chuỗi hex. width = số byte mỗi dòng (0 = 1 dòng)."""
    with open(path, "rb") as f:
        data = f.read()
    hex_str = binascii.hexlify(data).decode("ascii")
    if width > 0:
        step = width * 2  # 1 byte = 2 ký tự hex
        hex_str = "\n".join(hex_str[i:i + step] for i in range(0, len(hex_str), step))
    return hex_str


def hex_to_bytes(hex_str: str) -> bytes:
    """Làm sạch chuỗi hex (bỏ khoảng trắng, xuống dòng, tiền tố 0x) rồi chuyển thành bytes."""
    hex_str = re.sub(r"0x", "", hex_str, flags=re.IGNORECASE)
    hex_str = re.sub(r"[\s,]", "", hex_str)
    if len(hex_str) % 2:
        raise ValueError("Chuỗi hex có số ký tự lẻ - dữ liệu bị thiếu hoặc hỏng.")
    try:
        return binascii.unhexlify(hex_str)
    except binascii.Error as e:
        raise ValueError(f"Chuỗi hex không hợp lệ: {e}")


def main():
    parser = argparse.ArgumentParser(description="Chuyển ảnh <-> chuỗi hex")
    sub = parser.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encode", help="Ảnh -> hex")
    enc.add_argument("input", help="File ảnh đầu vào")
    enc.add_argument("output", nargs="?", help="File .txt đầu ra (bỏ trống = in ra màn hình)")
    enc.add_argument("--width", type=int, default=0, help="Số byte mỗi dòng (mặc định: 1 dòng)")

    dec = sub.add_parser("decode", help="Hex -> ảnh")
    dec.add_argument("input", help="File .txt chứa chuỗi hex")
    dec.add_argument("output", nargs="?", help="File ảnh đầu ra (bỏ trống = tự đặt tên)")

    args = parser.parse_args()

    try:
        if args.cmd == "encode":
            result = image_to_hex(args.input, args.width)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(result)
                n_bytes = len(re.sub(r"\s", "", result)) // 2
                print(f"Đã ghi hex của {n_bytes} byte vào: {args.output}")
            else:
                print(result)

        else:  # decode
            with open(args.input, "r") as f:
                data = hex_to_bytes(f.read())
            out = args.output
            if not out:
                out = os.path.splitext(args.input)[0] + "_decoded" + detect_extension(data)
            with open(out, "wb") as f:
                f.write(data)
            print(f"Đã khôi phục ảnh ({len(data)} byte) vào: {out}")

    except (OSError, ValueError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
