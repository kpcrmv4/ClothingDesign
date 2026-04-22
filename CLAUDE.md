# Baby Fashion Engine — Master Plan

## ภาพรวมโปรเจกต์

MCP server สำหรับสร้างแพทเทิร์นเสื้อผ้าเด็กเล็ก (0-24 เดือน) ครบวงจร
ตั้งแต่ออกแบบจากข้อความ/รูปภาพ → generate PDF แบบตัด A4 ต่อกันได้
→ แนะนำวัสดุ/ผ้า → ให้ preview ก่อนพิมพ์จริง

### เป้าหมาย
- แพทเทิร์นครอบคลุมตู้เสื้อผ้าเด็ก: เดรส, กางเกง, เสื้อยืด, ชุดหมี, ชุดนอน, หมวก, ผ้ากันเปื้อน
- ใช้ Claude วิเคราะห์รูป/ข้อความแล้วเลือก pattern + params ให้อัตโนมัติ
- แสดง preview PNG ก่อน generate PDF จริง
- ผลลัพธ์ระดับมืออาชีพ: bezier curves, notches, grain, fold, pattern symbols
- ให้ shopping list วัสดุ + cutting layout บนผ้ากว้างจริง

### หน่วย / มาตรฐาน
- ทุกอย่างเป็น cm
- พิกัด (0, 0) มุมล่างซ้ายของ virtual canvas
- SA เริ่มต้น 1.0 cm (ปรับต่อ tool ได้)
- A4 printable area: 19 x 27.7 cm (margin 1 cm รอบ)

---

## โครงสร้างไฟล์ (เป้าหมาย)

```
clothingdesign/
├── baby_pattern_server.py     # entry: FastMCP + @mcp.tool() รวมศูนย์
├── requirements.txt
├── .gitignore
├── CLAUDE.md
├── sizes.py                   # SIZE_CHART + helpers
├── constants.py               # page geometry, default SA
├── drawing.py                 # primitives: grain, notch, fold, bezier, tiling
├── symbols.py                 # dart, pleat, gather, buttonhole, pocket
├── preview.py                 # PNG thumbnail (Pillow)
├── features.py                # shopping list, cutting layout, customize, difficulty metadata
└── patterns/
    ├── __init__.py
    ├── dress.py
    ├── bib.py
    ├── bloomers.py
    ├── bonnet.py
    ├── kimono_top.py          # เสื้อป้ายผูกข้าง
    ├── pants.py               # กางเกงขายาว/ขาสั้น เอวยางยืด
    ├── tshirt.py              # เสื้อยืดคอกลม
    ├── romper.py              # ชุดหมี เสื้อ+กางเกงเป็นชิ้นเดียว
    └── sleep_sack.py          # ถุงนอนซิป
```

หมายเหตุ: ใช้ flat-ish structure ไม่ต้องลึกเกินไป ง่ายต่อการนำทาง

---

## SIZE_CHART

ไซส์: `0-3m`, `3-6m`, `6-9m`, `9-12m`, `12-18m`, `18-24m`

ฟิลด์: `chest`, `length`, `waist`, `hip`, `back_w`, `shoulder`, `neck_circ`,
`arm_len`, `rise_f`, `rise_b`, `head`, `strap_len`, `ruffle_h`

---

## Tool ที่จะมีทั้งหมด

### Pattern generators (9 ตัว)
| # | Tool | Description |
|---|------|-------------|
| 1 | `generate_full_dress_pattern` | เดรสไม่มีแขน สาย + ระบาย |
| 2 | `generate_bib_pattern` | ผ้ากันเปื้อน keyhole |
| 3 | `generate_bloomers_pattern` | กางเกงใน/คลุมผ้าอ้อม เป้าโค้ง |
| 4 | `generate_bonnet_pattern` | หมวกคลุมผม 3 ชิ้น |
| 5 | `generate_kimono_top_pattern` | เสื้อป้ายผูกข้าง ไม่มีกระดุม |
| 6 | `generate_pants_pattern` | กางเกงเอวยางยืด ขายาว/ขาสั้น |
| 7 | `generate_tshirt_pattern` | เสื้อยืดแขนสั้น คอกลม |
| 8 | `generate_romper_pattern` | ชุดหมี เสื้อ+กางเกง |
| 9 | `generate_sleep_sack_pattern` | ถุงนอนซิป |

### Support tools (7 ตัว)
| # | Tool | Description |
|---|------|-------------|
| 10 | `list_available_sizes` | ดูไซส์ทั้งหมดพร้อมสัดส่วน |
| 11 | `list_all_patterns` | ลิสต์แพทเทิร์นพร้อม difficulty, time, fabric suggestion |
| 12 | `calculate_fabric_requirement` | คำนวณเมตรผ้า 3 ความกว้าง |
| 13 | `generate_shopping_list` | รายการวัสดุครบ: ผ้า, ด้าย, ยางยืด, กระดุม, ฯลฯ |
| 14 | `generate_cutting_layout` | PNG แสดงผังวางชิ้นบนผ้ากว้างจริง |
| 15 | `generate_pattern_preview` | PNG thumbnail ของแพทเทิร์นก่อน generate PDF |
| 16 | `suggest_pattern_from_description` | รับบรรยาย/คำอธิบายรูป → แนะนำ tool + params |

---

## แผนการพัฒนาเป็นเฟส

### Phase A — Restructure + Metadata + Shopping (ฐาน)
- [ ] แตกไฟล์เดิมเป็นโมดูล (`sizes.py`, `constants.py`, `drawing.py`, `patterns/`)
- [ ] สร้าง `PATTERN_META` dict: difficulty, estimated_time, fabric_types
- [ ] เพิ่ม tool `list_all_patterns`
- [ ] เพิ่ม tool `generate_shopping_list` พร้อมข้อมูลวัสดุต่อแพทเทิร์น
- [ ] Smoke test + commit

### Phase B — แพทเทิร์นใหม่ 5 ตัว
- [ ] B1: `kimono_top.py` + tool
- [ ] B2: `pants.py` + tool (รองรับทั้งขายาว/ขาสั้นผ่าน param)
- [ ] B3: `tshirt.py` + tool
- [ ] B4: `romper.py` + tool
- [ ] B5: `sleep_sack.py` + tool
- [ ] Smoke test ทุกตัว + commit

### Phase C — Visual features
- [ ] C1: `symbols.py` — dart, pleat, gather marks, buttonhole, pocket placement
- [ ] C2: `preview.py` — PNG preview ใช้ Pillow (แยกจาก PDF rendering)
- [ ] C3: เพิ่ม tool `generate_pattern_preview`
- [ ] C4: `features.py:generate_cutting_layout` — PNG ผังวางบนผ้า 115/150 cm
- [ ] Smoke test + commit

### Phase D — Smart features
- [ ] D1: `features.py:customize_pattern` — รับ changes dict แปลงเป็น param override
- [ ] D2: tool `suggest_pattern_from_description` — Claude ใช้ตีความรูป/ข้อความ
- [ ] D3: ปรับ docstring ของทุก pattern tool ให้ Claude เลือกใช้ถูก
- [ ] Test กับบรรยายจริง + commit

### Phase E — Final polish
- [ ] Update README-style docstring ใน `baby_pattern_server.py`
- [ ] Push branch สุดท้าย

---

## หลักการออกแบบที่ยึด

1. **Virtual canvas ก่อน แล้ว tile** — วาดใน cm coordinate แล้ว `tile_and_save()` จัดการ A4
2. **แต่ละ pattern = draw_fn(canvas)** callback — ไม่ต้องคำนวณหน้ากันเอง
3. **Preview = Pillow, PDF = reportlab** — คนละ renderer แต่ share geometry calculation
4. **ไม่ over-abstract** — ไม่สร้าง Piece dataclass ที่บังคับใช้ทุกที่ เอาแค่ dict/tuple ก็พอ
5. **Fail → error string** — ผู้ใช้เห็นใน Claude Desktop ได้ชัด
6. **เลี่ยง dependency หนัก** — ใช้ Pillow (มากับ reportlab) แทน cairosvg/poppler

---

## สิ่งที่ *ไม่* ทำในรอบนี้

- Multi-size nested PDF (เลือกไซส์ได้ไฟล์เดียว)
- Bin-packing แพทเทิร์นแบบแม่นยำ (วางแนวตั้งก็พอ)
- Proper seam allowance offset บนโค้ง (ใช้ bounding box ง่าย ๆ ก่อน)
- DXF/SVG export สำหรับเครื่องตัดดิจิทัล
- Fabric shrinkage compensation
- Pattern versioning/history (ใช้ git)
- Custom measurements per child (Phase ถัดไป)

---

## Dependencies

```
mcp>=1.0
reportlab>=4.0
Pillow>=10.0    # PNG preview + cutting layout
```

Pillow มากับ reportlab อยู่แล้ว ไม่ต้องติดตั้งเพิ่ม

---

## หมายเหตุสำหรับเซสชันถัดไป

- Branch: `claude/baby-dress-pattern-ZUGM7`
- Entry: `baby_pattern_server.py`
- รัน: `python baby_pattern_server.py` (ต้อง cd เข้ามาในโฟลเดอร์ ไม่งั้น import error)
- PDF/PNG output ไปที่ `cwd` ของ server (ผู้ใช้ตั้งใน `claude_desktop_config.json`)
- การเพิ่ม pattern ใหม่: สร้างไฟล์ใน `patterns/` + เพิ่ม `PATTERN_META` + `@mcp.tool()` ที่ `baby_pattern_server.py`
