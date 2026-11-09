"""Склейка картинок в один лист для просмотра: python tools/contact.py out.png a.png b.png ..."""
import sys
from PIL import Image
out, names = sys.argv[1], sys.argv[2:]
W = 1000
ims = [Image.open(n).convert("RGB") for n in names]
ims = [i.resize((W, int(i.height * W / i.width))) for i in ims]
H = sum(i.height + 10 for i in ims)
o = Image.new("RGB", (W, H), (200, 200, 200)); y = 0
for i in ims:
    o.paste(i, (0, y)); y += i.height + 10
o.save(out)
