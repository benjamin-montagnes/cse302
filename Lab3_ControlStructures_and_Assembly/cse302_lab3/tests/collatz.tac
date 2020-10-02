  %2 = const 837799;
  %3 = copy %2;
  %4 = const 0;
  %5 = copy %4;
.L6:
  %10 = const 1;
  jz %10, .L9;
  print %3;
  %11 = const 1;
  %12 = add %5, %11;
  %5 = copy %12;
  %13 = const 1;
  %14 = sub %3, %13;
  jz %14, .L15;
  %14 = const 0;
  jmp .L16;
.L15:
  %14 = const 1;
.L16:
  jnz %14, .L17;
  jmp .L18;
.L17:
  jmp .L9;
.L18:
  %19 = const 2;
  %20 = mod %3, %19;
  %21 = const 0;
  %22 = sub %20, %21;
  jz %22, .L23;
  %22 = const 0;
  jmp .L24;
.L23:
  %22 = const 1;
.L24:
  jnz %22, .L25;
  %27 = const 3;
  %28 = mul %27, %3;
  %29 = const 1;
  %30 = add %28, %29;
  %3 = copy %30;
  jmp .L8;
.L25:
  %31 = const 1;
  %32 = shr %3, %31;
  %3 = copy %32;
.L8:
  jmp .L6;
.L9:
  print %5;
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  