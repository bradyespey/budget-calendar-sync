// Configurable Variables
var daysToProjectAndClear = 14; // Adjust as needed
var environment = "dev"; // Set to "prod" for production or "dev" for development

// Calendar Configuration
var calendarConfig = {
    prod: {
        balanceCalendarId: "prod_balance_calendar_id@group.calendar.google.com",
        billsCalendarId: "prod_balance_calendar_id@group.calendar.google.com"
    },
    dev: {
        balanceCalendarId: "dev_balance_calendar_id@group.calendar.google.com",
        billsCalendarId: "dev_balance_calendar_id@group.calendar.google.com"
    }
};

// Dynamically Select Calendar IDs Based on Environment
var balanceCalendarId = calendarConfig[environment].balanceCalendarId;
var billsCalendarId = calendarConfig[environment].billsCalendarId;

// List of Federal Holidays (2024 and 2025)
var federalHolidays = [
    // 2024
    new Date("2024-01-01"), // New Year's Day
    new Date("2024-01-15"), // Martin Luther King Jr. Day
    new Date("2024-02-19"), // Presidents' Day
    new Date("2024-05-27"), // Memorial Day
    new Date("2024-06-19"), // Juneteenth National Independence Day
    new Date("2024-07-04"), // Independence Day
    new Date("2024-09-02"), // Labor Day
    new Date("2024-10-14"), // Columbus Day
    new Date("2024-11-11"), // Veterans Day
    new Date("2024-11-28"), // Thanksgiving Day
    new Date("2024-12-25"), // Christmas Day
    // 2025
    new Date("2025-01-01"), // New Year's Day
    new Date("2025-01-20"), // Martin Luther King Jr. Day
    new Date("2025-02-17"), // Presidents' Day
    new Date("2025-05-26"), // Memorial Day
    new Date("2025-06-19"), // Juneteenth National Independence Day
    new Date("2025-07-04"), // Independence Day
    new Date("2025-09-01"), // Labor Day
    new Date("2025-10-13"), // Columbus Day
    new Date("2025-11-11"), // Veterans Day
    new Date("2025-11-27"), // Thanksgiving Day
    new Date("2025-12-25")  // Christmas Day
];

// Number Formatting Function
function formatNumber(number) {
    var roundedNumber = Math.round(number);
    var sign = roundedNumber < 0 ? "-" : "";
    var numberString = Math.abs(roundedNumber).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return sign + "$" + numberString;
}

// Parse Transaction Amount
function parseTransactionAmount(amount) {
    var amountString = amount.toString();
    var parsedAmount = parseFloat(amountString.replace(/[^\d.-]/g, ''));
    return isNaN(parsedAmount) ? 0 : parsedAmount;
}

// Create Event Description
function createEventDescription(name, amount) {
    var sign = amount < 0 ? "-" : "+";
    return name + " " + sign + formatNumber(Math.abs(amount));
}

// Check if a Date is a Holiday
function isHoliday(date) {
    return federalHolidays.some(function(holiday) {
        return holiday.toDateString() === date.toDateString();
    });
}

// Adjust Transaction Date for Weekends and Holidays
function adjustTransactionDate(date, isPaycheck) {
    if (isPaycheck) {
        // Move paychecks to the previous weekday
        while (date.getDay() === 0 || date.getDay() === 6 || isHoliday(date)) {
            date.setDate(date.getDate() - 1);
        }
    } else {
        // Move other transactions to the next weekday
        while (date.getDay() === 0 || date.getDay() === 6 || isHoliday(date)) {
            date.setDate(date.getDate() + 1);
        }
    }
    return date;
}

// Clear Events from Calendar within Date Range
function clearEventsFromDate(calendar, startDate, endDate) {
    var events = calendar.getEvents(startDate, endDate);
    var chunkSize = 50; // Adjust based on API limits
    for (var i = 0; i < events.length; i += chunkSize) {
        var chunk = events.slice(i, i + chunkSize);
        chunk.forEach(function(event) {
            event.deleteEvent();
        });
        Utilities.sleep(100); // Prevent hitting API rate limits
    }
}

// Update Balance from API
function updateBalanceFromAPI() {
    var url = "https://theespeys.com/budgetcalendar/get-balance/";
    var response = UrlFetchApp.fetch(url, {method: 'get', muteHttpExceptions: true});

    if (response.getResponseCode() === 200) {
        var json = JSON.parse(response.getContentText());
        var balance = parseFloat(json.balance);

        var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Info");
        sheet.getRange("B3").setValue(balance);  // Update balance in Info sheet
        Logger.log('Automatically updated balance to: $' + balance);
    } else {
        throw new Error('Failed to retrieve balance from the API: ' + response.getContentText());
    }
}

// Get Last Day of the Month
function getLastDayOfMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
}

// Strip Time from Date
function stripTime(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

// Safely Add Months to a Date
function addMonthsSafely(date, monthsToAdd) {
    var newDate = new Date(date.getTime());
    var desiredMonth = newDate.getMonth() + monthsToAdd;
    newDate.setMonth(desiredMonth);

    // Calculate expected year and month
    var expectedMonth = (date.getMonth() + monthsToAdd) % 12;
    var expectedYear = date.getFullYear() + Math.floor((date.getMonth() + monthsToAdd) / 12);

    // If month overflowed, set to last day of target month
    if (newDate.getMonth() !== expectedMonth) {
        var lastDay = getLastDayOfMonth(expectedYear, expectedMonth);
        newDate.setDate(lastDay);
    }

    return newDate;
}

// Check if a date is the last day of its month
function isLastDayOfMonth(date) {
    var testDate = new Date(date.getTime());
    testDate.setDate(date.getDate() + 1);
    return testDate.getDate() === 1;
}

// Get the last day of a given month and year
function getLastDayOfMonthDate(year, month) {
    return new Date(year, month + 1, 0);
}

// Main Function to Project Balances and Add Transactions
function projectFutureBalancesAndBills() {
    var sheet = SpreadsheetApp.getActiveSpreadsheet();
    var infoSheet = sheet.getSheetByName("Info");
    var billsSheet = sheet.getSheetByName("Bills");
    var upcomingSheet = sheet.getSheetByName("Upcoming");

    var balanceCalendar = CalendarApp.getCalendarById(balanceCalendarId);
    var billsCalendar = CalendarApp.getCalendarById(billsCalendarId);

    var balanceFromAPI = parseFloat(infoSheet.getRange("B3").getValue());
    var manualBalance = parseFloat(infoSheet.getRange("B4").getValue());
    var originalBalance = !isNaN(manualBalance) ? manualBalance : balanceFromAPI;

    if (isNaN(originalBalance)) {
        throw new Error('Original balance is not a number.');
    }

    // Clear future events from calendars before projecting new ones
    var today = stripTime(new Date());
    var endDate = new Date(today);
    endDate.setDate(today.getDate() + daysToProjectAndClear);
    clearEventsFromDate(balanceCalendar, today, endDate);
    clearEventsFromDate(billsCalendar, today, endDate);

    // Fetch Bills Data (columns A to G)
    var billData = billsSheet.getRange(2, 1, billsSheet.getLastRow() - 1, 7).getValues();

    var lowestBalance = originalBalance;
    var highestBalance = originalBalance;
    var lowestBalanceDate = today;
    var highestBalanceDate = today;

    var eventQueue = [];
    var upcomingData = [];

    var balance = originalBalance;

    for (var i = 0; i < daysToProjectAndClear; i++) {
        var currentDate = new Date(today);
        currentDate.setDate(today.getDate() + i);
        currentDate = stripTime(currentDate); // Ensure no time component

        billData.forEach(function (bill) {
            var billName = bill[0];
            var category = bill[1].toString().trim().toLowerCase();
            var amount = parseTransactionAmount(bill[2]);
            var repeatsEvery = parseInt(bill[3], 10) || 1;
            var frequency = bill[4].toString().trim().toLowerCase();
            var startDate = stripTime(new Date(bill[5]));
            var endDateBill = bill[6] ? stripTime(new Date(bill[6])) : null;

            var isPaycheck = category === "paycheck";
            var transactionOccurs = false;

            // Determine if the transaction occurs on the current date based on frequency
            if (frequency === "one-time" || frequency === "one time") {
                if (startDate.toDateString() === currentDate.toDateString()) {
                    transactionOccurs = true;
                }
            } else if (frequency === "days") {
                var daysDiff = Math.floor((currentDate - startDate) / (24 * 60 * 60 * 1000));
                if (daysDiff >= 0 && (!endDateBill || currentDate <= endDateBill) && daysDiff % repeatsEvery === 0) {
                    transactionOccurs = true;
                }
            } else if (frequency === "weeks") {
                var weeksDiff = Math.floor((currentDate - startDate) / (7 * 24 * 60 * 60 * 1000));
                if (weeksDiff >= 0 && (!endDateBill || currentDate <= endDateBill) && weeksDiff % repeatsEvery === 0 && currentDate.getDay() === startDate.getDay()) {
                    transactionOccurs = true;
                }
            } else if (frequency === "months") {
                var monthsDiff = (currentDate.getFullYear() - startDate.getFullYear()) * 12 + (currentDate.getMonth() - startDate.getMonth());

                if (monthsDiff >= 0 && (!endDateBill || currentDate <= endDateBill) && monthsDiff % repeatsEvery === 0) {
                    var isStartDateLastDay = isLastDayOfMonth(startDate);

                    var occurrenceDate;
                    if (isStartDateLastDay) {
                        // Schedule on the last day of the current month
                        occurrenceDate = getLastDayOfMonthDate(currentDate.getFullYear(), currentDate.getMonth());
                    } else {
                        // Calculate the occurrence date safely
                        occurrenceDate = addMonthsSafely(startDate, monthsDiff);
                    }

                    occurrenceDate = stripTime(occurrenceDate); // Remove time component

                    // Adjust for weekends and holidays
                    var adjustedDate = adjustTransactionDate(new Date(occurrenceDate), isPaycheck);

                    // Check if the adjusted date matches the current loop date
                    if (adjustedDate.toDateString() === currentDate.toDateString()) {
                        transactionOccurs = true;
                    }
                }
            } else if (frequency === "years") {
                var yearsDiff = currentDate.getFullYear() - startDate.getFullYear();
                if (yearsDiff >= 0 && (!endDateBill || currentDate <= endDateBill) && yearsDiff % repeatsEvery === 0 && currentDate.getMonth() === startDate.getMonth() && currentDate.getDate() === startDate.getDate()) {
                    transactionOccurs = true;
                }
            }

            if (transactionOccurs) {
                // Adjust date for weekends/holidays
                var transactionDate = adjustTransactionDate(new Date(currentDate), isPaycheck);

                // Validate transactionDate
                if (isNaN(transactionDate.getTime())) {
                    Logger.log(`Error: Invalid transaction date for ${billName}. Skipping event.`);
                    return;
                }

                var eventDescription = createEventDescription(billName, amount);
                eventQueue.push({ calendar: billsCalendar, description: eventDescription, date: transactionDate });

                // Log only items being added to the calendar
                Logger.log(`Scheduling ${billName} on ${transactionDate.toDateString()}`);

                // Update upcoming data and balance
                upcomingData.push([billName, amount, balance, transactionDate, frequency, category]);
                if (i !== 0) balance += amount;
            }
        });

        // Add the projected balance event
        var balanceDescription = i === 0 ? "Balance: " + formatNumber(balance) : "Projected Balance: " + formatNumber(balance);
        eventQueue.push({ calendar: balanceCalendar, description: balanceDescription, date: currentDate });

        // Log the projected balance for each day
        Logger.log(`Projected balance on ${currentDate.toDateString()}: ${formatNumber(balance)}`);

        // Update lowest and highest balance trackers
        if (balance < lowestBalance) {
            lowestBalance = balance;
            lowestBalanceDate = new Date(currentDate);
        }
        if (balance > highestBalance) {
            highestBalance = balance;
            highestBalanceDate = new Date(currentDate);
        }
    }

    // Batch create events in calendars
    eventQueue.forEach(function (event) {
        event.calendar.createAllDayEvent(event.description, event.date);
    });

    // Update Upcoming sheet with scheduled transactions
    if (upcomingData.length > 0) {
        upcomingSheet.getRange(2, 1, upcomingData.length, upcomingData[0].length).setValues(upcomingData);
    }

    // Update balance information in the Info sheet
    infoSheet.getRange("B5").setValue(lowestBalance);
    infoSheet.getRange("C5").setValue(lowestBalanceDate);
    infoSheet.getRange("B6").setValue(highestBalance);
    infoSheet.getRange("C6").setValue(highestBalanceDate);
}

// Combined Main Function to Run Everything
function executeBudgetProjection() {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Info");
    var startTime = new Date();

    try {
        // Update balance from API
        updateBalanceFromAPI();

        // Record the current date and time in C3
        sheet.getRange("C3").setValue(new Date());

        // Project future balances and add transactions
        projectFutureBalancesAndBills();

        var endTime = new Date();
        var scriptRunTime = (endTime - startTime) / 1000;
        var minutes = Math.floor(scriptRunTime / 60);
        var seconds = Math.round(scriptRunTime % 60);
        Logger.log('Script runtime: ' + minutes + ' minutes ' + seconds + ' seconds');
    } catch (error) {
        Logger.log('Error during execution: ' + error.message);
    }
}