// Clear Manual Spreadsheet Values.gs

function clearManualOverride() {
  // Open the active spreadsheet and the "Info" sheet
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Info");

  // Clear the values in cells B4 and C4
  sheet.getRange("B4").clearContent();
  sheet.getRange("C4").clearContent();
}