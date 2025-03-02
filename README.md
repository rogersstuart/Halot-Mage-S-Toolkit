Starting on a new PC and assuming you have virtualization enabled in your BIOS, you have python installed, and you know how to use git:

1) Run create_venv.py
2) Run generate_firmware.py
3) Copy output/firmware/ChituUpgrade.bin onto a flash drive with a MBR partition table and 1GB partition.
  a) Open command prompt and type diskpart
  b) list disk
  c) select disk [your disk]
  d) clean
  e) convert MBR
  f) create part pri size=1024
  g) you may need to select the volume
  h) format quick fs=fat32
  i) exit
4) Run ftp_serv.py to launch the appication. it will appear as a tray icon. on the first run a configuration file will be generated. input your printer IP and password.
