' HARMLESS VBA macro mimicking the structure of a maldoc, for recognition practice only.
' Does NOT download or run any real payload. AutoOpen here only shows a MsgBox.
' Goal: practice recognizing the auto-exec trigger and a string that is split/hidden.

Sub AutoOpen()
    ' auto-exec trigger: runs as soon as the file is opened
    Document_Open
End Sub

Sub Document_Open()
    Dim a As String
    ' string split apart to dodge a plain grep: reassembles into "Hello Analyst"
    a = "Hel" & "lo" & Chr(32) & "Ana" & "lyst"
    MsgBox a
    ' In a real maldoc, this spot would be:
    '   CreateObject("WScript.Shell").Run "powershell -enc <base64>"
    ' This lab leaves it blank on purpose, for safety.
End Sub
