#!/usr/bin/python

import sys, os, shutil
import glob
import pycdlib
import hashlib
import subprocess
import tempfile

import mhef.psp
from io import BytesIO

MD5HASH1 = "1f76ee9ccbd6d39158f06e6e5354a5bd"
MD5HASH2 = "0311fb5f949ce95f81034743cf24a903"
isofile = sys.argv[1]

databin = tempfile.gettempdir()+"/DATA.BIN"
databin_dec = tempfile.gettempdir()+"/DATA.BIN.DEC"

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Check file hash
def get_iso_hash(isofile):
    with open(isofile, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()

# Extract data.bin from the ISO
def extract_data_bin(isofile):
    iso = pycdlib.PyCdlib()
    iso.open(isofile)

    data_bin = BytesIO()
    iso.get_file_from_iso_fp(data_bin, iso_path='/PSP_GAME/USRDIR/DATA.BIN')

    iso.close()

    with open(databin, "wb") as f:
        f.write(data_bin.getbuffer())

# Decrypt data.bin
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
    patch1 = exe_path+"/patches/FUComplete.xdelta"
    
    nisofile = tempfile.gettempdir()+os.path.basename(isofile)[:-4]+"_FUC.iso"
    nisofile = nisofile.replace("_backup", "")
    subprocess.run([xdel, "-d", "-s", isofile, patch1, nisofile], shell=True, check=True)
        
    patches = sorted(glob.glob(exe_path+"/patches/*[!FUComplete]*.xdelta"))
    for i, p in enumerate(patches):
        name = os.path.basename(p)
        q = input(f"Install {name}? (y/n): ")
        
        if q in ["y", "Y"]:
            nisofile2 = f"{nisofile[:-4]}_{i}.iso"
            subprocess.run([xdel, "-d", "-s", nisofile, p, nisofile2], shell=True, check=True)
            os.remove(nisofile)
            nisofile = nisofile2
            
    shutil.move(nisofile, f"{isofile[:-4]}_FUC.iso")

print(f"*****FUComplete Patcher*****\n")
print("Checking ISO...")
if get_iso_hash(isofile) == MD5HASH1:
    print("Backing up ISO...")
    isofile_bak = f"{isofile[:-4]}_backup.iso"
    shutil.copy2(isofile, isofile_bak)
    
    print("Extracting DATA.BIN...")
    extract_data_bin(isofile)
    
    print("Decrypting DATA.BIN (this may take a few minutes)...")
    decrypt_data_bin(databin)
    
    print("Replacing DATA.BIN...")
    replace_data_bin(isofile, databin_dec)
    
    print("Cleaning up...")
    os.remove(databin)
    os.remove(databin_dec)

    print("Checking replaced ISO...")
    if get_iso_hash(isofile) == MD5HASH2:
        print("Preparations complete.")
        
        print("Installing patches...")
        install_patches(isofile)
        
        print("Patching complete.")
        os.remove(isofile)
    else:
        print("Error, Invalid replaced ISO.")
else:
    print(f"Invalid ISO, your dump should match md5: {MD5HASH1}")
    
os.system("pause")
