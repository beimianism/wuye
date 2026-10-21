// Real local backend/password auth and H5 query smoke. This is not WeChat OAuth.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname,'../..');
const {chromium} = require(path.join(root,'.tools/browser/node_modules/playwright-core'));
const config = JSON.parse(fs.readFileSync(path.join(root,'.runtime/wechat-test.json'),'utf8').replace(/^\uFEFF/,''));
const fixture = JSON.parse(fs.readFileSync(path.join(root,'.runtime/wechat-test-fixture.json'),'utf8'));
(async()=>{
  const browser = await chromium.launch({executablePath:process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  try {
    const context = await browser.newContext({viewport:{width:390,height:844}});
    const response = await context.request.post('http://127.0.0.1:8012/app/loginOwner',{
      headers:{'app-id':'992020061440050003','Content-Type':'application/json'},
      data:{username:fixture.ownerName,password:fixture.password,loginByPhone:false}
    });
    assert.equal(response.status(),200,'Local APP client password login must succeed; this does not exercise WeChat OAuth');
    const auth = await response.json();
    assert.ok(auth.token && auth.owner,'Backend must return a real session and owner');
    const base = 'http://127.0.0.1:' + (config.gatewayPort || 8080);
    await context.request.post(base + '/wechat-test/enter',{form:{code:config.accessCode}});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror',error=>errors.push(error.message));
    const responses = [];
    page.on('response',response=>{const url=new URL(response.url());if(url.pathname.startsWith('/app/'))responses.push([url.pathname,response.status()]);});
    await page.goto(base + '/#/pages/index/index');
    await page.getByText('物业费',{exact:true}).waitFor();
    await page.evaluate(({auth})=>{
      uni.setStorageSync('token',auth.token);
      uni.setStorageSync('ownerInfo',auth.owner);
      uni.setStorageSync('userInfo',JSON.stringify(auth.owner));
      uni.setStorageSync('currentCommunityInfo',{communityId:auth.owner.communityId,communityName:auth.owner.communityName});
      uni.setStorageSync('loginFlag',{sessionKey:auth.owner.userId,expireTime:Date.now()+3600000});
    },{auth});
    await page.goto(base + '/#/pages/my/myHouse');
    await page.getByText('TEST101室',{exact:false}).waitFor({timeout:15000});
    await page.goto(base + '/#/pages/roomFeeListNew/roomFeeListNew');
    await page.getByText('联调测试账单（禁止支付）',{exact:false}).waitFor({timeout:15000});
    assert.deepEqual(errors,[],'Actual backend owner pages must render without JavaScript errors');
    assert.ok(responses.some(([name,status])=>name === '/app/room.queryRoomsByOwner' && status===200));
    assert.ok(responses.some(([name,status])=>name === '/app/fee.listFee' && status===200));
    assert.equal(responses.some(([name])=>name.startsWith('/app/payment/')),false);
    console.log('Real local backend smoke passed: password auth via existing APP client, H5 room and synthetic 0.01 bill queries. WeChat OAuth remains unverified.');
  } finally {await browser.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
