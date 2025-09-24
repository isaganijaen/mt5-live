' Global Variabls
Public order_loc As Integer
Public deal_loc As Integer
Public actual_deal_start As Integer



Sub unmerge_cells()
'
' unmerge_cells Macro
'

'
    Workbooks.Open Filename:= _
        "C:\Users\Gani\AppData\Roaming\MetaQuotes\Terminal\BB16F565FAAA6B23A20C26C49416FF05\MQL5\Profiles\Templates\Demo-ReportHistory.xlsx"

    Range("M1").Activate
    Columns("M:N").Select

    With Selection
        .HorizontalAlignment = xlGeneral
        .VerticalAlignment = xlCenter
        .WrapText = False
        .Orientation = 0
        .AddIndent = False
        .IndentLevel = 0
        .ShrinkToFit = False
        .ReadingOrder = xlContext
        .MergeCells = False
    End With
    'ActiveWorkbook.Save
End Sub



' ---------------------------------
' Code in another Standard Module (e.g., Module2)
' ---------------------------------

Sub FindAnd_DeleteOrders()

    Dim ws As Worksheet
    Dim findOrder As Range
    Dim findDeal As Range

    ' Set the worksheet you are working on to avoid errors
    Set ws = ActiveSheet

    ' ----------------------------------------------------
    ' 1. Find the "order" location and pass its row to order_loc
    ' ----------------------------------------------------
    Set findOrder = ws.Cells.Find(What:="order", LookIn:=xlValues, LookAt:=xlWhole)
    
    If Not findOrder Is Nothing Then
        ' Store the ROW NUMBER in the global variable
        order_loc = findOrder.Row
    Else
        MsgBox "'order' not found. Cannot proceed.", vbCritical
        Exit Sub
    End If

    ' ----------------------------------------------------
    ' 2. Find the "deals" location and pass its row to deal_loc
    ' ----------------------------------------------------
    Set findDeal = ws.Cells.Find(What:="deals", LookIn:=xlValues, LookAt:=xlWhole)
    
    If Not findDeal Is Nothing Then
        ' Store the ROW NUMBER in the global variable
        deal_loc = findDeal.Row
    Else
        MsgBox "'deals' not found. Cannot proceed.", vbCritical
        Exit Sub
    End If

    ' ----------------------------------------------------
    ' 3. Select and Delete the Rows
    ' ----------------------------------------------------
    
    ' Check if the rows are in the correct order (order must be above deals)
    If order_loc >= deal_loc Then
        MsgBox "The 'order' row must be above the 'deals' row to delete a range.", vbExclamation
        Exit Sub
    End If

    ' Construct the range string using the row numbers and delete directly.
    ' We use (order_loc + 1) to start DELETE *after* the "order" row,
    ' and (deal_loc - 1) to end DELETE *before* the "deals" row.
    Dim RangeToDelete As Range
    Set RangeToDelete = ws.Rows(order_loc - 1 & ":" & deal_loc - 1)
    
    ' Best practice: Disable alerts to prevent the confirmation box
    Application.DisplayAlerts = False
    
    ' Delete the range (Shift:=xlUp is the default, but good to include)
    RangeToDelete.Delete Shift:=xlUp
    
    ' Re-enable alerts
    Application.DisplayAlerts = True
    
    ' MsgBox "Rows from " & (order_loc + 1) & " to " & (deal_loc - 1) & " have been deleted.", vbInformation

    
End Sub



Sub ConsolidateData()
    unmerge_cells
    FindAnd_DeleteOrders
    
    '--------------------------------------------
    ' Replace dots with dash for the dates
    ' in column A
    '--------------------------------------------
    
    Columns("A:A").Select
    
    Selection.Replace What:=".", Replacement:="-", LookAt:=xlPart, _
        SearchOrder:=xlByRows, MatchCase:=False, SearchFormat:=False, _
        ReplaceFormat:=False, FormulaVersion:=xlReplaceFormula2
        
        

End Sub



































