del fucubelib.pyf fucubelib.pyd
python c:/python27/Scripts/f2py.py -m fucubelib -h fucubelib.pyf fucubelib.f90
python c:/python27/Scripts/f2py.py -c fucubelib.pyf fucubelib.f90 --fcompiler=gnu95 --compiler=mingw32
pause
