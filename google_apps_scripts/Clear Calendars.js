// Clear Calendars.gs

// Configurable Variables
const clearDaysToClear = 120; // Number of days to clear events
const clearEnvironment = "prod"; // "prod", "dev", or "both"

function clearCalendars(days = clearDaysToClear, environment = clearEnvironment) {
  var startTime = new Date();
  try {
    // Retrieve Calendar IDs from Script Properties
    const props = PropertiesService.getScriptProperties();
    const ids = {
      devBalanceId: props.getProperty("DEV_BALANCE_CALENDAR_ID"),
      devBillsId: props.getProperty("DEV_BILLS_CALENDAR_ID"),
      prodBalanceId: props.getProperty("PROD_BALANCE_CALENDAR_ID"),
      prodBillsId: props.getProperty("PROD_BILLS_CALENDAR_ID")
    };

    // Determine Environments to Process
    let envList = [];
    const envLower = environment.toLowerCase();
    if (envLower === "both") {
      envList = ["dev", "prod"];
    } else if (["dev", "prod"].includes(envLower)) {
      envList = [envLower];
    } else {
      Logger.log('Invalid environment. Must be "prod", "dev", or "both".');
      return;
    }

    // Define Date Range
    const today = new Date();
    const endDate = new Date();
    endDate.setDate(today.getDate() + days);

    // Clear Events for Each Environment
    envList.forEach(env => {
      const balanceId = env === "dev" ? ids.devBalanceId : ids.prodBalanceId;
      const billsId = env === "dev" ? ids.devBillsId : ids.prodBillsId;

      const balanceCal = CalendarApp.getCalendarById(balanceId);
      const billsCal = CalendarApp.getCalendarById(billsId);

      if (balanceCal && billsCal) {
        clearEvents(balanceCal, today, endDate);
        clearEvents(billsCal, today, endDate);
        Logger.log(`Cleared calendar events for ${env} over ${days} days.`);
      } else {
        Logger.log(`Calendars not found for environment: ${env}`);
      }
    });

    var endTime = new Date();
    var scriptRunTime = (endTime - startTime) / 1000;
    var minutes = Math.floor(scriptRunTime / 60);
    var seconds = Math.round(scriptRunTime % 60);
    Logger.log('Clear Calendars runtime: ' + minutes + ' minutes ' + seconds + ' seconds');
  } catch (error) {
    Logger.log('Error during Clear Calendars execution: ' + error.message);
  }
}

// Helper Function to Clear Events
function clearEvents(calendar, startDate, endDate) {
  const events = calendar.getEvents(startDate, endDate);
  const chunkSize = 100;

  for (let i = 0; i < events.length; i += chunkSize) {
    const chunk = events.slice(i, i + chunkSize);
    chunk.forEach(event => {
      try {
        event.deleteEvent();
      } catch (err) {
        Logger.log(`Error deleting event: ${err}`);
      }
    });
    Utilities.sleep(20); // Prevent rate limiting
  }
  Logger.log(`Deleted ${events.length} events from ${calendar.getName()} between ${startDate.toDateString()} and ${endDate.toDateString()}.`);
}
