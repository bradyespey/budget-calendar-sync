// Main Script.gs

// Configurable Variables
const mainDaysToProjectAndClear = 120; // Number of days to project and clear events
const mainEnvironment = "prod";       // "prod", "dev", or "both"

function runMain() {
  var startTime = new Date();
  try {
    // Clear Calendars
    clearCalendars(mainDaysToProjectAndClear, mainEnvironment);

    // Refresh Accounts
    refreshAccounts();

    // Budget Projection
    executeBudgetProjection(mainDaysToProjectAndClear, mainEnvironment);

    var endTime = new Date();
    var scriptRunTime = (endTime - startTime) / 1000;
    var minutes = Math.floor(scriptRunTime / 60);
    var seconds = Math.round(scriptRunTime % 60);
    Logger.log('Main Script runtime: ' + minutes + ' minutes ' + seconds + ' seconds');
  } catch (error) {
    Logger.log('Error during Main Script execution: ' + error.message);
  }
}
