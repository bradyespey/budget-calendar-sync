// Calendar IDs and Configuration
var balanceCalendarId = "balance_calendar_id@group.calendar.google.com";
var billsCalendarId = "bills_calendar_id@group.calendar.google.com";
var daysToProjectAndClear = 120;

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
    new Date("2024-12-25"), // Christmas Day,
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

// Number Formatting Functions
function formatNumber(number) {
    var roundedNumber = Math.round(number);
    var sign = roundedNumber < 0 ? "-" : "";
    var numberString = Math.abs(roundedNumber).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return sign + "$" + numberString;
}

// Parse transaction amount
function parseTransactionAmount(amount) {
    var amountString = amount.toString();
    var parsedAmount = parseFloat(amountString.replace(/[^\d.-]/g, ''));
    return isNaN(parsedAmount) ? 0 : parsedAmount;
}

// Calendar Event Description Function
function createEventDescription(name, amount) {
    var sign = amount < 0 ? "-" : "+";
    return name + " " + sign + formatNumber(Math.abs(amount));
}

// Check if a date is a holiday
function isHoliday(date) {
    for (var i = 0; i < federalHolidays.length; i++) {
        if (federalHolidays[i].toDateString() === date.toDateString()) {
            return true;
        }
    }
    return false;
}

// Adjust date based on transaction type (paycheck or others)
function adjustTransactionDate(date, isPaycheck) {
    if (isPaycheck) {
        // Move paycheck transactions to the previous weekday
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

// Clear Events from Date Function
function clearEventsFromDate(calendar, startDate, endDate) {
    var events = calendar.getEvents(startDate, endDate);
    var chunkSize = 50; // Adjust chunk size based on limits
    for (var i = 0; i < events.length; i += chunkSize) {
        var chunk = events.slice(i, i + chunkSize);
        chunk.forEach(function(event) {
            event.deleteEvent();
        });
        Utilities.sleep(100); // Slight delay to avoid hitting API limits
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

// Main Function for Projecting Balances and Adding Transactions
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
    var today = new Date();
    var endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() + daysToProjectAndClear);
    clearEventsFromDate(balanceCalendar, today, endDate);
    clearEventsFromDate(billsCalendar, today, endDate);

    var billData = billsSheet.getRange("A2:F" + billsSheet.getLastRow()).getValues();

    var lowestBalance = originalBalance;
    var highestBalance = originalBalance;
    var lowestBalanceDate = new Date();
    var highestBalanceDate = new Date();

    var eventQueue = [];
    var upcomingData = [];

    for (var i = 0; i < daysToProjectAndClear; i++) {
        var date = new Date();
        date.setDate(today.getDate() + i);
        var balance = originalBalance;

        billData.forEach(function (bill) {
            var billName = bill[0]; // Name column
            var amount = parseTransactionAmount(bill[2]); // Amount column
            var repeatsEvery = bill[3]; // Repeats Every column
            var frequency = bill[4]; // Frequency column
            var startDate = new Date(bill[5]); // Start Date column
            var endDate = bill[6] ? new Date(bill[6]) : null; // End Date column
            var category = bill[1]; // Category column

            var isPaycheck = category.toLowerCase() === "paycheck";

            // Adjust date for weekends/holidays
            var transactionDate = adjustTransactionDate(new Date(date), isPaycheck);

            if (frequency.toLowerCase() === "one-time" || frequency.toLowerCase() === "one time") {
                if (startDate.toDateString() === date.toDateString()) {
                    var eventDescription = createEventDescription(billName, amount);
                    eventQueue.push({ calendar: billsCalendar, description: eventDescription, date: transactionDate });
                    upcomingData.push([billName, amount, balance, transactionDate, frequency, category]); // Add to Upcoming data
                    if (i !== 0) balance += amount; // Exclude today's transactions from balance calculation
                }
            } else if (frequency.toLowerCase() === "days") {
                var daysDiff = Math.floor((date - startDate) / (24 * 60 * 60 * 1000));
                if (daysDiff >= 0 && (!endDate || date <= endDate) && daysDiff % repeatsEvery === 0) {
                    var eventDescription = createEventDescription(billName, amount);
                    eventQueue.push({ calendar: billsCalendar, description: eventDescription, date: transactionDate });
                    upcomingData.push([billName, amount, balance, transactionDate, frequency, category]); // Add to Upcoming data
                    if (i !== 0) balance += amount; // Exclude today's transactions from balance calculation
                }
            } else if (frequency.toLowerCase() === "weeks") {
                var weeksDiff = Math.floor((date - startDate) / (7 * 24 * 60 * 60 * 1000));
                if (weeksDiff >= 0 && (!endDate || date <= endDate) && weeksDiff % repeatsEvery === 0 && date.getDay() === startDate.getDay()) {
                    var eventDescription = createEventDescription(billName, amount);
                    eventQueue.push({ calendar: billsCalendar, description: eventDescription, date: transactionDate });
                    upcomingData.push([billName, amount, balance, transactionDate, frequency, category]); // Add to Upcoming data
                    if (i !== 0) balance += amount; // Exclude today's transactions from balance calculation
                }
            } else if (frequency.toLowerCase() === "months") {
                var monthsDiff = (date.getFullYear() - startDate.getFullYear()) * 12 + date.getMonth() - startDate.getMonth();
                if (monthsDiff >= 0 && (!endDate || date <= endDate) && monthsDiff % repeatsEvery === 0) {
                    if (startDate.getDate() === date.getDate()) {
                        var eventDescription = createEventDescription(billName, amount);
                        eventQueue.push({ calendar: billsCalendar, description: eventDescription, date: transactionDate });
                        upcomingData.push([billName, amount, balance, transactionDate, frequency, category]); // Add to Upcoming data
                        if (i !== 0) balance += amount; // Exclude today's transactions from balance calculation
                    }
                }
            } else if (frequency.toLowerCase() === "years") {
                var yearsDiff = date.getFullYear() - startDate.getFullYear();
                if (yearsDiff >= 0 && (!endDate || date <= endDate) && yearsDiff % repeatsEvery === 0) {
                    if (startDate.getMonth() === date.getMonth() && startDate.getDate() === date.getDate()) {
                        var eventDescription = createEventDescription(billName, amount);
                        eventQueue.push({ calendar: billsCalendar, description: eventDescription, date: transactionDate });
                        upcomingData.push([billName, amount, balance, transactionDate, frequency, category]); // Add to Upcoming data
                        if (i !== 0) balance += amount; // Exclude today's transactions from balance calculation
                    }
                }
            }
        });

        // Add the projected balance event
        var balanceDescription = i === 0 ? "Balance: " + formatNumber(balance) : "Projected Balance: " + formatNumber(balance);
        eventQueue.push({ calendar: balanceCalendar, description: balanceDescription, date: date });
        originalBalance = balance;

        if (balance < lowestBalance) {
            lowestBalance = balance;
            lowestBalanceDate = new Date(date);
        }
        if (balance > highestBalance) {
            highestBalance = balance;
            highestBalanceDate = new Date(date);
        }
    }

    // Batch create events
    eventQueue.forEach(function (event) {
        event.calendar.createAllDayEvent(event.description, event.date);
    });

    // Update Upcoming sheet
    if (upcomingData.length > 0) {
        upcomingSheet.getRange(2, 1, upcomingData.length, upcomingData[0].length).setValues(upcomingData);
    }

    infoSheet.getRange("B5").setValue(lowestBalance);
    infoSheet.getRange("C5").setValue(lowestBalanceDate);
    infoSheet.getRange("B6").setValue(highestBalance);
    infoSheet.getRange("C6").setValue(highestBalanceDate);
}

// Combined Main Function to Run Everything
function executeBudgetProjection() {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Info");
    var startTime = new Date();
    
    // Update balance from API
    updateBalanceFromAPI();
    
    // Record the current date and time in C3
    var currentDate = new Date();
    sheet.getRange("C3").setValue(currentDate);

    // Project future GCp,s and add transactions
    projectFutureBalancesAndBills();
    
    var endTime = new Date();
    var scriptRunTime = (endTime - startTime) / 1000;
    var minutes = Math.floor(scriptRunTime / 60);
    var seconds = Math.round(scriptRunTime % 60);
    Logger.log('Script runtime: ' + minutes + ' minutes ' + seconds + ' seconds');
}
