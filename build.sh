#!/bin/bash

_include_paths=(assets)

system='linux'
if [ "$1" == "--windows" ]; then
    system='windows'
fi

if [ "$system" == "linux" ]; then
    _python='python'
    _pyinstaller='/home/l31rb4g/PyInstaller-2.1/pyinstaller.py'
    _build_path='BUILD/linux'
elif [ "$system" == 'windows' ]; then
    _python='C:/Python27/python.exe'
    _pyinstaller='C:/PyInstaller-2.1/pyinstaller.py'
    _build_path='BUILD/windows'
fi


echo '=================================='
echo ' Building Davi for '$system
echo '=================================='
echo -e '\n'


echo -e '\n>>> Cleaning build directory'
rm -rf $_build_path
mkdir -p $_build_path
echo -e '> OK'


echo -e '\n>>> Collecting trees'
trees=''
for p in ${_include_paths[@]}; do
    trees=$trees"Tree('"$p"', prefix='"$p"'), "
done
echo $trees
echo -e '> OK'


echo -e '\n>>> Building spec file...'
$_python $_pyinstaller davi.py \
    --onefile \
    --specpath="$_build_path" \
    --distpath="$_build_path/dist" \
    --workpath="$_build_path/build"
echo -e '> OK'


echo -e '\n>>> Appending trees to spec file'
trees=$(echo $trees | sed "s/\//\\\\\//g")
exp='s/exe = EXE(pyz,/exe = EXE(pyz, '$trees'/'
sed -i "$exp" $_build_path/davi.spec
echo -e '> OK'


echo -e '\n=== Spec file ==='
cat $_build_path'/davi.spec'
echo '==='


echo -e '\n>>> Building app...'
$_python $_pyinstaller $_build_path/davi.spec \
    --specpath="$_build_path" \
    --distpath="$_build_path/dist" \
    --workpath="$_build_path/build"
echo -e '> OK'


echo -e '\n\n'
echo '+-----------------------------+'
echo '| Build finished!             |'
echo '+-----------------------------+'
echo -e '\n\n'