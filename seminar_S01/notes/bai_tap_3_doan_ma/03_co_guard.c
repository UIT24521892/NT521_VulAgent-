/*
 * 03_co_guard.c - Doan ma TRONG NGUY HIEM nhung da co GUARD chan duoc
 *
 * Van dung strcpy (ham nguy hiem), nhung co kiem tra do dai TRUOC khi copy.
 * Diem hoc: guard phai chan MOI duong toi sink, va phai tinh ca byte '\0'.
 *
 * Bien dich:
 *   gcc -g -o 03_co_guard 03_co_guard.c
 */
#include <stdio.h>
#include <string.h>

void handle(const char *input) {
    char buf[64];
    /* GUARD: strlen(input) < 64 => toi da 63 ky tu + 1 byte '\0' = 64 byte,
     * vua khit buffer. Dung dau "<" (khong phai "<="): day la cho de sai.
     * Neu doi thanh "<=" se cho phep 64 ky tu + '\0' = 65 byte -> tran 1 byte
     * (off-by-one). Guard sai mot ky tu la loi quay lai. */
    if (strlen(input) < sizeof(buf)) {
        strcpy(buf, input);       /* an toan VI da kiem tra o tren */
        printf("Da nhan: %s\n", buf);
    } else {
        printf("Input qua dai, tu choi.\n");
    }
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Dung: %s <chuoi>\n", argv[0]);
        return 1;
    }
    handle(argv[1]);
    return 0;
}
