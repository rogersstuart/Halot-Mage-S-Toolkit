Starting on a new PC and assuming you have virtualization enabled in your BIOS, you have python installed, and you know how to use git:

1) Run create_venv.py
2) Run generate_firmware.py
3) Copy output/firmware/ChituUpgrade.bin onto a flash drive with a MBR partition table and 1GB partition.
  1) Open command prompt and type diskpart
  2) list disk
  3) select disk [your disk]
  4) clean
  5) convert MBR
  6) create part pri size=1024
  7) you may need to select the volume
  8) format quick fs=fat32
  9) exit
4) Run ftp_serv.py to launch the appication. it will appear as a tray icon. on the first run a configuration file will be generated. input you printer IP and password.
