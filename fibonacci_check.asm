; ================================================
; Sample Assembly Program: Fibonacci Check
; Checks if AX (=8) is a Fibonacci number
; ================================================

FSTART:
    MOV AX, 8        ; The number to check
    MOV BX, 0        ; prev  = 0
    MOV CX, 1        ; curr  = 1

FIBLOOP:
    CMP BX, AX       ; Is prev == AX?
    JZ FOUND         ; If yes, it's Fibonacci!
    CMP BX, AX       ; Is prev > AX?  (re-use CMP)
    JG NOTFOUND      ; If greater, not Fibonacci

    ; Compute next Fibonacci number
    ADD BX, CX       ; BX = BX + CX  (next = prev + curr)
    JMP FIBLOOP      ; Repeat

FOUND:
    MOV DX, 1        ; DX = 1 means "found"
    HLT

NOTFOUND:
    MOV DX, 0        ; DX = 0 means "not found"
    HLT
