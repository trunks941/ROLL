Sub ROLL_HeartbeatTick()
    ' Comfort/Advanced VBScript body for a future global Value change event.
    ' Configure ROLL_Clock acquisition as Cyclic continuous in TIA first.
    ' This source file does not install the native event binding by itself.
    Dim currentValue
    On Error Resume Next
    Err.Clear
    currentValue = SmartTags("ROLL_Heartbeat")
    If Err.Number <> 0 Then
        Exit Sub
    End If
    If IsEmpty(currentValue) Or IsNull(currentValue) Then
        Exit Sub
    End If
    If Not IsNumeric(currentValue) Then
        Exit Sub
    End If
    If CDbl(currentValue) >= 2147483646 Or CDbl(currentValue) < 0 Then
        SmartTags("ROLL_Heartbeat") = 0
    Else
        SmartTags("ROLL_Heartbeat") = CLng(currentValue) + 1
    End If
End Sub
