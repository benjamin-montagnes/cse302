	.globl main
	.text
main:
	pushq %rbp
	subq $0x40, %rsp
	movq -0x8(%rbp), %rax
	movq %rax, -0x10(%rbp)
	movq -0x18(%rbp), %rax
	movq %rax, -0x20(%rbp)
	movq -0x10(%rbp), %rax
	addq -0x20(%rbp), %rax
	movq %rax, -0x28(%rbp)
	movq -0x28(%rbp), %rax
	movq %rax, -0x30(%rbp)
	movq -0x30(%rbp), %rdi
	callq print
	movq -0x38(%rbp), %rax
	movq %rax, -0x40(%rbp)
	movq -0x40(%rbp), %rax
	movq %rax, -0x30(%rbp)
	movq -0x30(%rbp), %rdi
	callq print
	movq %rbp, %rsp
	popq %rbp
	xorq %rax, %rax
	retq
