Set WshShell = CreateObject("WScript.Shell")
' Inicia FORXIME/2 de forma totalmente silenciosa sin la consola negra
WshShell.Run ".\venv\Scripts\pythonw.exe -m streamlit run app.py", 0, False
Set WshShell = Nothing
