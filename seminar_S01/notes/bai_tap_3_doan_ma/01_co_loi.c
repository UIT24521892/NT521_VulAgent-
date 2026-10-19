/*
 * 01_co_loi.c - Doan ma CO LOI tran bo dem tren stack (CWE-121)
 *
 * Bien dich de thu nghiem (trong VM, KHONG bat bao ve de thay ro loi):
 *   gcc -fno-stack-protector -z execstack -no-pie -g -o 01_co_loi 01_co_loi.c
 * Chay:
 *   ./01_co_loi AAAA            # input ngan -> binh thuong
 *   ./01_co_loi $(python3 -c 'print("A"*200)')   # input dai -> co the crash
 *
 * Luu y: chi chay trong moi truong duoc phep, co lap (VM Kali).
 */
#include <stdio.h>
#include <string.h>

void handle(const char *input) {
    char buf[64];                 /* vung dem dich: 64 byte tren stack */
    strcpy(buf, input);           /* SINK: strcpy khong gioi han theo sizeof(buf) */
    printf("Da nhan: %s\n", buf);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Dung: %s <chuoi>\n", argv[0]);
        return 1;
    }
    handle(argv[1]);              /* SOURCE: argv[1] do nguoi dung kiem soat */
    return 0;
}
