//gas/Accounts Refresh.js


function refreshAccounts() {
  var startTime = new Date();
  try {
    // Configurable Variables
    const refreshApiAuthKey = "API_AUTH"; // Key name in Script Properties

    const props = PropertiesService.getScriptProperties();
    const apiAuth = props.getProperty(refreshApiAuthKey);
    
    if (!apiAuth) {
      Logger.log("API_AUTH missing in Script Properties.");
      throw new Error("Missing API_AUTH");
    }

    // Set Up API Request
    const API_REFRESH_URL = props.getProperty("API_REFRESH_URL");
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

    // Execute API Request
    const response = UrlFetchApp.fetch(API_REFRESH_URL, options);
    if (response.getResponseCode() === 200) {
      Logger.log("Account refresh initiated successfully.");
    } else {
      throw new Error("Refresh failed: " + response.getContentText());
    }

    var endTime = new Date();
    var scriptRunTime = (endTime - startTime) / 1000;
    var minutes = Math.floor(scriptRunTime / 60);
    var seconds = Math.round(scriptRunTime % 60);
    Logger.log('Accounts Refresh runtime: ' + minutes + ' minutes ' + seconds + ' seconds');
  } catch (error) {
    Logger.log('Error during Accounts Refresh execution: ' + error.message);
    throw error;
  }
}
