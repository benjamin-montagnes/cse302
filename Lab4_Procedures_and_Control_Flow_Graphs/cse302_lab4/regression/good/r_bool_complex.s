	.globl main
	.text
main:
	pushq %rbp
	movq %rsp, %rbp
	subq $0x8, %rsp
	movq %rbp, %rsp
	popq %rbp
	xorq %rax, %rax
	retq
