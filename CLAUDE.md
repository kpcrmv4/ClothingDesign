# Baby Fashion Engine — คู่มือโปรเจกต์

## ภาพรวม

MCP server สำหรับสร้างแพทเทิร์นเสื้อผ้าเด็กเล็ก (0-24 เดือน) ครบวงจร
ตั้งแต่ออกแบบจากข้อความ/รูปภาพ → generate PDF แบบตัด A4 ต่อกันได้
→ แนะนำวัสดุ/ผ้า → ให้ preview ก่อนพิมพ์จริง

### หน่วย / มาตรฐาน
- ทุกอย่างเป็น cm
- พิกัด (0, 0) มุมล่างซ้ายของ virtual canvas
- SA เริ่มต้น 1.0 cm (ปรับต่อ tool ได้)
- A4 printable area: 19 x 27.7 cm (margin 1 cm รอบ)

---

## โครงสร้างไฟล์ (ตามจริง)

```
clothingdesign/
├── baby_pattern_server.py   # entry: tool definitions + run/publish plumbing เท่านั้น
├── geometry.py              # ★ แหล่งความจริงเดียวของขนาดชิ้นทุกแพทเทิร์น + shelf packer
├── sizes.py                 # SIZE_CHART + get_size()
├── constants.py             # page geometry, default SA
├── drawing.py               # primitives ฝั่ง reportlab + ลงทะเบียนฟอนต์ไทย + tiling
├── symbols.py               # dart, pleat, gather, buttonhole, pocket
├── fonts.py                 # หาฟอนต์ไทยสำหรับฝั่ง Pillow (preview/rendered/layout)
├── preview.py               # PNG รูปทรงชิ้นแบน
├── rendered.py              # PNG ภาพชุดเมื่อเย็บเสร็จ (ใช้เป็น thumbnail แคตตาล็อก)
├── cutting_layout.py        # PNG ผังวางชิ้นบนผ้า
├── features.py              # PATTERN_META + คำนวณผ้า + รายการซื้อของ
├── customize.py             # ตีความคำบรรยาย → แพทเทิร์น + พารามิเตอร์
├── gallery.py               # จัดการ outputs/ + สร้าง index.html
├── test_smoke.py            # ชุดทดสอบ (รันเปล่า ๆ ได้ ไม่ต้องมี pytest)
└── patterns/                # วาดแต่ละแพทเทิร์นลง PDF
    ├── dress.py             # เดรสสายไหล่ (ชายระบาย / ชายบอลลูน / สาบกระดุม)
    ├── tiered_dress.py      # เดรสกระโปรงชั้น (คอกลม / halter / สายไหล่)
    ├── flutter_top.py       # เสื้อคอระบายแขนระบาย (ใส่ใต้เดรส/เอี๊ยม)
    ├── bib.py  bloomers.py  bonnet.py  kimono_top.py
    └── pants.py  tshirt.py  romper.py  sleep_sack.py  flutter_romper.py
```

---

## กฎเหล็ก 3 ข้อ (อ่านก่อนแก้โค้ด)

### 1. ขนาดชิ้นอยู่ที่ `geometry.py` ที่เดียว
เดิมสูตรคำนวณขนาดถูก copy ไว้ 4 ที่ (pattern, preview, features, cutting_layout)
แล้ว**ค่าไม่ตรงกันจริง ๆ** — ความยาวขากางเกงในรายการซื้อของต่างจากผังตัดเกือบเท่าตัว
ตอนนี้ทุกฝ่ายอ่านจาก `geometry.py`:

```python
geometry.<key>_dims(spec, **params)   # ค่าที่ pattern/preview ใช้วาด
geometry.get_pieces(key, size, **p)   # cut list สำหรับ features + cutting_layout
geometry.pack_pieces(pieces, width)   # shelf packer ที่ทั้งสองฝ่ายใช้ร่วมกัน
```

`test_fabric_estimate_matches_cutting_layout` ล็อกไว้ไม่ให้กลับไปแตกอีก

### 2. ห้ามใช้ `os.chdir()` — ส่ง `output_dir` เข้าไปแทน
ทุก `generate()` / `generate_preview()` / `render_finished()` / `generate_layout()`
รับ `output_dir: str = "."` และประกอบ path ด้วย `os.path.join()`
(`os.chdir` เป็น global state — ถ้ามี 2 request พร้อมกันไฟล์จะไปตกผิดโฟลเดอร์)
`test_output_dir_is_respected` ล็อกไว้

### 3. ห้าม hardcode `"Tahoma"` — ใช้ `THAI_FONT` / `THAI_FONT_BOLD`
เครื่องที่ไม่มีฟอนต์ไทยจะ fallback เป็น Helvetica พร้อมคำเตือน
ถ้า hardcode ชื่อฟอนต์ reportlab จะโยน KeyError กลางคัน
ฝั่ง PNG ใช้ `fonts.pil_font(size, bold)`

---

## Tool ที่มีทั้งหมด (24 ตัว)

### Pattern generators (12)
| Tool | คำอธิบาย | ตัวเลือกพิเศษ |
|------|----------|---------------|
| `generate_full_dress_pattern` | เดรสสายไหล่ + ระบาย | `skirt_style` (gathered/bubble), `front_placket` |
| `generate_tiered_dress_pattern` | เดรสกระโปรงชั้น | `tiers` (2-3), `neckline` (round/halter/strap), `tier_fullness`, `lace_trim` |
| `generate_flutter_top_pattern` | เสื้อคอระบายแขนระบาย (ใส่ใต้เดรส) | `sleeve_fullness`, `neck_finish` (ruffle/binding) |
| `generate_bib_pattern` | ผ้ากันเปื้อน keyhole | — |
| `generate_bloomers_pattern` | กางเกงคลุมผ้าอ้อม | — |
| `generate_bonnet_pattern` | หมวกคลุมผม 3 ชิ้น | — |
| `generate_kimono_top_pattern` | เสื้อป้ายผูกข้าง | — |
| `generate_pants_pattern` | กางเกงเอวยางยืด | `style` (long/short) |
| `generate_tshirt_pattern` | เสื้อยืดคอกลม | `sleeve` (short/long) |
| `generate_romper_pattern` | ชุดหมีสายไหล่ snap เป้า | — |
| `generate_sleep_sack_pattern` | ถุงนอนซิป | — |
| `generate_flutter_romper_pattern` | ชุดหมีคอระบาย off-shoulder | `ruffle_height`, `ruffle_fullness`, `crotch_snaps` |

### Support tools (12)
`list_available_sizes` · `list_all_patterns` · `calculate_fabric_requirement` ·
`generate_shopping_list` · `generate_pattern_preview` · `generate_cutting_layout` ·
`suggest_pattern_from_description` · `customize_pattern` · `rebuild_gallery_index` ·
`publish_gallery` · `set_auto_publish` · `git_status_summary`

---

## การเพิ่มแพทเทิร์นใหม่ (checklist)

1. `geometry.py` — เพิ่ม `<key>_dims()` + สาขาใน `get_pieces()`
2. `patterns/<key>.py` — `generate(size_label, seam_allowance=1.0, ..., output_dir=".")`
   เรียก `geometry.<key>_dims()` ห้ามคำนวณขนาดเอง
3. `features.PATTERN_META` — เพิ่ม title, title_th, emoji, difficulty, notions, pieces
4. `preview.py` — เพิ่ม `_preview_<key>()` + สาขาใน `generate_preview()`
5. `rendered.py` — เพิ่ม `_render_<key>()` + สาขาใน `render_finished()`
6. `customize.py` — เพิ่มคีย์เวิร์ดใน `_KEYWORDS` + ตัวเลือกใน `_PATTERN_PARAMS`
7. `baby_pattern_server.py` — เพิ่ม `@mcp.tool()` พร้อม docstring ที่บอกว่า
   **เมื่อไหร่ควรใช้ / เมื่อไหร่ควรใช้ตัวอื่นแทน** (Claude เลือก tool จากตรงนี้)
8. `test_smoke.py` — เพิ่มลง `GENERATORS` แล้วรัน

คีย์เวิร์ดต้องระวังการชนกัน: `_score_matches()` ให้คำที่ยาวกว่าชนะ
เพื่อไม่ให้ "กางเกงใน" ไปโดน "กางเกง" ด้วย — มีเทสต์ล็อกไว้

---

## การทดสอบ

```bash
python test_smoke.py          # ไม่ต้องมี pytest
pytest test_smoke.py -q       # หรือแบบนี้
```

ครอบคลุม: ทุกแพทเทิร์น × หลายไซส์ generate ได้จริง, ตัวเลขผ้าตรงกับผังตัด,
ผ้าหน้ากว้างขึ้นต้องไม่ใช้ผ้ายาวขึ้น, พารามิเตอร์ผิดต้องคืน error string ไม่ใช่ traceback,
คีย์เวิร์ดไม่ชนกัน, ไม่มีไฟล์รั่วออกนอก `output_dir`

---

## Auto-publish / GitHub Pages

ทุกครั้งที่ generate สำเร็จ ระบบจะ `git add -A && commit && push` ให้อัตโนมัติ
แล้ว GitHub Pages จะอัปเดตแคตตาล็อกภายใน 1-2 นาที (ใช้ดูผลงานจากมือถือได้)

ตั้งค่าผ่าน `set_auto_publish(enabled, allow_default_branch)` — บันทึกลง
`.engine_config.json` (gitignore ไว้) จึงอยู่ข้ามการรีสตาร์ท

**ตัวป้องกัน:** ระบบจะไม่ auto-push ขณะอยู่บน branch `main`/`master`
เว้นแต่สั่ง `allow_default_branch=True` — กันผลงานหลุดขึ้น branch หลักโดยไม่ตั้งใจ

**ข้อควรรู้:** ทุก run จะ commit ไฟล์ PDF/PNG เข้า git ทำให้ repo โตเร็ว
(git เก็บทุกเวอร์ชันตลอดไป ลบทีหลังก็ไม่ยุบ) ถ้าเริ่มหนักเกินไป ทางแก้คือย้าย
`outputs/` ไป branch `gh-pages` แยกแล้ว force-push ทับ — ยังไม่ได้ทำในรอบนี้

---

## หลักการออกแบบที่ยึด

1. **Virtual canvas ก่อน แล้ว tile** — วาดใน cm coordinate แล้ว `tile_and_save()` จัดการ A4
2. **แต่ละ pattern = draw_fn(canvas)** callback — ไม่ต้องคำนวณหน้ากันเอง
3. **Preview = Pillow, PDF = reportlab** — คนละ renderer แต่ **share geometry จาก `geometry.py`**
4. **ไม่ over-abstract** — piece เป็น dict ธรรมดา ไม่ต้องมี dataclass
5. **Fail → error string** — ผู้ใช้เห็นใน Claude ได้ชัด ไม่ใช่ traceback
6. **เลี่ยง dependency หนัก** — ใช้ Pillow (มากับ reportlab) แทน cairosvg/poppler

---

## สิ่งที่ *ยัง* ไม่ทำ

- Multi-size nested PDF (เลือกไซส์ได้ไฟล์เดียว)
- Bin-packing แบบแม่นยำ (ใช้ shelf packing แบบลองหลายกลยุทธ์แล้วเลือกที่สั้นสุด)
- Proper seam allowance offset บนโค้ง (ใช้ bounding box ง่าย ๆ)
- DXF/SVG export สำหรับเครื่องตัดดิจิทัล
- Fabric shrinkage compensation
- Custom measurements per child
- แยก `outputs/` ไป branch `gh-pages` (ดูหัวข้อ Auto-publish)

---

## Dependencies

```
mcp>=1.0          # รองรับทั้ง SDK 1.x (FastMCP) และ 2.x (MCPServer)
reportlab>=4.0
Pillow>=10.0
```

ฟอนต์ไทยไม่ใช่ dependency แต่ถ้าไม่มี ข้อความไทยใน PDF จะเพี้ยน
(ระบบจะเตือนในผลลัพธ์) แนะนำ Tahoma / Leelawadee / Noto Sans Thai / TLWG

---

## หมายเหตุสำหรับเซสชันถัดไป

- Branch ปัจจุบัน: `claude/system-analysis-improvement-zcg11t`
- Entry: `baby_pattern_server.py` — รันด้วย `python baby_pattern_server.py`
  (ต้อง cd เข้ามาในโฟลเดอร์ก่อน ไม่งั้น import ไม่เจอ)
- ผลลัพธ์ทั้งหมดลง `outputs/<label>_<timestamp>/` ไม่ลง cwd อีกแล้ว
