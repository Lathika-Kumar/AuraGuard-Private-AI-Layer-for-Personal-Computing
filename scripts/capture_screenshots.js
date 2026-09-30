let playwright;
try {
  playwright = require('playwright');
} catch {
  try {
    playwright = require('C:/Users/hp5cd/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
  } catch {
    throw new Error('Playwright not found. Install playwright or run via npx.');
  }
}
const { chromium } = playwright;
const path = require('path');

const SCREENSHOTS_DIR = 'E:/Auraguard/docs/screenshots';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  console.log('Launching browser...');
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  // -------------------------------------------------------------
  // SCREENSHOT 3 & 4: Grounded Answer & Transparency Panel
  // -------------------------------------------------------------
  console.log('Navigating to http://localhost:5173/ask...');
  await page.goto('http://localhost:5173/ask', { waitUntil: 'networkidle' });
  await sleep(1500);

  console.log('Asking grounded question: "What are the three checkpoints of the AuraGuard Privacy Engine?"');
  await page.fill('textarea', 'What are the three checkpoints of the AuraGuard Privacy Engine?');
  await page.click('button[type="submit"]');

  console.log('Waiting for answer card and pipeline flow to complete...');
  await page.waitForSelector('text=Generated locally on-device', { timeout: 90000 });
  await sleep(2500);

  // Take Screenshot 3: Grounded Answer (Full page or top section showing pipeline + answer + sources)
  console.log('Capturing screenshot-3-grounded-answer.png...');
  await page.screenshot({
    path: path.join(SCREENSHOTS_DIR, 'screenshot-3-grounded-answer.png'),
    fullPage: false,
  });

  // Scroll to Transparency Panel for Screenshot 4
  console.log('Capturing screenshot-4-transparency.png...');
  const transparencyHeading = await page.$('text=Why this answer?');
  if (transparencyHeading) {
    await transparencyHeading.scrollIntoViewIfNeeded();
    await sleep(1000);
  }
  await page.screenshot({
    path: path.join(SCREENSHOTS_DIR, 'screenshot-4-transparency.png'),
    fullPage: false,
  });

  // -------------------------------------------------------------
  // SCREENSHOT 5: ReMind Consent Banner
  // -------------------------------------------------------------
  console.log('Asking memory trigger question...');
  await page.goto('http://localhost:5173/ask', { waitUntil: 'networkidle' });
  await sleep(1500);

  await page.fill('textarea', 'I prefer dark mode and high contrast charts in all my reports.');
  await page.click('button[type="submit"]');

  console.log('Waiting for ReMind consent banner...');
  await page.waitForSelector('text=Potential Memory Detected', { timeout: 90000 });
  await sleep(2000);

  const consentBanner = await page.$('text=Potential Memory Detected');
  if (consentBanner) {
    await consentBanner.scrollIntoViewIfNeeded();
    await sleep(1000);
  }

  console.log('Capturing screenshot-5-remind-consent.png...');
  await page.screenshot({
    path: path.join(SCREENSHOTS_DIR, 'screenshot-5-remind-consent.png'),
    fullPage: false,
  });

  // -------------------------------------------------------------
  // SCREENSHOT 6: ReMind Stored Memory
  // -------------------------------------------------------------
  console.log('Approving memory via "Save Memory" button...');
  const saveBtn = await page.$('button:has-text("Save Memory")');
  if (saveBtn) {
    await saveBtn.click();
    await sleep(2500);
  }

  console.log('Navigating to http://localhost:5173/memory...');
  await page.goto('http://localhost:5173/memory', { waitUntil: 'networkidle' });
  await sleep(3000);

  console.log('Capturing screenshot-6-remind-memory.png...');
  await page.screenshot({
    path: path.join(SCREENSHOTS_DIR, 'screenshot-6-remind-memory.png'),
    fullPage: true,
  });

  // -------------------------------------------------------------
  // SCREENSHOT 7: Sensitive-Data Blocking
  // -------------------------------------------------------------
  console.log('Navigating back to /ask for sensitive data blocking demo...');
  await page.goto('http://localhost:5173/ask', { waitUntil: 'networkidle' });
  await sleep(1500);

  console.log('Entering artificial credential pattern...');
  await page.fill('textarea', 'Please authenticate with sk-proj-1234567890abcdef1234567890');
  await page.click('button[type="submit"]');

  console.log('Waiting for blocked response...');
  await page.waitForSelector('text=blocked', { timeout: 30000 });
  await sleep(2000);

  console.log('Capturing screenshot-7-sensitive-block.png...');
  await page.screenshot({
    path: path.join(SCREENSHOTS_DIR, 'screenshot-7-sensitive-block.png'),
    fullPage: false,
  });

  // -------------------------------------------------------------
  // SCREENSHOT 8: Context Firewall Protection
  // -------------------------------------------------------------
  console.log('Navigating to /ask for Context Firewall demo...');
  await page.goto('http://localhost:5173/ask', { waitUntil: 'networkidle' });
  await sleep(1500);

  console.log('Asking question to retrieve injected prompt from injection_test.pdf...');
  await page.fill('textarea', 'What does section 4 say about the test vector?');
  await page.click('button[type="submit"]');

  console.log('Waiting for Context Firewall banner...');
  await page.waitForSelector('text=Context Firewall', { timeout: 90000 });
  await sleep(2000);

  console.log('Capturing screenshot-8-context-firewall.png...');
  await page.screenshot({
    path: path.join(SCREENSHOTS_DIR, 'screenshot-8-context-firewall.png'),
    fullPage: true,
  });

  await browser.close();
  console.log('ALL SCREENSHOTS CAPTURED SUCCESSFULLY!');
}

run().catch(err => {
  console.error('Fatal error during capture:', err);
  process.exit(1);
});
