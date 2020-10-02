	.globl main
	.text
main:
	pushq %rbp
	subq $56, %rsp
	
	movq $0, -8(%rbp)
	
	movq -8(%rbp), %r11
	movq %r11, %rcx
	movq %rcx, -16(%rbp)
	
	movq $1, -24(%rbp)
	movq -24(%rbp), %rax
	movq %rax, %rcx
	movq %rcx, -32(%rbp)
	movq $0, -40(%rbp)
	movq -40(%rbp), %rax
	movq %rax, %rcx
	movq %rcx, -48(%rbp)
.L8:
	movq $20, -56(%rbp)
	movq -56(%rbp), %rcx
	movq -48(%rbp), %rax
	subq %rax, %rcx
	movq %rcx, -64(%rbp)
	cmpq $0, -64(%rbp)
	jl .L14
	movq $0, -64(%rbp)
	jmp .L15
.L14:
	movq $1, -64(%rbp)
.L15:
	cmpq $0, -64(%rbp)
	jz .L11
	movq $2, -72(%rbp)
	xor %rdx, %rdx
	movq -48(%rbp), %rax
	idivq -72(%rbp)
	movq %rdx, -80(%rbp)
	movq $0, -88(%rbp)
	movq -88(%rbp), %rcx
	movq -80(%rbp), %rax
	subq %rax, %rcx
	movq %rcx, -96(%rbp)
	cmpq $0, -96(%rbp)
	jz .L20
	movq $0, -96(%rbp)
	jmp .L21
.L20:
	movq $1, -96(%rbp)
.L21:
	cmpq $0, -96(%rbp)
	jnz .L22
	movq -112(%rbp), %rax
	negq %rax
	movq %rcx, -104(%rbp)
	pushq %rdi
	movq -104(%rbp), %rdi
	callq _bx_print_int
	popq %rdi
	jmp .L23
.L22:
	pushq %rdi
	movq -16(%rbp), %rdi
	callq _bx_print_int
	popq %rdi
.L23:
	movq -32(%rbp), %rcx
	movq -16(%rbp), %rax
	addq %rax, %rcx
	movq %rcx, -120(%rbp)
	movq -120(%rbp), %rax
	movq %rax, %rcx
	movq %rcx, -128(%rbp)
	movq -32(%rbp), %rax
	movq %rax, %rcx
	movq %rcx, -16(%rbp)
	movq -128(%rbp), %rax
	movq %rax, %rcx
	movq %rcx, -32(%rbp)
	movq $1, -136(%rbp)
	movq -136(%rbp), %rcx
	movq -48(%rbp), %rax
	addq %rax, %rcx
	movq %rcx, -144(%rbp)
	movq -144(%rbp), %rax
	movq %rax, %rcx
	movq %rcx, -48(%rbp)
.L10:
	jmp .L8
.L11:
	movq %rbp, %rsp
	popq %rbp
	movq $0, %rax
	retq