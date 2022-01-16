#!/usr/bin/python

import sys, os, shutil
import glob
import pycdlib
import hashlib
import subprocess
import tempfile

import mhef.psp
from io import BytesIO

isofile = sys.argv[1]

UMD_MD5HASH = "1f76ee9ccbd6d39158f06e6e5354a5bd"
PSN_MD5HASH = "cc39d070b2d2c44c9ac8187e00b75dc4"

databin = tempfile.gettempdir()+"/DATA.BIN"
databin_dec = tempfile.gettempdir()+"/DATA.BIN.DEC"

base_patches = ["align.xdelta",
                "compat.xdelta",
                "FUComplete_EN.xdelta",
                "FUComplete_JP.xdelta"]

def pause_exit():
    os.system("pause")
    sys.exit()

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_iso_hash(isofile):
    with open(isofile, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()

def extract_data_bin(isofile):
    iso = pycdlib.PyCdlib()
    iso.open(isofile)

    data_bin = BytesIO()
    iso.get_file_from_iso_fp(data_bin, iso_path='/PSP_GAME/USRDIR/DATA.BIN')

    iso.close()

    with open(databin, "wb") as f:
        f.write(data_bin.getbuffer())

def decrypt_data_bin(data_bin):
    dc = mhef.psp.DataCipher(mhef.psp.MHP2G_JP)
    dc.decrypt_file(data_bin, databin_dec)
    
def replace_data_bin(isofile, data_bin_dec):
    umdr = resource_path("bin/UMD-replace.exe")
    data_bin_path = "/PSP_GAME/USRDIR/DATA.BIN"
    subprocess.run([umdr, isofile, data_bin_path, data_bin_dec], shell=True, check=True)
    
def install_patches(isofile):
    xdel = resource_path("bin/xdelta3.exe")
    exe_path = os.path.dirname(sys.executable)
    lang = ""
    
    while not lang.lower() in ["en", "jp"]:
        lang = input(f"Select language (en/jp): ")

    if lang.lower() == "en":
        patch1 = exe_path+"/patches/base/FUComplete_EN.xdelta"
    if lang.lower() == "jp":
        patch1 = exe_path+"/patches/base/FUComplete_JP.xdelta"
    
    nisofile = tempfile.gettempdir()+"/"+os.path.basename(isofile)[:-4]+"_FUC.iso"
    nisofile = nisofile.replace("_backup", "")
    subprocess.run([xdel, "-d", "-s", isofile, patch1, nisofile], shell=True, check=True)
        
    patches = sorted(glob.glob(exe_path+"/patches/optional/*.xdelta"))
    for i, p in enumerate(patches):
        name = os.path.basename(p)
        q = input(f"Install {name}? (y/n): ")
        
        if q in ["y", "Y"]:
            nisofile2 = f"{nisofile[:-4]}_{i}.iso"
            subprocess.run([xdel, "-d", "-n", "-s", nisofile, p, nisofile2], shell=True, check=True)
            os.remove(nisofile)
            nisofile = nisofile2
            
    shutil.move(nisofile, f"{isofile[:-4]}_FUC.iso")
    
def install_compat_patch(isofile):
    xdel = resource_path("bin/xdelta3.exe")
    exe_path = os.path.dirname(sys.executable)
    patch1 = exe_path+"/patches/base/compat.xdelta"
    
    nisofile = tempfile.gettempdir()+"/"+os.path.basename(isofile)[:-4]+"_compat.iso"
    nisofile = nisofile.replace("_backup", "")
    subprocess.run([xdel, "-d", "-s", isofile, patch1, nisofile], shell=True, check=True)

    os.remove(isofile)
    shutil.move(nisofile, isofile)
    
def install_data_patch(databin_dec):
    xdel = resource_path("bin/xdelta3.exe")
    exe_path = os.path.dirname(sys.executable)
    patch1 = exe_path+"/patches/base/align.xdelta"
    
    ndatabin = tempfile.gettempdir()+"/"+os.path.basename(databin_dec)[:-4]+"_patched.BIN"
    ndatabin = ndatabin.replace("_backup", "")
    subprocess.run([xdel, "-d", "-s", databin_dec, patch1, ndatabin], shell=True, check=True)

    os.remove(databin_dec)
    shutil.move(ndatabin, databin_dec)
    
def check_patches():
    exe_path = os.path.dirname(sys.executable)
    base = []
    
    for f in base_patches:
        fpath = exe_path+"/patches/base/"+f
        base.append(os.path.isfile(fpath))
    
    optional = len(glob.glob(exe_path+"/patches/optional/*.xdelta"))
    
    return (all(base), optional)

print(f"*****FUComplete Patcher*****\n")

if not os.path.isfile(isofile):
    print("ISO file not found.")
    pause_exit()

elif check_patches() == (False, True):
    print("ERROR: Missing one or more of the base patches.")
    pause_exit()
elif check_patches() == (False, False):
    print("ERROR: Base and optional patches not found.")
    pause_exit()
elif check_patches() == (True, False):
    print("WARNING: optional patches not found.")

print("Checking ISO...")
isohash = get_iso_hash(isofile)
if isohash in [UMD_MD5HASH, PSN_MD5HASH]:
    print("Backing up ISO...")
    isofile_bak = f"{isofile[:-4]}_backup.iso"
    shutil.copy2(isofile, isofile_bak)
    
    if isohash == UMD_MD5HASH:
        print("UMD ISO found, converting...")
        install_compat_patch(isofile)
    
    print("Extracting DATA.BIN...")
    extract_data_bin(isofile)
    
    print("Decrypting DATA.BIN (this may take a few minutes)...")
    decrypt_data_bin(databin)
    
    print("Patching DATA.BIN...")
    install_data_patch(databin_dec)
    
    print("Replacing DATA.BIN...")
    replace_data_bin(isofile, databin_dec)
    
    print("Cleaning up...")
    os.remove(databin)
    os.remove(databin_dec)

    print("Installing patches...")
    install_patches(isofile)

    print("Patching complete.")
    os.remove(isofile)
else:
    print(f"ERROR: Invalid ISO, your dump should match one of the following md5 hashes:")
    print(f"UMD: {UMD_MD5HASH}")
    print(f"PSN: {PSN_MD5HASH}")
    
os.system("pause")
