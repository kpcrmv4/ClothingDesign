# Baby Fashion Engine - แผนพัฒนา MCP Server

## ภาพรวมโปรเจกต์

MCP Server สำหรับสร้างแพทเทิร์นเสื้อผ้าเด็กเล็ก (0-24 เดือน) ออกมาเป็น PDF
ที่แบ่งเป็นหน้า A4 ต่อกันได้ พร้อมเครื่องหมายช่วยเย็บแบบมืออาชีพ

### เป้าหมายหลัก
- รองรับแพทเทิร์นหลายประเภท (ไม่ใช่แค่เดรส)
- ใช้เส้นโค้ง bezier แทนเส้นตรงล้วนเพื่อให้แพทเทิร์นเหมือนของจริง
- มีเครื่องหมาย notch, grain line, fold edge, registration grid
- คำนวณปริมาณผ้าที่ต้องใช้ให้ได้
- ให้คำแนะนำการเย็บเบื้องต้น

### หน่วยและมาตรฐาน
- ใช้ cm ตลอดทั้งไฟล์
- พิกัด (0, 0) อยู่มุมล่างซ้ายของ virtual canvas (ตาม reportlab)
- seam allowance ค่าเริ่มต้น 1.0 cm (ปรับต่อขอบได้)

---

## โครงสร้างไฟล์ baby_pattern_server.py

```
1. Module docstring + imports
2. SIZE_CHART (ขยายจาก 4 เป็น 6 ไซส์ เพิ่มฟิลด์วัดตัว)
3. ค่าคงที่หน้ากระดาษ (PRINTABLE_W_CM, PRINTABLE_H_CM)
4. Drawing utilities (ฟังก์ชันช่วยวาด):
   - _grid_ref()                แปลง col,row เป็น A1/A2/B1
   - draw_grain_line()          ลูกศรแนวเส้นด้าย
   - draw_notch()                ขีด V ที่ขอบชิ้น
   - draw_fold_edge()           เส้น chain-dot สำหรับตัดบนผ้าพับ
   - draw_bezier_edge()         เส้นโค้งสำหรับวงคอ วงแขน
   - draw_piece_rect()          สี่เหลี่ยมพร้อม SA ต่อขอบ
   - draw_calibration()         จัตุรัส 5x5 + bar วัด 10 cm
   - draw_page_header()         หัวกระดาษบอกชื่อแพทเทิร์น + grid ref
   - draw_registration_marks()  เครื่องหมายเล็ง 4 มุม
   - tile_and_save()            ฟังก์ชันหลัก tile virtual canvas ลง A4 หลายหน้า
5. Fabric calculator
   - calculate_yardage()        รับ bbox -> คืนเมตรผ้าที่ต้องใช้ 3 ความกว้าง
6. @mcp.tool() ต่าง ๆ
7. if __name__ == "__main__": mcp.run()
```

---

## SIZE_CHART ที่จะใช้ (ขยายจากต้นฉบับ)

| ฟิลด์ | ความหมาย |
|------|---------|
| chest | รอบอก |
| length | ความยาวตัวเสื้อ (ไหล่ถึงชายเสื้อ) |
| waist | รอบเอว |
| hip | รอบสะโพก |
| back_w | ความกว้างหลัง (ไหล่ถึงไหล่) |
| shoulder | ความยาวบ่า (คอถึงปลายไหล่) |
| neck_circ | รอบคอ |
| arm_len | ความยาวแขน (ไหล่ถึงข้อมือ) |
| rise_f | ระยะหน้าเป้า (เอวหน้าถึงก้น) |
| rise_b | ระยะหลังเป้า |
| head | รอบศีรษะ |
| strap_len | ความยาวสาย |
| ruffle_h | ความสูงระบาย |

**ไซส์:** 0-3m, 3-6m, 6-9m, 9-12m, 12-18m, 18-24m

---

## Tool ที่จะเขียน

| # | ชื่อ tool | ส่วนประกอบหลัก | ใช้เส้นโค้ง? |
|---|---------|--------------|-------------|
| 1 | `generate_full_dress_pattern` | ตัวเสื้อ + สาย + ระบาย | ใช่ (วงคอ วงแขน) |
| 2 | `generate_bloomers_pattern` | กางเกงใน 1 ชิ้นพับ | ใช่ (เป้าโค้ง) |
| 3 | `generate_bib_pattern` | ผ้ากันเปื้อน | ใช่ (keyhole คอ) |
| 4 | `generate_bonnet_pattern` | หมวกคลุมผม: crown + brim + tie | ใช่ (โค้งมาก) |
| 5 | `calculate_fabric_requirement` | คำนวณผ้าต่อ pattern | - |
| 6 | `list_available_sizes` | คืน SIZE_CHART เป็น JSON-like | - |

### ข้อตกลงทั่วไปของ tool แต่ละตัว

แต่ละ pattern tool รับพารามิเตอร์:
- `size_label: str` - เลือกจาก SIZE_CHART
- `seam_allowance: float = 1.0` - SA ค่าเริ่มต้น
- `include_instructions: bool = True` - แนบหน้าคำแนะนำเย็บ

และคืน string: สถานะ + path ของไฟล์ PDF + จำนวนหน้า

---

## แผนการพัฒนาเป็นเฟส

### Phase 1: Foundation (จำเป็นก่อน)
- [ ] Module docstring, imports, mcp init
- [ ] SIZE_CHART ขยาย 6 ไซส์
- [ ] ค่าคงที่หน้ากระดาษ + `_grid_ref()`

### Phase 2: Drawing primitives
- [ ] `draw_grain_line()`
- [ ] `draw_notch()`
- [ ] `draw_fold_edge()`
- [ ] `draw_bezier_edge()`
- [ ] `draw_calibration()`
- [ ] `draw_page_header()`
- [ ] `draw_registration_marks()`

### Phase 3: High-level tiling
- [ ] `tile_and_save()` — รับ draw_callback, ขนาด canvas, path -> ออก PDF
- [ ] `draw_instruction_page()` — หน้าแนะนำการเย็บ

### Phase 4: Tool แพทเทิร์น (1 ตัวต่อสเต็ป)
- [ ] 4a: `generate_full_dress_pattern` (ปรับปรุงของเดิม)
- [ ] 4b: `generate_bib_pattern` (ง่ายสุด เริ่มตรงนี้ได้)
- [ ] 4c: `generate_bloomers_pattern`
- [ ] 4d: `generate_bonnet_pattern`

### Phase 5: Tool สนับสนุน
- [ ] `calculate_fabric_requirement`
- [ ] `list_available_sizes`

### Phase 6: ทดสอบ + commit
- [ ] รัน smoke test (import + เรียก 1 tool)
- [ ] Commit แยกเฟส หรือ commit ใหญ่ก้อนเดียว
- [ ] Push branch `claude/baby-dress-pattern-ZUGM7`

---

## หลักการออกแบบที่จะยึด

1. **Virtual canvas ก่อน แล้วค่อย tile** — เขียนโค้ดวาดใน canvas ใหญ่ (หน่วย cm) แล้วให้ `tile_and_save()` ตัดเป็นหน้า A4 เอง ไม่ต้องคำนวณ offset ของแต่ละหน้าในโค้ดแต่ละ tool
2. **แต่ละ piece เป็น callback** — tool ส่ง `draw_fn(c)` เข้า `tile_and_save()` แทนการคำนวณ row/col เอง
3. **ไม่ over-abstract** — ไม่สร้าง dataclass `Piece` เต็มรูปแบบ เพราะ reportlab API ทำงานแบบ imperative อยู่แล้ว
4. **Fail กลับเป็น error string** — เพื่อให้ผู้ใช้เห็นข้อความใน Claude Desktop เมื่อใส่ไซส์ผิด
5. **ใช้ bezier curve 4-จุด** — reportlab มี `c.bezier(x1,y1,x2,y2,x3,y3,x4,y4)` พอสำหรับวงคอ/วงแขน

---

## สิ่งที่จะ *ไม่* ทำในรอบนี้

- Multi-size nested patterns (เลือกไซส์ได้ในไฟล์เดียว)
- Bin-packing จัดวางชิ้นส่วนให้กินหน้ากระดาษน้อยสุด — จัดวางแนวตั้งธรรมดาไปก่อน
- Export SVG/DXF
- ความซับซ้อนระดับมืออาชีพ (dart, pleat calculator)
- Image-to-pattern (รับรูปแล้วออกแพทเทิร์น)
- Romper, Sleep sack, Pinafore — เก็บไว้เฟสถัดไป

---

## หมายเหตุสำหรับ Claude เซสชันถัดไป

- Branch: `claude/baby-dress-pattern-ZUGM7`
- ไฟล์หลัก: `baby_pattern_server.py`
- ต้องติดตั้ง `pip install mcp reportlab` ก่อนใช้งาน
- สคริปต์นี้ต้อง register ใน `claude_desktop_config.json` ถึงจะเรียกผ่าน Claude Desktop ได้
- PDF output จะถูกเขียนไว้ที่ current working directory ของ server
