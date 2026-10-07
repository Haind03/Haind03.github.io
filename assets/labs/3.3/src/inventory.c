/*
 * Lab 3.3 - Recovering a struct
 *
 * Build (Linux, unoptimized so it stays readable):
 *     gcc -O0 -g -o inventory inventory.c
 * Build (Windows, MSVC x64 Developer Command Prompt):
 *     cl /Od /Zi inventory.c
 * Build (Windows, MinGW):
 *     gcc -O0 -g -o inventory.exe inventory.c
 *
 * Task: open the built file in IDA or Ghidra, read the pseudocode of
 * update_player and print_player BEFORE assigning the struct, then rebuild
 * struct Player and compare. Watch the padding between the fields.
 */
#include <stdio.h>
#include <string.h>

struct Player {
    int   id;        /* offset 0  */
    char  rank;      /* offset 4  (1 byte, then padding) */
    int   score;     /* offset 8  (int needs 4-byte alignment -> 3 bytes of padding after rank) */
    char  name[16];  /* offset 12 */
    double balance;  /* offset ... (double needs 8-byte alignment -> padding before it) */
    int   level;     /* last offset */
};

/* This function only reads/writes fields at fixed offsets -> the signature of a struct */
void update_player(struct Player *p, int gained) {
    p->score += gained;
    if (p->score > 100 && p->name[0] != '\0') {
        p->level++;
        p->rank = 'A';
    }
    p->balance = p->balance + gained * 1.5;
}

void print_player(struct Player *p) {
    printf("id=%d rank=%c score=%d name=%s balance=%.2f level=%d\n",
           p->id, p->rank, p->score, p->name, p->balance, p->level);
}

int main(void) {
    struct Player p;
    memset(&p, 0, sizeof(p));
    p.id = 7;
    p.rank = 'C';
    p.score = 95;
    strcpy(p.name, "neo");
    p.balance = 50.0;
    p.level = 1;

    printf("sizeof(struct Player) = %zu\n", sizeof(struct Player));
    update_player(&p, 20);
    print_player(&p);
    return 0;
}
