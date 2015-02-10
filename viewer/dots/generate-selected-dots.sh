#!/bin/bash

#color='#111111'
#color='#26264A'
color='#d34f4f'
stroke_color=$color
text_color='#ffffff'
font=Helvetica-Bold

convert -size 9x9 xc:none -fill $color -draw 'circle 4,4 7,7' dots/1.png

for x in $(seq 2 9); do
  convert -size 13x13 xc:none -fill $color -stroke $stroke_color -draw 'circle 6,6 10,10' -stroke none -fill $text_color -pointsize 10 -font $font -gravity center -draw "text 1,1 '$x'" ../static/images/$x.png
done

for x in $(seq 10 19); do
  convert -size 25x25 xc:none -fill $color -stroke $stroke_color -draw 'circle 12,12 20,20' -stroke none -fill $text_color -pointsize 14 -font $font -gravity center -draw "text 0,1 '$x'" ../static/images/$x.png
done

for x in $(seq 20 99); do
  convert -size 25x25 xc:none -fill $color -stroke $stroke_color -draw 'circle 12,12 20,20' -stroke none -fill $text_color -pointsize 14 -font $font -gravity center -draw "text 1,2 '$x'" ../static/images/$x.png
done

convert -size 39x39 xc:none -fill $color -stroke $stroke_color -draw 'circle 19,19 32,32' -stroke none -fill $text_color -pointsize 16 -font $font -gravity center -draw "text 1,1 '100+'" ../static/images/100.png

montage $(ls dots/?.png dots/??.png dots/???.png | sort -t/ -k2 -n | xargs) -background transparent -gravity NorthWest -geometry '39x39>+0+0' -tile 10x ../static/images/selected-2013-01-14.png

rm dots/?.png dots/??.png dots/???.png
