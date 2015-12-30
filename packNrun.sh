#!/bin/bash

cp content.xml styles.xml ./ODT_Contents_Rozvrh/

cd ./ODT_Contents_Rozvrh/

zip -r output.odt *

mv output.odt ../

cd ..

libreoffice output.odt
