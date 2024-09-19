// Create Custom Menu Function
function createCustomMenu() {
  var ui = SpreadsheetApp.getUi(); // Gets the user interface of the spreadsheet for menu creation
  ui.createMenu('Update Budget')
    .addItem('Update Full Budget', 'executeBudgetProjection')
    .addItem('Update Balance from Chase', 'updateBalanceFromChaseEmail')
    .addItem('Project Future Balances', 'projectFutureBalancesAndBills')
    .addItem('Clear Calendars', 'clearCalendars')
    .addToUi();
}

// Function to clear events for the defined period from the calendars
function clearCalendars() {
  var balanceCalendar = CalendarApp.getCalendarById(balanceCalendarId);
  var billsCalendar = CalendarApp.getCalendarById(billsCalendarId);
  var today = new Date();
  var endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() + daysToProjectAndClear);
  clearEventsFromDate(balanceCalendar, today, endDate);
  clearEventsFromDate(billsCalendar, today, endDate);
  Logger.log('Calendars cleared for the next ' + daysToProjectAndClear + ' days.');
}

// Run Custom Menu Function on Open
function onOpen() {
  createCustomMenu(); // This will create the menu every time the spreadsheet is opened
}
