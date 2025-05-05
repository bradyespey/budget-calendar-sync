//gas/Budget Projection.js


// Configurable Variables
const budgetDaysToProject = 14; // Number of days to project events
const budgetEnvironment = "prod"; // "prod", "dev", or "both"
const balanceThreshold = 2000;   // Email alert if projected lowest balance falls below this value

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

  // Load holidays for projection period
  const holidaysSet = loadUsFederalHolidaysForProjection(days);

  // Access Spreadsheets
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const infoSheet = ss.getSheetByName("Info");
  const billsSheet = ss.getSheetByName("Bills");
  const upcomingSheet = ss.getSheetByName("Upcoming");

  // Check for manual override first
  const manualOverrideValue = infoSheet.getRange("B4").getValue();
  let manualBalance = NaN;
  if (manualOverrideValue !== "" && manualOverrideValue !== null) {
    manualBalance = parseTransactionAmount(manualOverrideValue);
    // Update cell C4 with the current date in M/D/YYYY format
    const now = new Date();
    const formattedDate = Utilities.formatDate(now, SpreadsheetApp.getActive().getSpreadsheetTimeZone(), "M/d/yyyy");
    infoSheet.getRange("C4").setValue(formattedDate);
  }
  
  // If no manual override, update API balance
  if (isNaN(manualBalance)) {
    updateBalanceFromAPIForProjection();
  }

  // Read API balance from B3 (it was updated by the API call if no manual override)
  const balAPI = parseFloat(infoSheet.getRange("B3").getValue());
  const originalBalance = !isNaN(manualBalance) ? manualBalance : balAPI;
  
  // Log only once: if manual override exists, log it here.
  if (!isNaN(manualBalance)) {
    Logger.log("Updated manual override balance to: " + formatNumber(manualBalance));
  }
  // Otherwise, let updateBalanceFromAPIForProjection() handle the logging.

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

      // Determine if bill occurs on currentDate based on frequency
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
        if (weeksDiff >= 0 && (!endDateBill || currentDate <= endDateBill) &&
            weeksDiff % repeatsEvery === 0 && currentDate.getDay() === startDate.getDay()) {
          occurs = true;
        }
      } else if (frequency === "months") {
        const monthsDiff = (currentDate.getFullYear() - startDate.getFullYear()) * 12 +
                           (currentDate.getMonth() - startDate.getMonth());
        if (monthsDiff >= 0 && (!endDateBill || currentDate <= endDateBill) &&
            monthsDiff % repeatsEvery === 0) {
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
        if (yearsDiff >= 0 && (!endDateBill || currentDate <= endDateBill) &&
            yearsDiff % repeatsEvery === 0 &&
            currentDate.getMonth() === startDate.getMonth() &&
            currentDate.getDate() === startDate.getDate()) {
          occurs = true;
        }
      }

      // If the bill occurs, update the balance (for days after today) before recording it
      if (occurs) {
        const txDate = adjustTransactionDate(new Date(currentDate), isPaycheck, holidaysSet);
        if (!isNaN(txDate.getTime())) {
          if (i !== 0) {
            balance += amount;
          }
          const desc = createEventDescription(billName, amount);
          eventQueue.push({ calendar: billsCal, description: desc, date: txDate });
          upcomingData.push([billName, amount, balance, txDate, frequency, category]);
        }
      }
    });

    // Queue the daily balance event with the final balance for the day
    const balDesc = i === 0 ? `Balance: ${formatNumber(balance)}` : `Projected Balance: ${formatNumber(balance)}`;
    eventQueue.push({ calendar: balanceCal, description: balDesc, date: currentDate });

    // Track the lowest and highest balance for the projection
    if (balance < lowest) {
      lowest = balance;
      lowestDate = new Date(currentDate);
    }
    if (balance > highest) {
      highest = balance;
      highestDate = new Date(currentDate);
    }
  }

  // Create calendar events in chunks to prevent rate limiting
  const chunkSize = 50; // Reduced chunk size
  for (let j = 0; j < eventQueue.length; j += chunkSize) {
    const chunk = eventQueue.slice(j, j + chunkSize);
    chunk.forEach(evt => {
      try {
        evt.calendar.createAllDayEvent(evt.description, evt.date);
      } catch(e) {
        Logger.log(`Error creating event: ${e}`);
      }
    });
    Utilities.sleep(200); // Increased delay between chunks
  }

  // Update Upcoming Sheet with rounded balance values
  if (upcomingData.length > 0) {
    upcomingSheet.getRange(2, 1, upcomingData.length, upcomingData[0].length).setValues(upcomingData);
  }

  // Write the lowest and highest balance values (rounded) and their dates to the Info sheet
  infoSheet.getRange("B5").setValue(Math.round(lowest));
  infoSheet.getRange("C5").setValue(lowestDate);
  infoSheet.getRange("B6").setValue(Math.round(highest));
  infoSheet.getRange("C6").setValue(highestDate);

  // Send email alert if projected lowest balance is below threshold
  if (lowest < balanceThreshold) {
    const recipient = "bradyjennytx@gmail.com";
    const subject = "Low Balance Alert: Budget Projection";
    const body = `Your projected lowest balance is ${formatNumber(lowest)} on ${lowestDate.toLocaleDateString()}. Please review your upcoming bills and expenses.`;
    GmailApp.sendEmail(recipient, subject, body);
    Logger.log("Low balance alert email sent to: " + recipient);
  }

  Logger.log(`Completed budget projection for ${days} days.`);
}

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
      Logger.log("Updated API balance to: " + formatNumber(bal));
    } else {
      throw new Error(`Failed to retrieve balance: ${response.getContentText()}`);
    }
  } catch (err) {
    Logger.log("Error in updateBalanceFromAPIForProjection: " + err.message);
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