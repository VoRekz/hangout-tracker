/**
 * Google Apps Script: Auto-generate Hangout Tracker Form & Linked Sheet
 * 
 * Instructions:
 * 1. Open https://script.new in your browser.
 * 2. Delete existing code, paste this entire script, and click "Run" (the play button).
 * 3. Grant Google permission when prompted.
 * 4. Check the Execution Log at the bottom for your Form link and Sheet link!
 */

function createHangoutFormAndSheet() {
  // 1. Create the Google Form
  var form = FormApp.create('Hangout Tracker');
  form.setDescription('Log group outings, shared expenses, attendees, and who suggested the spot.');

  // Field 1: Date
  form.addDateItem()
      .setTitle('Date')
      .setRequired(true);

  // Field 2: Location
  form.addTextItem()
      .setTitle('Location')
      .setHelpText('e.g., Wingstop, Cinemark, Dave & Busters')
      .setRequired(true);

  // Field 3: Address
  form.addTextItem()
      .setTitle('Address')
      .setHelpText('e.g., Dallas TX (used for map geolocation)')
      .setRequired(false);

  // Field 4: Category
  form.addListItem()
      .setTitle('Category')
      .setChoiceValues(['Dining', 'Entertainment', 'Gaming', 'Groceries', 'Travel', 'Other'])
      .setRequired(true);

  // Field 5: TotalCost
  form.addTextItem()
      .setTitle('TotalCost')
      .setHelpText('e.g., 54.50 (numbers only)')
      .setRequired(true);

  // Group Members List
  var friends = ['Julio', 'Girlfriend', 'Barbara', 'Karla', 'Holden', 'Josue'];

  // Field 6: PaidBy
  form.addListItem()
      .setTitle('PaidBy')
      .setChoiceValues(friends)
      .setRequired(true);

  // Field 7: Attendees (Checkboxes for multi-select)
  form.addCheckboxItem()
      .setTitle('Attendees')
      .setChoiceValues(friends)
      .setRequired(true);

  // Field 8: SuggestedBy
  form.addListItem()
      .setTitle('SuggestedBy')
      .setChoiceValues(friends)
      .setRequired(true);

  // 2. Create the Google Sheet & Link it to the Form
  var ss = SpreadsheetApp.create('Hangout Tracker Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  Logger.log('====================================================');
  Logger.log('🎉 SUCCESS! YOUR FORM AND SHEET ARE CREATED:');
  Logger.log('----------------------------------------------------');
  Logger.log('📱 Form URL (to submit on phone): ' + form.getPublishedUrl());
  Logger.log('📝 Form Edit URL: ' + form.getEditUrl());
  Logger.log('📊 Google Sheet URL (for ETL): ' + ss.getUrl());
  Logger.log('====================================================');
}

