# Bộ lệnh GDB để "THẤY" từng bước ret2libc trên `split` (x86_64)
# Dùng: gdb -q ./split -x gdb_demo.gdb
# Mục đích: cho người xem quan sát CHIẾM LUỒNG và GỌI HÀM ĐÚNG ĐỐI SỐ, không chỉ
# tin vào việc "ra flag". Khuyến nghị dùng kèm pwndbg/gef cho dễ đọc.
#
# Gợi ý trình bày: tắt ASLR trong phiên GDB để địa chỉ ổn định khi giảng, và NÓI RÕ
# đây là giả định của lab, không phải khả năng tự rò rỉ địa chỉ của exploit.
set disable-randomization on

# --- Mốc A: hàm đọc input (sink). Đổi tên hàm cho đúng binary (pwnme/read...). ---
# Vì sao: cho thấy nơi input tràn vào buffer. [SỬA tên hàm nếu khác]
break pwnme
commands
  echo \n===== MỐC A: vào hàm đọc input (sink) =====\n
  echo RSP (đỉnh stack hiện tại):\n
  print/x $rsp
  echo >> Tiếp tục để gửi payload, rồi dừng tại ret của hàm này.\n
  continue
end

# --- Mốc B: ngay trước khi RET của hàm đọc input ---------------------------------
# Vì sao: đây là lúc CPU sắp lấy saved RIP làm địa chỉ chạy tiếp. Ta xem giá trị đó
# đã bị payload ghi đè thành gadget của ta chưa => bằng chứng "chiếm luồng".
# [SỬA địa chỉ: đặt break tại lệnh `ret` của hàm đọc input, xem objdump]
# break *0x[ĐO địa chỉ ret]
# commands
#   echo \n===== MỐC B: sắp RET — saved RIP trên đỉnh stack =====\n
#   x/gx $rsp
#   echo >> Nếu giá trị này = địa chỉ gadget pop rdi;ret của ta => đã chiếm luồng.\n
#   continue
# end

# --- Mốc C: tại system@plt — kiểm tra đối số RDI --------------------------------
# Vì sao: mấu chốt ret2libc trên x86_64. Đối số 1 phải ở RDI. Ta kiểm tra RDI có
# trỏ đúng chuỗi lệnh không => bằng chứng "gọi hàm thư viện với đối số đúng".
break system
commands
  echo \n===== MỐC C: vào system() =====\n
  echo RDI (đối số 1 — phải là con trỏ tới chuỗi lệnh):\n
  print/x $rdi
  echo Nội dung chuỗi tại RDI:\n
  x/s $rdi
  echo RSP (kiểm căn lề 16-byte — vì movaps trong prologue):\n
  print/x $rsp
  echo >> Nếu x/s $rdi in ra "/bin/cat flag.txt" => đối số đúng. Tiếp tục để lấy flag.\n
  continue
end

echo \n[gdb_demo] Đã nạp breakpoint A và C. Chạy: run < <(python3 -c "...payload...")\n
echo [gdb_demo] Hoặc dùng pwntools gdb.attach trong exploit.py để tự đặt payload.\n
