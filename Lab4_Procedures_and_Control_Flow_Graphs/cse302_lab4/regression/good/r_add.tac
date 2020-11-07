proc @main([]): 
  %3 = copy %0;
  %4 = copy %1;
  %2 = add %3, %4;
  param 1, %2;
  %_ = call @print, 1;
  %6 = copy %5;
  param 1, %6;
  %_ = call @print, 1;
