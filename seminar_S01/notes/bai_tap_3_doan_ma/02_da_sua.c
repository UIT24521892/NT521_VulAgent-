/*
 * 02_da_sua.c - Ban SUA cua 01_co_loi.c
 *
 * Y tuong sua: gioi han luong ghi theo kich thuoc vung dem dich,
 * va luon bao dam co ky tu ket thuc chuoi '\0'.
 *
 * Bien dich:
 *   gcc -g -o 02_da_sua 02_da_sua.c
 * Chay:
 *   ./02_da_sua $(python3 -c 'print("A"*200)')   # bi cat ngan, KHONG tran
 */
#include <stdio.h>
#include <string.h>

void handle(const char *input) {
    char buf[64];
    /* snprintf gioi han ghi toi da sizeof(buf)-1 ky tu + 1 byte '\0'.
     * Input dai hon se bi CAT NGAN (mat du lieu) nhung KHONG tran bo dem. */
    snprintf(buf, sizeof(buf), "%s", input);
    printf("Da nhan: %s\n", buf);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Dung: %s <chuoi>\n", argv[0]);
        return 1;
    }
    handle(argv[1]);
    return 0;
}
