$pdf_mode = 5;
$xelatex = 'xelatex -interaction=nonstopmode -halt-on-error %O %S';
$max_repeat = 5;

$ENV{TFMFONTS} = "./fonts/math//:" . ($ENV{TFMFONTS} // "");
