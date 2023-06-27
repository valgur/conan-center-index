#include <pbc/pbc.h>

#include <stdio.h>
#include <stdlib.h>

#define TYPE_A                                                                                     \
    "type a\n"                                                                                     \
    "q "                                                                                           \
    "87807107996633125224377819847540498158068831994142082110286533992664756308802229570786251794" \
    "22662221423155858769582317459277713367317481324925129998224791\n"                             \
    "h "                                                                                           \
    "12016012264891146079388821366740534204802954401251311822919615131047207289359704531102844802" \
    "183906537786776\n"                                                                            \
    "r 730750818665451621361119245571504901405976559617\n"                                         \
    "exp2 159\n"                                                                                   \
    "exp1 107\n"                                                                                   \
    "sign1 1\n"                                                                                    \
    "sign0 1\n"

int main(void) {
    pairing_t pairing;
    pairing_init_set_buf(pairing, TYPE_A, sizeof(TYPE_A));

    element_t g, g2, h, h2, a, gt1, gt2;
    element_init_G1(g, pairing);
    element_init_G1(g2, pairing);
    element_init_G2(h, pairing);
    element_init_G2(h2, pairing);
    element_init_Zr(a, pairing);
    element_init_GT(gt1, pairing);
    element_init_GT(gt2, pairing);

    element_from_hash(g, "FEDCBA9876", 10);
    element_from_hash(h, "0123456789", 10);
    element_pow_zn(g2, g, a);
    element_pow_zn(h2, h, a);
    pairing_apply(gt1, g, h2, pairing);
    pairing_apply(gt2, g2, h, pairing);

    return element_cmp(gt1, gt2);
}
