#!/usr/bin/env python3
"""Strip a JPEG's metadata losslessly, keeping only its orientation (run on every new original).

Drops every APPn and comment segment (EXIF with GPS and device, XMP, ICC, maker
notes), then writes back a minimal EXIF block holding the orientation tag, so
the photo isn't shown on its side. The image data is copied byte for byte.
Run: python3 scripts/strip.py assets/new-photo.jpg [...]
"""
import struct
import sys

from PIL import Image


def strip(data: bytes, orientation: int) -> bytes:
    assert data[:2] == b"\xff\xd8", "not a JPEG"
    out, i = bytearray(), 2
    while True:
        assert data[i] == 0xFF, "malformed JPEG"
        marker = data[i + 1]
        if marker == 0xDA:  # start of scan: the rest is image data
            out += data[i:]
            break
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if not (0xE0 <= marker <= 0xEF or marker == 0xFE):  # keep tables and frame headers
            out += data[i:i + 2 + length]
        i += 2 + length
    exif = Image.Exif()
    exif[0x0112] = orientation
    body = exif.tobytes()
    app1 = body if body.startswith(b"Exif\x00\x00") else b"Exif\x00\x00" + body
    return b"\xff\xd8\xff\xe1" + struct.pack(">H", len(app1) + 2) + app1 + bytes(out)


def main() -> None:
    for path in sys.argv[1:]:
        orientation = Image.open(path).getexif().get(0x0112, 1)
        with open(path, "rb") as f:
            data = f.read()
        clean = strip(data, orientation)
        with open(path, "wb") as f:
            f.write(clean)
        assert dict(Image.open(path).getexif()) == {0x0112: orientation}
        print(f"{path}: {len(data):,} -> {len(clean):,} B, orientation {orientation}")


if __name__ == "__main__":
    main()
