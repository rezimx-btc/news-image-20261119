"""THE WORLD TODAY - a one-page newspaper of 19 November 2026.

Draws a 1024x1024 front page with a hand-rolled PNG encoder and a 5x7
bitmap font. Standard library only, fully deterministic: same input,
same bytes, every run.
"""

import math
import struct
import zlib

W = 1024
H = 1024

CREAM = bytes((250, 244, 226))
INK = bytes((22, 20, 18))
RED = bytes((178, 32, 28))

FONT = {
    "A": [14, 17, 17, 31, 17, 17, 17],
    "B": [30, 17, 17, 30, 17, 17, 30],
    "C": [14, 17, 16, 16, 16, 17, 14],
    "D": [30, 17, 17, 17, 17, 17, 30],
    "E": [31, 16, 16, 30, 16, 16, 31],
    "F": [31, 16, 16, 30, 16, 16, 16],
    "G": [14, 17, 16, 23, 17, 17, 15],
    "H": [17, 17, 17, 31, 17, 17, 17],
    "I": [14, 4, 4, 4, 4, 4, 14],
    "J": [7, 2, 2, 2, 2, 18, 12],
    "K": [17, 18, 20, 24, 20, 18, 17],
    "L": [16, 16, 16, 16, 16, 16, 31],
    "M": [17, 27, 21, 21, 17, 17, 17],
    "N": [17, 25, 21, 19, 17, 17, 17],
    "O": [14, 17, 17, 17, 17, 17, 14],
    "P": [30, 17, 17, 30, 16, 16, 16],
    "Q": [14, 17, 17, 17, 21, 18, 13],
    "R": [30, 17, 17, 30, 20, 18, 17],
    "S": [15, 16, 16, 14, 1, 1, 30],
    "T": [31, 4, 4, 4, 4, 4, 4],
    "U": [17, 17, 17, 17, 17, 17, 14],
    "V": [17, 17, 17, 17, 17, 10, 4],
    "W": [17, 17, 17, 21, 21, 27, 17],
    "X": [17, 17, 10, 4, 10, 17, 17],
    "Y": [17, 17, 10, 4, 4, 4, 4],
    "Z": [31, 1, 2, 4, 8, 16, 31],
    "0": [14, 17, 19, 21, 25, 17, 14],
    "1": [4, 12, 4, 4, 4, 4, 14],
    "2": [14, 17, 1, 6, 8, 16, 31],
    "3": [30, 1, 1, 14, 1, 1, 30],
    "4": [2, 6, 10, 18, 31, 2, 2],
    "5": [31, 16, 30, 1, 1, 17, 14],
    "6": [6, 8, 16, 30, 17, 17, 14],
    "7": [31, 1, 2, 4, 8, 8, 8],
    "8": [14, 17, 17, 14, 17, 17, 14],
    "9": [14, 17, 17, 15, 1, 2, 12],
    " ": [0, 0, 0, 0, 0, 0, 0],
    ".": [0, 0, 0, 0, 0, 12, 12],
    ",": [0, 0, 0, 0, 12, 4, 8],
    "-": [0, 0, 0, 14, 0, 0, 0],
    "'": [4, 4, 8, 0, 0, 0, 0],
    ":": [0, 12, 12, 0, 12, 12, 0],
    ";": [0, 12, 12, 0, 12, 4, 8],
    "!": [4, 4, 4, 4, 4, 0, 4],
    "?": [14, 17, 1, 6, 4, 0, 4],
    "/": [1, 2, 2, 4, 8, 8, 16],
    "(": [2, 4, 8, 8, 8, 4, 2],
    ")": [8, 4, 2, 2, 2, 4, 8],
    "%": [25, 26, 2, 4, 8, 11, 19],
    "+": [0, 4, 4, 14, 4, 4, 0],
}

PIX = bytearray(CREAM * (W * H))


def set_px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PIX[i:i + 3] = color


def fill_rect(x, y, w, h, color):
    x0 = max(x, 0)
    y0 = max(y, 0)
    x1 = min(x + w, W)
    y1 = min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    row = color * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        PIX[i:i + len(row)] = row


def draw_line(x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_px(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_circle(cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(r * r - dy * dy, 0)))
        fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)


def fill_ellipse(cx, cy, rx, ry, color):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * math.sqrt(max(t, 0.0)))
        fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_char(ch, x, y, scale, color):
    glyph = FONT.get(ch.upper(), FONT[" "])
    for row in range(7):
        bits = glyph[row]
        for col in range(5):
            if bits & (1 << (4 - col)):
                fill_rect(x + col * scale, y + row * scale, scale, scale, color)


def draw_text(text, x, y, scale, color, align="left"):
    if align == "center":
        x -= text_width(text, scale) // 2
    elif align == "right":
        x -= text_width(text, scale)
    cx = x
    for ch in text:
        draw_char(ch, cx, y, scale, color)
        cx += 6 * scale


def wrap_lines(text, max_w, scale):
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_palm(x, base_y, color):
    top_x = x - 10
    top_y = base_y - 58
    draw_line(x, base_y, top_x, top_y, color)
    draw_line(top_x, top_y, top_x - 26, top_y - 6, color)
    draw_line(top_x, top_y, top_x - 14, top_y - 18, color)
    draw_line(top_x, top_y, top_x + 2, top_y - 20, color)
    draw_line(top_x, top_y, top_x + 18, top_y - 14, color)
    draw_line(top_x, top_y, top_x + 26, top_y - 2, color)


def draw_skyline():
    fill_circle(905, 368, 30, RED)
    buildings = [
        (60, 50, 372), (115, 40, 352), (160, 60, 385), (225, 45, 360),
        (275, 55, 392), (335, 40, 368), (380, 60, 355), (445, 45, 388),
        (495, 55, 362), (555, 40, 380), (600, 60, 350), (665, 45, 390),
        (715, 55, 365), (775, 40, 382), (820, 55, 358),
    ]
    for bx, bw, top in buildings:
        fill_rect(bx, top, bw, 418 - top, INK)
    draw_palm(70, 418, INK)
    draw_palm(954, 418, INK)
    fill_rect(36, 418, 952, 3, INK)


def draw_map():
    draw_text("THE WORLD IN BRIEF - STORIES MARKED IN RED", 512, 428, 2, INK, "center")
    fill_rect(36, 448, 952, 2, INK)
    fill_rect(36, 566, 952, 2, INK)
    fill_rect(36, 448, 2, 120, INK)
    fill_rect(986, 448, 2, 120, INK)
    fill_ellipse(180, 492, 80, 30, INK)
    fill_ellipse(230, 540, 28, 22, INK)
    fill_ellipse(500, 476, 30, 18, INK)
    fill_ellipse(520, 520, 38, 32, INK)
    fill_ellipse(680, 486, 120, 32, INK)
    fill_ellipse(850, 540, 40, 16, INK)
    fill_circle(165, 484, 5, RED)
    fill_circle(575, 500, 5, RED)
    fill_circle(498, 470, 5, RED)
    fill_circle(640, 500, 5, RED)
    fill_circle(740, 490, 5, RED)
    fill_circle(935, 480, 5, RED)
    draw_text("USA", 140, 526, 2, INK)
    draw_text("GULF", 560, 522, 2, INK)
    draw_text("EUROPE", 398, 470, 2, INK)
    draw_text("INDIA", 615, 522, 2, INK)
    draw_text("CHINA", 715, 522, 2, INK)
    draw_text("VOYAGER 1", 848, 452, 2, INK)


def draw_story(x, y, width, headline, deck):
    for line in wrap_lines(headline, width, 2):
        draw_text(line, x, y, 2, INK)
        y += 20
    y += 2
    for line in wrap_lines(deck, width, 1):
        draw_text(line, x, y, 1, INK)
        y += 11
    return y + 16


def png_chunk(kind, data):
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def save_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += PIX[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", ihdr)
    png += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


COL1 = [
    ("JEFFRIES NOMINATED FIRST BLACK SPEAKER",
     "Democrats pick Hakeem Jeffries for US House Speaker, a first."),
    ("US AND IRAN EXCHANGE FIRE AGAIN",
     "Iran hits a US base in Kuwait and Bahrain; US strikes Qeshm Island."),
    ("TRUMP, XI AND PUTIN TO MEET AT APEC",
     "Trilateral talks scheduled in Shenzhen on the 19th."),
    ("EU PROPOSES EUR 45BN UKRAINE LOAN",
     "To be repaid after Russia pays reparations."),
]

COL2 = [
    ("NVIDIA STOPS H-SERIES CHIPS TO CHINA",
     "Acting CEO Colette Kress after founder Jensen Huang resigned."),
    ("CYCLONE AKVAN NEARS INDIA",
     "Storm likely to cross between Machilipatnam and Puri."),
    ("VOYAGER 1 REACHES ONE LIGHT-DAY",
     "NASA probe hits milestone; confirmation due at 19 Nov briefing."),
    ("FED MINUTES: MORE HIKES LIKELY",
     "Most officials expect further rises to bring inflation to 2%."),
]

COL3 = [
    ("ISLAM SET TO BE WORLD'S LARGEST FAITH BY 2035",
     "Pew Research report."),
    ("CANADA RESETS CHINA TIES",
     "PM Carney aims to clinch the right deal with the US."),
    ("EARTH'S MISSING BILLION YEARS",
     "Scientists may have found why a billion years of history is missing."),
]


def draw_page():
    fill_rect(24, 24, 976, 3, INK)
    fill_rect(24, 997, 976, 3, INK)
    fill_rect(24, 24, 3, 976, INK)
    fill_rect(997, 24, 3, 976, INK)
    draw_text("THE WORLD TODAY", 512, 44, 8, INK, "center")
    fill_rect(36, 116, 952, 3, INK)
    fill_rect(36, 122, 952, 1, INK)
    draw_text("Thursday, 19 November 2026", 512, 132, 4, RED, "center")
    fill_rect(36, 168, 952, 2, INK)
    draw_text("GTA VI BEGINS", 512, 184, 6, INK, "center")
    draw_text("GLOBAL ROLLOUT", 512, 230, 6, INK, "center")
    deck = "Gamers enter Vice City as Grand Theft Auto VI launches worldwide after a 13-year wait."
    y = 288
    for line in wrap_lines(deck, 880, 2):
        draw_text(line, 512, y, 2, INK, "center")
        y += 24
    draw_skyline()
    draw_map()
    fill_rect(36, 580, 952, 2, INK)
    for x, stories in ((36, COL1), (368, COL2), (700, COL3)):
        yy = 592
        for headline, story_deck in stories:
            yy = draw_story(x, yy, 292, headline, story_deck)
    fill_rect(352, 592, 2, 340, INK)
    fill_rect(684, 592, 2, 340, INK)
    fill_rect(700, 820, 292, 2, RED)
    draw_text("BY THE NUMBERS", 700, 832, 2, RED)
    draw_text("13 YEARS - WAIT FOR GTA VI", 700, 858, 1, INK)
    draw_text("45 BN EUR - UKRAINE LOAN", 700, 872, 1, INK)
    draw_text("1 LIGHT-DAY - VOYAGER 1", 700, 886, 1, INK)
    fill_rect(36, 946, 952, 2, INK)
    draw_text("ONE PAGE. EVERY STORY THAT MATTERED.", 512, 960, 2, INK, "center")


def main():
    draw_page()
    save_png("entry.png")


if __name__ == "__main__":
    main()
