function refreshAccounts() {
    var url = "https://your-domain.com/budgetcalendar/refresh-accounts/";  // Ensure this URL matches exactly
    var response = UrlFetchApp.fetch(url, {method: 'get', muteHttpExceptions: true});

    if (response.getResponseCode() === 200) {
        Logger.log('Account refresh initiated. Waiting for completion...');
    } else {
        throw new Error('Failed to initiate account refresh: ' + response.getContentText());
    }
}
