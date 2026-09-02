/**
 * Publishes Sabelle's gig sheet the moment she edits it.
 *
 * Lives in the Upcoming Gigs spreadsheet (Extensions > Apps Script), not in the
 * site build. It pokes GitHub, GitHub runs the Sync Gigs workflow, and the
 * website and the Instagram graphics rebuild within a couple of minutes instead
 * of waiting for the next scheduled run.
 *
 * Setup is in GIGS.md under "Publishing straight away". In short:
 *   1. Project Settings > Script Properties: add GITHUB_TOKEN (a fine-grained
 *      PAT with Contents: read and Actions: read and write on the site repo).
 *   2. Triggers > Add Trigger: onSheetChange, From spreadsheet, On change.
 *   3. Reload the sheet; use Gigs > Publish now to test.
 *
 * Nothing here can break the site. If the token is missing or GitHub is down
 * the script gives up quietly and the six-hourly sync still picks the edit up.
 */

var REPO = 'mikemad/sabellesings';  // owner/repo — change if the repo moves
var EVENT_TYPE = 'gigs-updated';

// Sheets fires onChange for every edit. Collapse a burst of them into one
// build; anything the debounce swallows gets caught by the next change or by
// the scheduled sync.
var DEBOUNCE_SECONDS = 90;

/** Adds the Gigs menu when the spreadsheet opens. */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Gigs')
    .addItem('Publish now', 'publishNow')
    .addToUi();
}

/** Installable trigger target: any structural or content change to the sheet. */
function onSheetChange(e) {
  var props = PropertiesService.getScriptProperties();
  var last = Number(props.getProperty('lastDispatch') || 0);
  var now = Date.now();
  if (now - last < DEBOUNCE_SECONDS * 1000) return;
  props.setProperty('lastDispatch', String(now));
  dispatch(false);
}

/** Menu item: rebuild right now, graphics included, debounce ignored. */
function publishNow() {
  var ok = dispatch(true);
  SpreadsheetApp.getActive().toast(
    ok ? 'Publishing — the site updates in a minute or two.'
       : 'Could not reach GitHub. The scheduled sync will pick this up.',
    'Gigs',
    8
  );
}

/**
 * Asks GitHub to run the Sync Gigs workflow.
 * @param {boolean} force Rebuild the graphics even if the dates did not change.
 * @return {boolean} Whether GitHub accepted it.
 */
function dispatch(force) {
  var token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  if (!token) {
    console.warn('No GITHUB_TOKEN script property; leaving it to the schedule.');
    return false;
  }

  var response = UrlFetchApp.fetch('https://api.github.com/repos/' + REPO + '/dispatches', {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + token,
      Accept: 'application/vnd.github+json'
    },
    payload: JSON.stringify({
      event_type: EVENT_TYPE,
      client_payload: { force: force === true }
    }),
    muteHttpExceptions: true
  });

  var code = response.getResponseCode();
  if (code === 204) return true;
  console.error('GitHub returned ' + code + ': ' + response.getContentText());
  return false;
}
