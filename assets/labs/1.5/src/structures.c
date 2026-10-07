/*
 * Lab 1.5 - Recognizing control structures in assembly
 *
 * This file deliberately packs in everything: a loop, nested if/else, a
 * multi-way switch, array access and struct access. Build it, open it in
 * Ghidra/IDA, and point out each construct yourself before checking the solution.
 *
 * Build (easy to read, close to the templates):
 *   gcc -O0 -g -o structures_O0 structures.c
 * Build (optimized, harder to read, for comparison):
 *   gcc -O2 -o structures_O2 structures.c
 *
 * On Windows (MSVC):
 *   cl /Od structures.c      (equivalent to -O0)
 *   cl /O2 structures.c
 */

#include <stdio.h>

/* ----- struct for practicing reading [base + offset] ----- */
struct Player {
    int   id;        /* offset 0  */
    int   score;     /* offset 4  */
    int   level;     /* offset 8  */
    char  grade;     /* offset 12 */
};

/* 1) LOOP: sum an array. In asm you will see a backward jump,
 *    and array access of the form [base + index*4] because the elements are int. */
int sum_array(int *arr, int n) {
    int total = 0;
    for (int i = 0; i < n; i++) {
        total += arr[i];        /* int array -> scale *4 */
    }
    return total;
}

/* 2) NESTED IF/ELSE: grade a score. Several cmp + jumps, with a jmp at the end of each body. */
char classify(int score) {
    if (score >= 90) {
        return 'A';
    } else {
        if (score >= 70) {
            return 'B';
        } else if (score >= 50) {
            return 'C';
        } else {
            return 'F';
        }
    }
}

/* 3) SWITCH with consecutive values 0..4 -> the compiler usually builds a
 *    jump table. See whether Ghidra/IDA recognizes the table. */
const char *action_name(int action) {
    switch (action) {
        case 0: return "idle";
        case 1: return "walk";
        case 2: return "run";
        case 3: return "jump";
        case 4: return "attack";
        default: return "unknown";
    }
}

/* 4) STRUCT: read/write fields through fixed offsets. */
void level_up(struct Player *p) {
    p->level += 1;              /* [p + 8] */
    p->score += 100;           /* [p + 4] */
    if (p->score >= 500) {     /* [p + 4] */
        p->grade = 'S';        /* [p + 12] */
    }
}

int main(void) {
    int data[5] = {10, 20, 30, 40, 50};
    int s = sum_array(data, 5);
    printf("sum = %d\n", s);
    printf("grade = %c\n", classify(s / 5));

    struct Player p = {1, 420, 3, 'B'};
    level_up(&p);
    printf("player %d: level %d score %d grade %c\n",
           p.id, p.level, p.score, p.grade);

    for (int a = 0; a < 6; a++) {
        printf("action %d = %s\n", a, action_name(a));
    }
    return 0;
}
