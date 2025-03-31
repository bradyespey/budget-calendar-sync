// Custom Menu Functions.gs

function createCustomMenu() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Update Budget')
    .addItem('Main Script', 'runMain')
    .addItem('Budget Projection', 'executeBudgetProjection')
    .addItem('Clear Calendars', 'clearCalendars')
    .addItem('Accounts Refresh', 'refreshAccounts')
    .addToUi();
}

function onOpen() {
  createCustomMenu();
}

// Wrapper Functions for Custom Menu

function runBudgetProjection() {
  // Configurable Variables
  const budgetDaysToProject = 30; // Number of days to project events
  const budgetEnvironment = "prod"; // "prod", "dev", or "both"

  executeBudgetProjection(budgetDaysToProject, budgetEnvironment);
}

function runClearCalendars() {
  // Configurable Variables
  const clearDaysToClear = 30; // Number of days to clear events
  const clearEnvironment = "prod"; // "prod", "dev", or "both"

  clearCalendars(clearDaysToClear, clearEnvironment);
}

function runAccountsRefresh() {
  refreshAccounts();
}
