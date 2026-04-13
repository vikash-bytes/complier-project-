START:
    MOV AX, 5
    CMP AX, 10
    JZ EQUAL
    ADD AX, 1
    JMP START
EQUAL:
    SUB AX, 1
    HLT