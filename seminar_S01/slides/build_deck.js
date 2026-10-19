// Dung deck S01 - Stack-based Buffer Overflow. Chay: node build_deck.js
const pptx = require('pptxgenjs');
const path = require('path');

const EV = path.join(__dirname, '..', 'evidence');
const img = (n) => path.join(EV, n);

// ---- Palette (chu de khai thac lo hong) ----
const BG_DARK = '14181F';
const BG_LIGHT = 'FFFFFF';
const INK = '1B2430';      // chu dam tren nen sang
const MUTED = '6B7280';
const RED = 'E63946';      // nhan manh "lo hong"
const STEEL = '2A6F97';    // xanh thep
const GREEN = '2E8B57';    // "da sua / an toan"
const CODEBG = '0F1419';   // nen terminal
const CODEFG = 'E6EDF3';
const HEAD = 'Cambria';
const BODY = 'Calibri';
const MONO = 'Courier New';

const p = new pptx();
p.layout = 'LAYOUT_WIDE';     // 13.33 x 7.5
p.author = 'Nhom 3 - NT521';
p.title = 'S01 - Stack-based Buffer Overflow';

const W = 13.33, H = 7.5;

// ---- helpers ----
function tb(slide, text, opts) { slide.addText(text, Object.assign({ isTextBox: true, margin: 0, fontFace: BODY }, opts)); }

function title(slide, text, color) {
  tb(slide, text, { x: 0.6, y: 0.4, w: 12.1, h: 0.95, fontFace: HEAD, fontSize: 32, bold: true, color: color || INK, align: 'left', valign: 'middle' });
}

function tag(slide, text) { // nhan "Muc N" goc phai tren
  tb(slide, text, { x: 9.9, y: 0.52, w: 2.8, h: 0.5, fontFace: BODY, fontSize: 12, bold: true, color: RED, align: 'right', valign: 'middle' });
}

// fit anh vao vung (maxW x maxH) giu ti le; tra ve {x,y,w,h} can giua vung
function fit(x, y, maxW, maxH, ar) {
  let w = maxW, h = w / ar;
  if (h > maxH) { h = maxH; w = h * ar; }
  return { x: x + (maxW - w) / 2, y: y + (maxH - h) / 2, w, h };
}
const AR = { '01': 936/420, '02': 936/368, '03': 1294/1036, '04': 1274/864, '05': 1676/880 };

function shot(slide, name, x, y, maxW, maxH) {
  const f = fit(x, y, maxW, maxH, AR[name]);
  slide.addImage({ path: img(`${name}_` + ({'01':'kiem_tra_binary','02':'chay_binh_thuong','03':'sink_va_buffer','04':'debugger_truoc_sau','05':'ket_qua_challenge'}[name])) + '.png', x: f.x, y: f.y, w: f.w, h: f.h });
  slide.addShape(p.ShapeType.rect, { x: f.x, y: f.y, w: f.w, h: f.h, line: { color: MUTED, width: 0.75 }, fill: { color: 'FFFFFF', transparency: 100 } });
  return f;
}

function bullets(slide, items, opts) {
  const o = Object.assign({ x: 0.6, y: 1.6, w: 7.2, h: 5.2, fontSize: 16, color: INK, align: 'left', valign: 'top', lineSpacingMultiple: 1.05, paraSpaceAfter: 10 }, opts);
  const arr = items.map((t, i) => (typeof t === 'string'
    ? { text: t, options: { bullet: { indent: 18 }, breakLine: i !== items.length - 1 } }
    : Object.assign({}, t, { options: Object.assign({ bullet: { indent: 18 }, breakLine: i !== items.length - 1 }, t.options) })));
  slide.addText(arr, Object.assign({ isTextBox: true, margin: 0, fontFace: BODY }, o));
}

function darkBg(slide) { slide.background = { color: BG_DARK }; }

// ============ SLIDE 1 - Title (dark) ============
let s = p.addSlide(); darkBg(s);
tb(s, 'CWE-121', { x: 0.9, y: 2.0, w: 6, h: 0.6, fontFace: MONO, fontSize: 18, bold: true, color: RED });
tb(s, 'Stack-based Buffer Overflow', { x: 0.9, y: 2.55, w: 11.5, h: 1.7, fontFace: HEAD, fontSize: 48, bold: true, color: 'FFFFFF' });
tb(s, 'Tran bo dem tren stack — tu ghi vuot den dieu khien luong thuc thi', { x: 0.9, y: 4.25, w: 11.3, h: 0.7, fontSize: 18, color: 'CADCFC' });
tb(s, 'Mini seminar S01  ·  NT521 — Lap trinh khai thac lo hong', { x: 0.9, y: 5.6, w: 11, h: 0.5, fontSize: 15, color: 'AAB4C4' });
tb(s, 'Nhom 3:  [CHUA CHOT: A, B, C]        ·        Ngay: [CHUA CHOT]', { x: 0.9, y: 6.05, w: 11, h: 0.5, fontSize: 13, color: '7E8A9C' });
s.addNotes('Gioi thieu nhom. Muc tieu: phan tich lo hong tran stack theo mach source->sink->guard, demo CTF ret2win va mot CVE that (glibc CVE-2015-7547).');

// ============ SLIDE 2 - Muc 1: Gioi thieu & boi canh ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 1 — Gioi thieu');
title(s, 'Lo hong tran bo dem tren stack la gi?');
bullets(s, [
  { text: 'Buffer = vung nho co dinh; tren stack la bien cuc bo (vd char buf[64])', options: {} },
  'Overflow = ghi NHIEU HON suc chua -> de du lieu nam ke ben',
  { text: 'Du lieu vao tu: nguoi dung, tep, mang', options: {} },
  'Hay gap: C/C++, dich vu mang, thu vien he thong, firmware',
  'Tac dong: tu crash -> chiem quyen dieu khien luong thuc thi',
], { w: 7.1, y: 1.7 });
// khung minh hoa phai
s.addShape(p.ShapeType.roundRect, { x: 8.1, y: 1.9, w: 4.6, h: 4.3, rectRadius: 0.08, fill: { color: 'F4F6F9' }, line: { color: 'DDE3EA', width: 1 } });
tb(s, 'Vi du', { x: 8.4, y: 2.1, w: 4, h: 0.4, fontSize: 13, bold: true, color: RED });
s.addText([
  { text: 'char buf[64];\n', options: { color: CODEFG } },
  { text: 'read(0, buf, 200);', options: { color: '9CDCFE' } },
], { isTextBox: true, margin: 8, x: 8.4, y: 2.55, w: 4.0, h: 0.95, fontFace: MONO, fontSize: 14, fill: { color: CODEBG }, valign: 'middle' });
tb(s, 'Doc 200 byte vao cho chi chua 64 byte\n=> ghi vuot 136 byte, de len du lieu stack ke ben.', { x: 8.4, y: 3.7, w: 4.0, h: 1.2, fontSize: 13, color: INK });
s.addNotes('Nhap chuoi qua dai. Nhan manh: loi o ngon ngu khong kiem tra bien tu dong.');

// ============ SLIDE 3 - Muc 2: Nguyen ly + so do stack ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 2 — Nguyen ly');
title(s, 'Nguyen ly, dieu kien va dang pho bien');
bullets(s, [
  'Ghi tu buf di len dia chi cao -> cham saved rbp -> dia chi tra ve',
  { text: 'Dieu kien: (a) input toi duoc sink; (b) ghi khong gioi han theo kich thuoc dich; (c) buffer tren stack', options: {} },
  'Dang pho bien: strcpy/gets/scanf("%s"); read(fd,buf,n) voi n lon; off-by-one; tinh sai do dai',
  { text: 'Phan biet: CRASH ≠ dieu khien duoc luong thuc thi', options: { color: RED, bold: true } },
], { w: 7.0, y: 1.7 });
// So do stack minh hoa (phai)
const sx = 9.0, sw = 3.4; let sy = 1.75; const rh = 0.7;
function stackRow(label, col, note) {
  s.addShape(p.ShapeType.rect, { x: sx, y: sy, w: sw, h: rh, fill: { color: col }, line: { color: 'FFFFFF', width: 1.5 } });
  tb(s, label, { x: sx, y: sy, w: sw, h: rh, fontSize: 12.5, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle' });
  if (note) tb(s, note, { x: sx + sw + 0.1, y: sy, w: 0.0, h: rh, fontSize: 10, color: MUTED, valign: 'middle' });
  sy += rh;
}
tb(s, 'dia chi CAO', { x: sx, y: sy - 0.32, w: sw, h: 0.3, fontSize: 9, italic: true, color: MUTED, align: 'center' });
stackRow('... frame caller', '8A94A6');
stackRow('dia chi tra ve', RED);
stackRow('saved rbp', STEEL);
stackRow('buf[63] ... buf[0]', '3E4756');
tb(s, 'dia chi THAP  ·  ghi bat dau tu buf di len', { x: sx - 0.3, y: sy + 0.05, w: sw + 0.6, h: 0.5, fontSize: 9, italic: true, color: MUTED, align: 'center' });
tb(s, 'So do minh hoa — offset that phai do tren binary', { x: sx - 0.3, y: sy + 0.55, w: sw + 0.6, h: 0.4, fontSize: 9, color: RED, align: 'center' });
s.addNotes('So do chi minh hoa. Khoang cach buf -> return address do bang gdb o phan demo.');

// ============ SLIDE 4 - Muc 3: CWE ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 3 — CWE');
title(s, 'CWE-121 va quan he ho hang');
// cay CWE (boxes)
function cweBox(x, y, w, t, col, txtcol) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h: 0.75, rectRadius: 0.06, fill: { color: col }, line: { color: 'FFFFFF', width: 1 } });
  tb(s, t, { x, y, w, h: 0.75, fontSize: 13, bold: true, color: txtcol || 'FFFFFF', align: 'center', valign: 'middle' });
}
cweBox(0.8, 1.75, 6.2, 'CWE-119  —  Thao tac vuot bien buffer (rong)', '8A94A6');
cweBox(1.4, 2.8, 5.6, 'CWE-787  —  Out-of-bounds Write', STEEL);
cweBox(2.0, 3.85, 5.0, 'CWE-121  —  Stack-based Buffer Overflow', RED);
tb(s, '← chu de S01', { x: 7.15, y: 3.85, w: 2, h: 0.75, fontSize: 12, bold: true, color: RED, valign: 'middle' });
bullets(s, [
  { text: 'CWE ≠ CVE', options: { bold: true } },
  'CWE = LOAI yeu diem (vd CWE-121)',
  'CVE = MOT lo hong cu the trong san pham cu the (vd CVE-2015-7547)',
  { text: 'Luu y that: NVD gan CVE-2015-7547 la CWE-119 (muc cha), ban chat ky thuat la 121', options: { color: STEEL } },
], { x: 8.0, y: 1.75, w: 4.8, fontSize: 14 });
s.addNotes('Trich dinh nghia MITRE nguyen van khi noi. NVD gan 119, ban chat la 121 (con cua 119) — khong tu sua nhan.');

// ============ SLIDE 5 - Muc 4: Vi tri & nguyen nhan (anh 03) ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 4 — Vi tri & nguyen nhan');
title(s, 'Vi tri & nguyen nhan trong binary ret2win');
bullets(s, [
  { text: 'Binary: ret2win (ROP Emporium, x86-64, not stripped)', options: {} },
  { text: 'checksec: No canary · NX enabled · No PIE', options: { color: RED, bold: true } },
  'Ham pwnme (0x4006e8): read(0, buf, 0x38=56) vao buffer 32 byte',
  { text: '=> doc 56 byte vao cho chua 32 byte -> ghi vuot 24 byte', options: { bold: true } },
  'Ham dich ret2win = 0x400756 (goi system("/bin/cat flag.txt"))',
], { x: 0.6, y: 1.7, w: 6.0, fontSize: 15 });
shot(s, '03', 6.8, 1.7, 6.1, 5.2);
s.addNotes('Chinh dong chu binary in: "fit 56 bytes into 32 bytes of stack buffer". Chi ro read va buffer trong disassembly.');

// ============ SLIDE 6 - Muc 5: Chuoi khai thac ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 5 — Chuoi khai thac');
title(s, 'Chuoi khai thac (5 buoc)');
const steps = [
  ['1', 'Gui input dai hon buffer (56 byte)'],
  ['2', 'Ghi tran qua 32B buffer + 8B saved rbp -> toi dia chi tra ve'],
  ['3', 'offset = 40 byte; ghi de bang dia chi ret2win = 0x400756'],
  ['4', 'Ham ket thuc -> lenh ret nhay toi ret2win()'],
  ['5', 'ret2win() goi system("/bin/cat flag.txt") -> in flag'],
];
let yy = 1.75;
steps.forEach(([n, t]) => {
  s.addShape(p.ShapeType.ellipse, { x: 0.7, y: yy, w: 0.6, h: 0.6, fill: { color: RED } });
  tb(s, n, { x: 0.7, y: yy, w: 0.6, h: 0.6, fontSize: 18, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle' });
  tb(s, t, { x: 1.5, y: yy, w: 7.2, h: 0.6, fontSize: 15, color: INK, valign: 'middle' });
  yy += 0.82;
});
s.addShape(p.ShapeType.roundRect, { x: 9.0, y: 1.9, w: 3.9, h: 2.6, rectRadius: 0.08, fill: { color: 'F4F6F9' }, line: { color: 'DDE3EA', width: 1 } });
tb(s, 'Payload', { x: 9.25, y: 2.1, w: 3.5, h: 0.4, fontSize: 13, bold: true, color: RED });
s.addText([
  { text: "b'A'*40\n", options: { color: CODEFG } },
  { text: '+ p64(0x400770)  ', options: { color: '9CDCFE' } },
  { text: '# ret gadget\n', options: { color: '6A9955' } },
  { text: '+ p64(0x400756)  ', options: { color: '9CDCFE' } },
  { text: '# ret2win', options: { color: '6A9955' } },
], { isTextBox: true, margin: 8, x: 9.25, y: 2.5, w: 3.45, h: 1.3, fontFace: MONO, fontSize: 12, fill: { color: CODEBG }, valign: 'top' });
tb(s, 'No PIE -> dia chi co dinh.\nNX khong can vi nhay toi ham co san.', { x: 9.25, y: 3.95, w: 3.5, h: 0.9, fontSize: 12, color: INK });
s.addNotes('Day la "ret-to-function", khong shellcode. Ret gadget giai thich o slide sau.');

// ============ SLIDE 7 - Muc 7: Demo kiem tra (anh 01 + 02) ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 7 — Demo');
title(s, 'Demo — kiem tra binary & chay binh thuong');
tb(s, 'uname -m · file · checksec', { x: 0.6, y: 1.55, w: 6, h: 0.4, fontSize: 13, bold: true, color: STEEL });
shot(s, '01', 0.6, 1.95, 6.1, 2.9);
tb(s, 'Chay input ngan -> thoat binh thuong', { x: 6.9, y: 1.55, w: 6, h: 0.4, fontSize: 13, bold: true, color: STEEL });
shot(s, '02', 6.9, 1.95, 6.0, 2.9);
tb(s, 'Moi truong: Kali amd64 tren UTM (Emulate) — duoc phep, co lap, an toan.', { x: 0.6, y: 6.5, w: 12, h: 0.5, fontSize: 13, italic: true, color: MUTED });
s.addNotes('Noi ro chay trong VM emulate; day la mot gioi han (slide dieu kien & gioi han).');

// ============ SLIDE 8 - Muc 7: dieu khien return (anh 04) ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 7 — Demo');
title(s, 'Da dieu khien dia chi tra ve');
shot(s, '04', 0.6, 1.7, 7.0, 5.2);
bullets(s, [
  'Lan chay dau: payload A*40 + ret2win (chua can le)',
  { text: 'In "Well done! Here\'s your flag:" -> da nhay vao ret2win()', options: { color: GREEN, bold: true } },
  { text: 'Roi SIGSEGV trong system() (stack lech 16 byte)', options: { color: RED } },
  'Bang chung: chay code cua ret2win = DA DIEU KHIEN return address, manh hon chi "crash"',
], { x: 7.8, y: 1.9, w: 5.1, fontSize: 15 });
s.addNotes('Phan biet muc bang chung: day la "da doi luong thuc thi", CHUA phai "dat muc tieu" (flag chua in vi system crash).');

// ============ SLIDE 9 - Muc 7: dat muc tieu (anh 05) ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 7 — Demo');
title(s, 'Dat muc tieu challenge — in flag');
shot(s, '05', 0.6, 1.7, 7.3, 5.2);
bullets(s, [
  'Lan 2: them ret gadget 0x400770 can le stack 16 byte',
  { text: 'exit code 0 -> in ROPE{a_placeholder_32byte_flag!}', options: { color: GREEN, bold: true } },
  'Vi sao can ret gadget: system() dung movaps doi stack boi so 16; mot ret day stack lech 8 byte cho khop',
  'Demo chay lai >= 2 lan on dinh (exit 0)',
], { x: 8.1, y: 1.9, w: 4.8, fontSize: 15 });
s.addNotes('Cau chuyen 2 buoc (control -> align -> flag) la diem nhan. Co phuong an anh/video du phong neu demo truc tiep loi.');

// ============ SLIDE 10 - Muc 6: CVE bang ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 6 — CVE');
title(s, 'CVE that: CVE-2015-7547 (glibc getaddrinfo)');
const rows = [
  ['San pham', 'glibc (getaddrinfo) — anh huong RHEL 6/7, Debian/Ubuntu/SUSE...'],
  ['Phien ban', '2.9 – 2.22, va tu 2.23'],
  ['CWE (NVD)', 'CWE-119 (ban chat la 121, con cua 119)'],
  ['CVSS', 'v2 6.8  /  v3.0 8.1 (High)  ·  Red Hat: Critical'],
  ['Du lieu doi phuong', 'Phan hoi DNS tao rieng (DNS doc hai / MITM)'],
  ['Khac phuc', 'Va glibc >= 2.23; workaround han che; tat IPv6 vo dung'],
];
s.addTable(rows.map((r, i) => [
  { text: r[0], options: { bold: true, color: 'FFFFFF', fill: { color: STEEL }, fontSize: 13, align: 'left', valign: 'middle', margin: 6 } },
  { text: r[1], options: { color: INK, fill: { color: i % 2 ? 'F4F6F9' : 'FFFFFF' }, fontSize: 13, align: 'left', valign: 'middle', margin: 6 } },
]), { x: 0.6, y: 1.7, w: 12.1, colW: [2.9, 9.2], rowH: 0.62, border: { type: 'solid', color: 'DDE3EA', pt: 1 }, fontFace: BODY });
tb(s, 'Chi nghien cuu & trinh bay — khong tai hien khai thac.', { x: 0.6, y: 6.7, w: 12, h: 0.4, fontSize: 13, italic: true, color: RED });
s.addNotes('Nhan: NVD gan 119, ban chat ky thuat la 121 — khong tu sua nhan NVD.');

// ============ SLIDE 11 - Muc 6: CVE co che ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 6 — CVE');
title(s, 'CVE-2015-7547 — co che & khac phuc');
bullets(s, [
  'getaddrinfo() truy van song song A (IPv4) + AAAA (IPv6)',
  'Buffer 2048 byte cap bang alloca() tren stack',
  { text: 'Loi: sai dong bo con tro/kich thuoc o phan hoi thu hai -> ghi toi ~63 KB du lieu doi phuong', options: { color: RED } },
  'Du lieu doi phuong: phan hoi DNS tao rieng (DNS doc hai / ke chen giua)',
  { text: 'Khac phuc: va glibc >= 2.23; workaround (gioi han TCP <=1023B) han che; TAT IPv6 vo dung', options: { color: GREEN } },
], { x: 0.6, y: 1.7, w: 8.2, fontSize: 15.5 });
s.addShape(p.ShapeType.roundRect, { x: 9.1, y: 1.9, w: 3.7, h: 4.3, rectRadius: 0.08, fill: { color: 'FBEAEC' }, line: { color: 'F3C6CB', width: 1 } });
tb(s, 'So voi ret2win', { x: 9.35, y: 2.1, w: 3.3, h: 0.4, fontSize: 13, bold: true, color: RED });
tb(s, 'Giong: deu ghi VUOT buffer tren stack.\n\nKhac:\n· Nguon du lieu = mang (DNS), khong phai argv\n· Loi o quan ly con tro/kich thuoc, khong phai strcpy don gian', { x: 9.35, y: 2.55, w: 3.3, h: 3.5, fontSize: 13, color: INK });
s.addNotes('Lien he ro voi phan demo de nguoi nghe thay cung mot ban chat CWE-121.');

// ============ SLIDE 12 - Muc 8: Khac phuc & bao ve ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 8 — Khac phuc');
title(s, 'Khac phuc & phong ngua');
bullets(s, [
  { text: 'Goc re: gioi han ghi theo kich thuoc dich', options: { bold: true } },
  'snprintf / fgets / kiem tra do dai (xem bai tap 3 doan ma)',
  'Kiem thu: AddressSanitizer, fuzzing, SAST',
  'Cac lop bao ve giam kha nang khai thac, KHONG xoa loi',
], { x: 0.6, y: 1.7, w: 5.3, fontSize: 15 });
const prot = [
  ['Co che', 'Tac dung', 'ret2win'],
  ['Stack canary', 'Phat hien ghi tran toi return', 'Tat'],
  ['NX', 'Stack khong thuc thi', 'Bat'],
  ['ASLR / PIE', 'Ngau nhien hoa dia chi', 'PIE tat'],
];
s.addTable(prot.map((r, i) => r.map((c, j) => ({
  text: c,
  options: {
    bold: i === 0, color: i === 0 ? 'FFFFFF' : INK,
    fill: { color: i === 0 ? STEEL : (i % 2 ? 'F4F6F9' : 'FFFFFF') },
    fontSize: 13, align: j === 2 ? 'center' : 'left', valign: 'middle', margin: 6,
  },
}))), { x: 6.2, y: 1.9, w: 6.6, colW: [2.2, 3.0, 1.4], rowH: 0.7, border: { type: 'solid', color: 'DDE3EA', pt: 1 }, fontFace: BODY });
tb(s, 'Sua tan goc = gioi han ghi theo kich thuoc dich.', { x: 6.2, y: 5.0, w: 6.6, h: 0.5, fontSize: 13, italic: true, color: GREEN });
s.addNotes('Doi chieu ma loi vs ma sua trong notes/bai_tap_3_doan_ma.');

// ============ SLIDE 13 - Muc 9: Dieu kien & gioi han ============
s = p.addSlide(); s.background = { color: BG_LIGHT };
tag(s, 'Muc 9 — Dieu kien & gioi han');
title(s, 'Dieu kien & gioi han (noi dung da/chua xac nhan)');
const lim = [
  ['Hang muc', 'Trang thai'],
  ['Input toi sink', 'Da xac nhan (demo)'],
  ['Offset do tren binary', 'Da xac nhan = 40 (buffer 32 + rbp 8)'],
  ['Dieu khien dia chi tra ve', 'Da xac nhan (anh 04: "Well done" roi SIGSEGV)'],
  ['Dat muc tieu (in flag)', 'Da xac nhan (anh 05: exit 0, ra flag)'],
  ['ASLR luc chay', 'Quan sat duoi EMULATION — khong dai dien may that'],
  ['CVE: tu tai hien khai thac', 'KHONG lam (chi nghien cuu)'],
];
s.addTable(lim.map((r, i) => r.map((c, j) => ({
  text: c,
  options: {
    bold: i === 0, color: i === 0 ? 'FFFFFF' : INK,
    fill: { color: i === 0 ? STEEL : (i % 2 ? 'F4F6F9' : 'FFFFFF') },
    fontSize: 14, align: 'left', valign: 'middle', margin: 6,
  },
}))), { x: 0.6, y: 1.8, w: 12.1, colW: [4.3, 7.8], rowH: 0.62, border: { type: 'solid', color: 'DDE3EA', pt: 1 }, fontFace: BODY });
s.addNotes('Thanh that ve dieu chua kiem chung (ASLR duoi emulation).');

// ============ SLIDE 14 - Muc 10: Ket luan (dark) ============
s = p.addSlide(); darkBg(s);
tb(s, 'Muc 10 — Ket luan', { x: 0.9, y: 0.6, w: 6, h: 0.5, fontSize: 13, bold: true, color: RED });
tb(s, 'Ket luan', { x: 0.9, y: 1.1, w: 11, h: 1.0, fontFace: HEAD, fontSize: 40, bold: true, color: 'FFFFFF' });
s.addText([
  { text: 'Tran stack: ghi vuot buffer -> de dia chi tra ve -> doi luong thuc thi', options: { bullet: { indent: 18 }, breakLine: true, color: 'E6EDF3' } },
  { text: 'Da chung minh tren ret2win (dat muc tieu); CVE-2015-7547 cho thay tac dong that quy mo lon', options: { bullet: { indent: 18 }, breakLine: true, color: 'E6EDF3' } },
  { text: 'Phong ngua: gioi han ghi + cac lop bao ve (canary/NX/ASLR/PIE)', options: { bullet: { indent: 18 }, breakLine: false, color: 'E6EDF3' } },
], { isTextBox: true, margin: 0, x: 0.9, y: 2.4, w: 11.4, h: 2.4, fontFace: BODY, fontSize: 18, paraSpaceAfter: 14, lineSpacingMultiple: 1.05 });
tb(s, 'Tai lieu: MITRE CWE-121/787/119 · ROP Emporium ret2win · NVD / Red Hat / Google (CVE-2015-7547) · GCC stack protector · Clang ASan', { x: 0.9, y: 5.4, w: 11.4, h: 1.1, fontSize: 13, color: 'AAB4C4' });
tb(s, 'Moi nguon/URL tren slide can duoc tra lai truoc khi trinh bay.', { x: 0.9, y: 6.5, w: 11.4, h: 0.4, fontSize: 12, italic: true, color: '7E8A9C' });
s.addNotes('3 y ket luan ngan, khong phong dai. Ghi nguon da tra lai.');

p.writeFile({ fileName: path.join(__dirname, 'S01_seminar.pptx') }).then(f => console.log('OK ->', f));
