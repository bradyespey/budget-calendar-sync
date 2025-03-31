// Budget Projection.gs

// Configurable Variables
const budgetDaysToProject = 14; // Number of days to project events
const budgetEnvironment = "prod"; // "prod", "dev", or "both"

function executeBudgetProjection(days = budgetDaysToProject, environment = budgetEnvironment) {
  var startTime = new Date();
  try {
    projectFutureBalancesAndBills(days, environment);
    
    var endTime = new Date();
    var scriptRunTime = (endTime - startTime) / 1000; // in seconds
    var minutes = Math.floor(scriptRunTime / 60);
    var seconds = Math.round(scriptRunTime % 60);
    Logger.log('Budget Projection runtime: ' + minutes + ' minutes ' + seconds + ' seconds');
  } catch (error) {
    Logger.log('Error during Budget Projection execution: ' + error.message);
  }
}

function projectFutureBalancesAndBills(days, env) {
  // Retrieve Calendar IDs based on environment
  const props = PropertiesService.getScriptProperties();
  const calIds = getCalendarIdsProjection(props, env);
  if (!calIds) return;

  const balanceCal = CalendarApp.getCalendarById(calIds.balanceId);
  const billsCal = CalendarApp.getCalendarById(calIds.billsId);
  if (!balanceCal || !billsCal) {
    Logger.log("Calendars not found for the specified environment.");
    return;
  }

  // Load Holidays and Update Balance
  const holidaysSet = loadUsFederalHolidaysForProjection(days);
  updateBalanceFromAPIForProjection();

  // Access Spreadsheets
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const infoSheet = ss.getSheetByName("Info");
  const billsSheet = ss.getSheetByName("Bills");
  const upcomingSheet = ss.getSheetByName("Upcoming");

  const balAPI = parseFloat(infoSheet.getRange("B3").getValue());
  const manBal = parseFloat(infoSheet.getRange("B4").getValue());
  const originalBalance = !isNaN(manBal) ? manBal : balAPI;
  if (isNaN(originalBalance)) {
    throw new Error("Original balance is not valid.");
  }

  // Define Date Range
  const today = stripTime(new Date());
  const endDate = new Date(today);
  endDate.setDate(today.getDate() + days);

  // Fetch Bills Data
  const billData = billsSheet.getRange(2, 1, billsSheet.getLastRow() - 1, 7).getValues();
  let lowest = originalBalance, highest = originalBalance;
  let lowestDate = today, highestDate = today;
  const eventQueue = [];
  const upcomingData = [];
  let balance = originalBalance;

  // Iterate Over Each Day
  for (let i = 0; i < days; i++) {
    const currentDate = new Date(today);
    currentDate.setDate(today.getDate() + i);
    stripTime(currentDate);

    billData.forEach(row => {
      const billName = row[0];
      const category = String(row[1]).trim().toLowerCase();
      const amount = parseTransactionAmount(row[2]);
      const repeatsEvery = parseInt(row[3], 10) || 1;
      const frequency = String(row[4]).trim().toLowerCase();
      const startDate = stripTime(new Date(row[5]));
      const endDateBill = row[6] ? stripTime(new Date(row[6])) : null;
      const isPaycheck = (category === "paycheck");
      let occurs = false;

      // Determine if Bill Occurs Today
      if (frequency === "one-time" || frequency === "one time") {
        if (startDate.toDateString() === currentDate.toDateString()) {
          occurs = true;
        }
      } else if (frequency === "days") {
        const daysDiff = Math.floor((currentDate - startDate) / 86400000);
        if (daysDiff >= 0 && (!endDateBill || currentDate <= endDateBill) && daysDiff % repeatsEvery === 0) {
          occurs = true;
        }
      } else if (frequency === "weeks") {
        const weeksDiff = Math.floor((currentDate - startDate) / (7 * 86400000));
        if (weeksDiff >= 0 && (!endDateBill || currentDate <= endDateBill) && weeksDiff % repeatsEvery === 0 && currentDate.getDay() === startDate.getDay()) {
          occurs = true;
        }
      } else if (frequency === "months") {
        const monthsDiff = (currentDate.getFullYear() - startDate.getFullYear()) * 12 + (currentDate.getMonth() - startDate.getMonth());
        if (monthsDiff >= 0 && (!endDateBill || currentDate <= endDateBill) && monthsDiff % repeatsEvery === 0) {
          const isLast = isLastDayOfMonth(startDate);
          let occDate = isLast 
            ? getLastDayOfMonthDate(currentDate.getFullYear(), currentDate.getMonth())
            : addMonthsSafely(startDate, monthsDiff);
          occDate = stripTime(occDate);
          const adjusted = adjustTransactionDate(new Date(occDate), isPaycheck, holidaysSet);
          if (adjusted.toDateString() === currentDate.toDateString()) {
            occurs = true;
          }
        }
      } else if (frequency === "years") {
        const yearsDiff = currentDate.getFullYear() - startDate.getFullYear();
        if (yearsDiff >= 0 && (!endDateBill || currentDate <= endDateBill) && yearsDiff % repeatsEvery === 0 &&
            currentDate.getMonth() === startDate.getMonth() && currentDate.getDate() === startDate.getDate()) {
          occurs = true;
        }
      }

      // Queue Event if Occurs
      if (occurs) {
        const txDate = adjustTransactionDate(new Date(currentDate), isPaycheck, holidaysSet);
        if (!isNaN(txDate.getTime())) {
          const desc = createEventDescription(billName, amount);
          eventQueue.push({ calendar: billsCal, description: desc, date: txDate });
          upcomingData.push([billName, amount, balance, txDate, frequency, category]);
          if (i !== 0) balance += amount;
        }
      }
    });

    // Queue Balance Event
    const balDesc = i === 0 ? `Balance: ${formatNumber(balance)}` : `Projected Balance: ${formatNumber(balance)}`;
    eventQueue.push({ calendar: balanceCal, description: balDesc, date: currentDate });

    // Track Lowest and Highest Balance
    if (balance < lowest) {
      lowest = balance;
      lowestDate = new Date(currentDate);
    }
    if (balance > highest) {
      highest = balance;
      highestDate = new Date(currentDate);
    }
  }

  // Create Events in Chunks
  const chunkSize = 100;
  for (let j = 0; j < eventQueue.length; j += chunkSize) {
    const chunk = eventQueue.slice(j, j + chunkSize);
    chunk.forEach(evt => {
      try {
        evt.calendar.createAllDayEvent(evt.description, evt.date);
      } catch(e) {
        Logger.log(`Error creating event: ${e}`);
      }
    });
    Utilities.sleep(20); // Prevent rate limiting
  }

  // Update Upcoming Sheet
  if (upcomingData.length > 0) {
    upcomingSheet.getRange(2, 1, upcomingData.length, upcomingData[0].length).setValues(upcomingData);
  }

  // Update Balance Information
  infoSheet.getRange("B5").setValue(lowest);
  infoSheet.getRange("C5").setValue(lowestDate);
  infoSheet.getRange("B6").setValue(highest);
  infoSheet.getRange("C6").setValue(highestDate);

  Logger.log(`Completed budget projection for ${days} days.`);
}

// Helper Functions
function getCalendarIdsProjection(props, env) {
  const envLower = env.toLowerCase();
  if (envLower === "prod") {
    return {
      balanceId: props.getProperty("PROD_BALANCE_CALENDAR_ID"),
      billsId: props.getProperty("PROD_BILLS_CALENDAR_ID")
    };
  } else if (envLower === "dev") {
    return {
      balanceId: props.getProperty("DEV_BALANCE_CALENDAR_ID"),
      billsId: props.getProperty("DEV_BILLS_CALENDAR_ID")
    };
  } else {
    Logger.log('Invalid environment for Budget Projection. Must be "prod" or "dev".');
    return null;
  }
}

function loadUsFederalHolidaysForProjection(days) {
  const startDate = new Date();
  const endDate = new Date();
  endDate.setDate(startDate.getDate() + days);
  const startYear = startDate.getFullYear();
  const endYear = endDate.getFullYear();
  const holidaysSet = new Set();

  for (let y = startYear; y <= endYear; y++) {
    const url = `https://date.nager.at/api/v3/PublicHolidays/${y}/US`;
    try {
      const res = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
      if (res.getResponseCode() === 200) {
        const data = JSON.parse(res.getContentText());
        data.forEach(h => {
          const hd = new Date(`${h.date}T00:00:00`);
          if (hd >= startDate && hd <= endDate) {
            holidaysSet.add(hd.toDateString());
          }
        });
      }
    } catch(e) {
      Logger.log(`Holiday fetch error for year ${y}: ${e}`);
    }
  }
  return holidaysSet;
}

function adjustTransactionDate(date, isPaycheck, holidaysSet) {
  if (isPaycheck) {
    while (date.getDay() === 0 || date.getDay() === 6 || holidaysSet.has(date.toDateString())) {
      date.setDate(date.getDate() - 1);
    }
  } else {
    while (date.getDay() === 0 || date.getDay() === 6 || holidaysSet.has(date.toDateString())) {
      date.setDate(date.getDate() + 1);
    }
  }
  return date;
}

function updateBalanceFromAPIForProjection() {
  const props = PropertiesService.getScriptProperties();
  const apiAuth = props.getProperty("API_AUTH");
  if (!apiAuth) {
    Logger.log("API_AUTH missing in Script Properties.");
    return;
  }

  try {
    const url = "https://api.theespeys.com/chase_balance";
    const options = {
      method: "get",
      headers: {
        "Authorization": "Basic " + Utilities.base64Encode(apiAuth),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
                      "AppleWebKit/537.36 (KHTML, like Gecko) " +
                      "Chrome/98.0.4758.102 Safari/537.36"
      },
      muteHttpExceptions: true
    };

    const response = UrlFetchApp.fetch(url, options);
    if (response.getResponseCode() === 200) {
      const js = JSON.parse(response.getContentText());
      const bal = parseFloat(js.chase_balance);
      const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Info");
      // Update balance in cell B3:
      sheet.getRange("B3").setValue(bal);
      // Also update the date in cell C3 with the current date:
      sheet.getRange("C3").setValue(new Date());
      Logger.log(`Updated balance to: ${formatNumber(bal)}`);
    } else {
      throw new Error(`Failed to retrieve balance: ${response.getContentText()}`);
    }
  } catch (err) {
    Logger.log(`Error in updateBalanceFromAPIForProjection: ${err.message}`);
  }
}

function formatNumber(n) {
  const rounded = Math.round(n);
  const sign = rounded < 0 ? "-" : "";
  const absStr = Math.abs(rounded).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${sign}$${absStr}`;
}

function parseTransactionAmount(val) {
  const p = parseFloat(val.toString().replace(/[^\d.-]/g, ""));
  return isNaN(p) ? 0 : p;
}

function createEventDescription(name, amt) {
  const sign = amt < 0 ? "-" : "+";
  return `${name} ${sign}${formatNumber(Math.abs(amt))}`;
}

function stripTime(d) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function addMonthsSafely(date, monthsToAdd) {
  const newDate = new Date(date);
  newDate.setMonth(newDate.getMonth() + monthsToAdd);
  const expectedMonth = (date.getMonth() + monthsToAdd) % 12;
  const expectedYear = newDate.getFullYear();
  if (newDate.getMonth() !== expectedMonth) {
    newDate.setDate(getLastDayOfMonth(expectedYear, expectedMonth));
  }
  return newDate;
}

function getLastDayOfMonth(y, m) {
  return new Date(y, m + 1, 0).getDate();
}

function getLastDayOfMonthDate(y, m) {
  return new Date(y, m + 1, 0);
}

function isLastDayOfMonth(date) {
  const nd = new Date(date);
  nd.setDate(nd.getDate() + 1);
  return nd.getDate() === 1;
}
