	.globl main
	.text
main:
	pushq %rbp
	subq $0x40, %rsp
	movq 0x1(%rbp), %rax
	movq %rax, 0x0(%rbp)
	movq -0x1(%rbp), %rax
	movq %rax, -0x2(%rbp)
	movq 0x0(%rbp), %rax
	addq -0x2(%rbp), %rax
	movq %rax, -0x3(%rbp)
	movq -0x3(%rbp), %rax
	movq %rax, -0x4(%rbp)
	movq -0x4(%rbp), %rdi
	callq _bx_print_int
	movq -0x5(%rbp), %rax
	movq %rax, -0x6(%rbp)
	movq -0x6(%rbp), %rax
	movq %rax, -0x4(%rbp)
	movq -0x4(%rbp), %rdi
	callq _bx_print_int
	movq %rbp, %rsp
	popq %rbp
	movq $0x0, %rax
	retq
