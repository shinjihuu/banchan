"""반찬 사진 누끼 따기 → images/<이름>.png (투명 배경, 작게 줄여서 저장)

사용법:
    pip install "rembg[cpu]" pillow
    python tools/cutout.py 원본사진.jpg kimchi
    python tools/cutout.py 장조림.jpg jangjorim
    python tools/cutout.py 제육.jpg jeyuk
"""
import sys
from pathlib import Path

from PIL import Image
from rembg import new_session, remove

SIZE = 256  # 앱에서는 64px 정도로 보이므로 256px이면 충분 (레티나 대응)


def cutout(src: Path, name: str) -> Path:
    img = Image.open(src).convert("RGB")
    out = remove(img, session=new_session("isnet-general-use"), post_process_mask=True)
    bbox = out.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox()
    if bbox:
        out = out.crop(bbox)
    # 정사각형 캔버스 가운데에 배치
    side = max(out.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(out, ((side - out.width) // 2, (side - out.height) // 2))
    canvas = canvas.resize((SIZE, SIZE), Image.LANCZOS)
    dest = Path(__file__).resolve().parent.parent / "images" / f"{name}.png"
    dest.parent.mkdir(exist_ok=True)
    canvas.save(dest, optimize=True)
    return dest


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print("저장:", cutout(Path(sys.argv[1]), sys.argv[2]))
