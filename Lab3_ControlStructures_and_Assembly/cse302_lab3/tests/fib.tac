.L0:
  %2 = const 0;
  %3 = copy %2;
  %4 = const 1;
  %5 = copy %4;
  %6 = const 0;
  %7 = copy %6;
.L8:
  %12 = const 20;
  %13 = sub %7, %12;
  jl %13, .L14;
  %13 = const 0;
  jmp .L15;
.L14:
  %13 = const 1;
.L15:
  jz %13, .L11;
  %16 = const 2;
  %17 = mod %7, %16;
  %18 = const 0;
  %19 = sub %17, %18;
  jz %19, .L20;
  %19 = const 0;
  jmp .L21;
.L20:
  %19 = const 1;
.L21:
  jnz %19, .L22;
  %24 = neg %3;
  print %24;
  jmp .L23;
.L22:
  print %3;
.L23:
  %25 = add %3, %5;
  %26 = copy %25;
  %3 = copy %5;
  %5 = copy %26;
  %27 = const 1;
  %28 = add %7, %27;
  %7 = copy %28;
.L10:
  jmp .L8;
.L11:

