// UI regression smoke uses synthetic API fixtures; it does not prove backend login.
const assert = require('node:assert/strict');
const path = require('node:path');
const {chromium} = require(path.resolve(__dirname, '../../.tools/browser/node_modules/playwright-core'));
(async () => {
  const browser = await chromium.launch({executablePath:process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  try {
    const page = await browser.newPage({viewport:{width:390,height:844}});
    const errors = [];
    page.on('pageerror', error=>errors.push(error.message));
    let ticketComplete = false;
    let prematureOwnerQuery = false;
    const calls = [];
    await page.route('**/app/**', async route => {
      const name = new URL(route.request().url()).pathname;
      calls.push(name);
      let data = {code:0};
      if (name === '/app/loginOwnerByKey') {
        assert.equal(route.request().postDataJSON().authTicket,'smoke-one-use-ticket');
        await new Promise(resolve=>setTimeout(resolve,300));
        ticketComplete = true;
        data = {code:0,token:'smoke-session',owner:{ownerId:'smoke-owner',userId:'smoke-user',communityId:'smoke-community',communityName:'测试小区'}};
      } else if (name === '/app/owner.listAppUserBindingOwners') {
        if (!ticketComplete) prematureOwnerQuery = true;
        data = {code:0,data:[]};
      } else if (name === '/app/room.queryRoomsByOwner') {
        data = {code:0,rooms:[{roomId:'smoke-room',floorNum:'1',unitNum:'2',roomNum:'301'}]};
      } else if (name === '/app/fee.listFee') data = {code:0,fees:[]};
      else if (name === '/app/refreshToken') data = {code:1,msg:'UI smoke has no real OAuth'};
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
    });
    const base = process.env.OWNER_H5_URL || 'http://127.0.0.1:8000';
    await page.goto(base + '/#/pages/index/index?wAppId=smoke-app');
    await page.getByText('物业费',{exact:true}).waitFor();
    assert.deepEqual(errors,[],'homepage must mount without JavaScript errors');
    await page.goto(base + '/#/pages/login/login?wAppId=smoke-app&code=smoke-binding-ticket');
    await page.getByText('用户名',{exact:true}).waitFor();
    await page.goto(base + '/#/pages/register/register?wAppId=smoke-app');
    await page.getByText('姓名',{exact:true}).waitFor();
    await page.goto(base + '/#/pages/my/myHouse?wAppId=smoke-app&authTicket=smoke-one-use-ticket');
    await page.getByText('1号楼2单元301室',{exact:false}).waitFor({timeout:5000});
    assert.equal(prematureOwnerQuery,false,'owner queries must await the OAuth ticket exchange');
    assert.equal(new URL(page.url()).hash.includes('authTicket='),false,'ticket must be removed after login');
    await page.goto(base + '/#/pages/roomFeeListNew/roomFeeListNew?wAppId=smoke-app');
    await page.waitForTimeout(500);
    assert.ok(calls.includes('/app/fee.listFee'),'bill page must issue the fee query');
    const fee = {amount:'10',feeFlag:'2006012',endTime:'2026-10-21 00:00:00',feeId:'smoke-fee',roomId:'smoke-room'};
    await page.goto(base + '/#/pages/roomFee/roomFee?wAppId=smoke-app&fee=' + encodeURIComponent(JSON.stringify(fee)));
    const paymentButton = page.getByText('微信支付未开通',{exact:true});
    await paymentButton.waitFor();
    assert.equal(await paymentButton.getAttribute('disabled'),'true');
    assert.deepEqual(errors,[],'retained pages must not throw JavaScript errors');
    console.log('Owner H5 UI fixture smoke passed: home, login, register, ticket login, rooms, bills, unavailable payment.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
