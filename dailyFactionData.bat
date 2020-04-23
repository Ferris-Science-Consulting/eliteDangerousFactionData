SET logfile="C:\Users\filip\OneDrive\Elite Dangerous\FactionData\logfile"
@echo off
@echo Starting Script at %date% %time% >> %logfile%
"C:\Users\filip\AppData\Local\Programs\Python\Python37-32\python.exe" "C:\Users\filip\OneDrive\Elite Dangerous\FactionData\factionData.py"
@echo finished at %date% %time% >> %logfile%
