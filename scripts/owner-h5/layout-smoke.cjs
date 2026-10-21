// Real compiled CSS at phone widths; no real WeChat identity is asserted here.
const assert = require('node:assert/strict');
const path = require('node:path');
const {chromium} = require(path.resolve(__dirname, '../../.tools/browser/node_modules/playwright-core'));
(async () => {
  const browser = await chromium.launch({executablePath: process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true});
  try {
    for (const width of [360, 390, 430]) {
      const page = await browser.newPage({viewport: {width, height: 844}});
      const failures = [];
      page.on('pageerror', error => failures.push(error.message));
      page.on('response', response => { if (response.status() >= 400) failures.push(new URL(response.url()).pathname); });
      await page.route('**/app/**', route => route.fulfill({status: 200, contentType: 'application/json', body: '{"code":1,"msg":"Layout test only"}'}));
      for (const route of ['pages/index/index', 'pages/my/my']) {
        await page.goto((process.env.OWNER_H5_URL || 'http://127.0.0.1:8000') + '/#/' + route + '?wAppId=layout-synthetic');
        await page.getByText(route === 'pages/my/my' ? '业主信息' : '物业费', {exact: true}).waitFor();
        await page.locator('uni-tabbar .uni-tabbar').waitFor();
        await page.waitForLoadState('networkidle');
        const layout = await page.evaluate(() => {
          const tab = document.querySelector('uni-tabbar .uni-tabbar');
          const images = [...document.querySelectorAll('uni-tabbar img')];
          const raw = [...document.querySelectorAll('style')].map(style => style.textContent).join('\n').replace(/\/\*[\s\S]*?\*\//g, '');
          return {
            tabPosition: getComputedStyle(tab).position,
            tabBottom: tab.getBoundingClientRect().bottom,
            icons: images.map(image => ({width: image.getBoundingClientRect().width, height: image.getBoundingClientRect().height})),
            rows: [...document.querySelectorAll('.cu-list.menu > .cu-item')].map(item => item.getBoundingClientRect().height),
            unsupportedUnits: /[\d.](?:upx|rpx)\b/.test(raw),
            pageWidth: document.documentElement.scrollWidth,
          };
        });
        assert.equal(layout.tabPosition, 'fixed', `${width} ${route}: navigation must stay at the bottom`);
        assert.ok(Math.abs(layout.tabBottom - 844) < 2, 'navigation must fit the viewport');
        assert.equal(layout.icons.length, 2);
        assert.ok(layout.icons.every(icon => icon.width >= 20 && icon.width <= 32 && icon.height <= 32), 'navigation icons must fit their cells');
        assert.equal(layout.unsupportedUnits, false, 'all imported styles must compile uni-app units');
        if (route === 'pages/my/my') assert.ok(layout.rows.length >= 2 && layout.rows.every(height => height >= 40 && height <= 70), 'account menu rows need full touch targets');
        assert.ok(layout.pageWidth <= width, 'page must not overflow horizontally');
        assert.deepEqual(failures, [], 'rendered pages must load without errors');
        if (width === 390) await page.screenshot({path: path.resolve(__dirname, '../../.runtime/layout-' + route.split('/')[1] + '.png'), fullPage: true});
      }
      await page.close();
    }
    console.log('H5 layout passed: home and account at 360/390/430px, compiled units, navigation and menu sizing.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode = 1;});
