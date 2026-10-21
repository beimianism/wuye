/* Local module policy: shared by Express and browser. Keep archived source files intact. */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) module.exports = factory();
    else root.localFeatures = factory();
}(typeof window !== 'undefined' ? window : this, function () {
    'use strict';
    // Explicit inventory of disabled page/component codes (no substring keyword blocking).
    var disabledComponents = new Set([
        "indexarrears", "myauditorders", "myaudithistoryorders",
        "simplifyowneraccesscontol", "indexopendooranalysis", "inandoutstep", "chooseinandouttype",
        "activitiesbeautifulstaffmanage",
        "activitiesmanage",
        "activitiesrulemanage",
        "activitiestypemanage",
        "addactivitiesbeautifulstaff",
        "addactivitiesrule",
        "addactivitiestype",
        "addactivitiesview",
        "addadvert",
        "addapplicationkey",
        "addcomplaintstep",
        "addinspectionplan",
        "addinspectionplanstaff",
        "addinspectionpoint",
        "addinspectionroute",
        "additemoutstep",
        "addmachine",
        "addmachineauth",
        "addmachinetranslate",
        "addnotice",
        "addnoticeview",
        "addownerrepair",
        "addpurchaseapplystep",
        "addpurchaseapplyview",
        "addpurchaseapplyview2",
        "addrepairsetting",
        "addresourcequantity",
        "addresourcestore",
        "addresourcestorespecification",
        "addresourcestoretype",
        "addresourcesupplier",
        "addroomcomplaint",
        "addroomrepair",
        "addstorehouse",
        "addvisit",
        "addvisitcase",
        "addvisitspace",
        "advertmanage",
        "advertvedioview",
        "allocationstorehouse",
        "allocationstorehouseapplymanage",
        "allocationstorehouseauditorders",
        "allocationstorehousedetail",
        "allocationstorehousedetailed",
        "allocationstorehousehistoryauditorders",
        "allocationstorehousemanage",
        "allocationuserstorehousemanage",
        "applicationkeymanage",
        "appraiserepair",
        "auditapplicationkeymanage",
        "chooseactivities",
        "chooseactivitiesbeautifulstaff",
        "chooseactivitiesrule",
        "chooseactivitiestype",
        "chooseadvert",
        "chooseapplicationkey",
        "choosecomplaint",
        "chooseinspectionplan",
        "chooseinspectionpoint",
        "chooseinspectionroute",
        "chooseinspectionroutepoint",
        "choosemachine",
        "choosemachineauth",
        "choosemachinetranslate",
        "chooseownerrepair",
        "choosepurchaseapply",
        "chooserepairsetting",
        "chooseresourcestaff",
        "chooseresourcestore",
        "chooseresourcestore2",
        "chooseresourcestore3",
        "chooseresourcestorespecification",
        "chooseresourcesupplier",
        "choosesingleresource",
        "choosestorehouse",
        "complaintdetail",
        "complaintmanage",
        "deleteactivities",
        "deleteactivitiesbeautifulstaff",
        "deleteactivitiesrule",
        "deleteactivitiestype",
        "deleteadvert",
        "deleteapplicationkey",
        "deletecomplaint",
        "deleteinspectionplan",
        "deleteinspectionplanstaff",
        "deleteinspectionpoint",
        "deleteinspectionroute",
        "deleteinspectionroutepoint",
        "deleteitemout",
        "deletemachine",
        "deletemachineauth",
        "deletemachinetranslate",
        "deletenotice",
        "deleteownerrepair",
        "deletepurchaseapply",
        "deleterepairsetting",
        "deleterepairtypeuser",
        "deleteresourcestore",
        "deleteresourcestorespecification",
        "deleteresourcestoretype",
        "deleteresourcesupplier",
        "deletestorehouse",
        "deletestorehousemanage",
        "dispatchrepair",
        "editactivitiesbeautifulstaff",
        "editactivitiesrule",
        "editactivitiestype",
        "editactivitiesview",
        "editadvert",
        "editapplicationkey",
        "editcomplaint",
        "editinspectionplan",
        "editinspectionpoint",
        "editinspectionroute",
        "editmachine",
        "editmachineauth",
        "editmachinetranslate",
        "editnoticeview",
        "editownerrepair",
        "editpurchaseapply",
        "editrepairsetting",
        "editrepairtypeuser",
        "editresourcestore",
        "editresourcestorespecification",
        "editresourcestoretype",
        "editresourcesupplier",
        "editstorehouse",
        "editvisit",
        "finishrepair",
        "forcefinishrepair",
        "inspectionplanmanage",
        "inspectionplanstaffmanage",
        "inspectionplanstate",
        "inspectionpointmanage",
        "inspectionroutemanage",
        "inspectionroutepointmanage",
        "inspectionrouteselect2",
        "inspectiontaskdetail",
        "inspectiontaskmanage",
        "iteminmanage",
        "itemout",
        "itemoutmanage",
        "machineauthmanage",
        "machinemanage",
        "machinerecorddetail",
        "machinerecordmanage",
        "machineselect2",
        "machinestate",
        "machinetranslatemanage",
        "machinevistorphotomanage",
        "myauditcomplaints",
        "myaudithistorycomplaints",
        "myitemoutaudithistoryorders",
        "myitemoutauditorders",
        "myrepairdispatchmanage",
        "myresourcestoremanage",
        "noticedetail",
        "noticemanage",
        "ownerrepairdetail",
        "ownerrepairmanage",
        "printpurchaseapply",
        "printrepairdetail",
        "purchaseapplydetail",
        "purchaseapplydetailmanage",
        "purchaseapplymanage",
        "purchaseapprovers",
        "repairdispatchmanage",
        "repairdispatchstep",
        "repairforcefinishmanage",
        "repairpoolmanage",
        "repairreturnvisit",
        "repairsettingmanage",
        "repairtypeuser",
        "reportrepair",
        "resourceenterdetailmanage",
        "resourceentermanage",
        "resourceoutmanage",
        "resourcestoremanage",
        "resourcestorespecificationmanage",
        "resourcestoretypemanage",
        "resourcestoreuserecordmanage",
        "resourcesuppliermanage",
        "resubmitcomplaint",
        "simplifyownercomplaint",
        "simplifyownerrepair",
        "storehousemanage",
        "transfergoodsstep",
        "viewactivitiesbeautifulstaffinfo",
        "viewactivitiesinfo",
        "viewactivitiesruleinfo",
        "viewactivitiestypeinfo",
        "viewadvertinfo",
        "viewapplicationkeyinfo",
        "viewcomplaintinfo",
        "viewinspectionplaninfo",
        "viewinspectionpointinfo",
        "viewinspectionrouteinfo",
        "viewmachineauthinfo",
        "viewmachineinfo",
        "viewmachinerecordinfo",
        "viewmachinetranslateinfo",
        "viewownerrepairinfo",
        "viewpurchaseapplyinfo",
        "viewrepairsettinginfo",
        "viewresourcestaffinfo",
        "viewresourcestoreinfo",
        "viewresourcestoreinfo2",
        "viewresourcestoreinfo3",
        "viewresourcestorespecificationinfo",
        "viewresourcesupplierinfo",
        "viewstorehouseinfo",
        "viewvisitinfo",
        "visitforowner",
        "visitmanage",
        "visitownerrepair",
        "writeadvertmachine",
        "addcomplaintstepbinding",
        "itemoutbinding",
        "addallocationuserstorehouse",
        "repairdispatchstepbinding",
        "myrepairdispatch",
        "updateinspectionplanstate",
        "editnotice"
]);
    var disabledServices = new Set([
        'repair', 'repairs', 'ownersrepair', 'ownerrepair', 'repairsetting',
        'complaint', 'notice', 'advert', 'activities', 'activitiesrule', 'activitiestype',
        'activitiesbeautifulstaff', 'visit', 'inspectionplan', 'inspectionplanstaff',
        'inspectionpoint', 'inspectionroute', 'inspectionroutepoint', 'inspectiontask',
        'inspectiontaskdetail', 'purchase', 'purchaseapply', 'collection', 'resourcestore',
        'resourcesupplier', 'storehouse', 'machine', 'machineauth', 'machinetranslate',
        'machinerecord', 'machinevistorphoto', 'applicationkey'
    ]);
    var parkingOperations = new Set(['machinetranslate.machinegetfreeparkingspace', 'machinetranslate.machineuploadcarlog', 'machinetranslate.machineroadgateopen', 'machinetranslate.machineheartbeart', 'machinetranslate.machinegettaskinfo', 'machinetranslate.machinecmdresult']);
    var disabledOperations = new Set([
        'index.queryindextodotask', 'index/queryindextodotask',
        'audituser.listaudithistoryorders', 'audituser/listaudithistoryorders',
        'bigscreen/getassetsrepair', 'bigscreen/getassetopendoor', 'bigscreen/getassetinspection',
        'bigscreen.getassetsrepair', 'bigscreen.getassetopendoor', 'bigscreen.getassetinspection',
        'nav/getnavdata', 'reportfeemonthstatistics/queryrepair', 'reportfeemonthstatistics.queryrepair',
        'audituser.listitemoutaudithistoryorders', 'audituser.listitemoutauditorders',
        'audituser.listauditcomplaints', 'audituser.listaudithistorycomplaints'
    ]);
    // Procurement leaves behind a hidden shared audit-user setup link in this group.
    var disabledMenuGroups = new Set(['800201906011']);
    function normalizedPath(value) {
        var path = String(value || '');
        // Menus use /admin.html#/pages/...; the hash is the actual route.
        if (path.indexOf('#') !== -1) path = path.slice(path.indexOf('#') + 1);
        path = path.split('?')[0];
        for (var i = 0; i < 3; i++) {
            try { var decoded = decodeURIComponent(path); } catch (_) { return ''; }
            if (decoded === path) break;
            path = decoded;
        }
        var segments = [];
        path.replace(/\\/g, '/').toLowerCase().split('/').forEach(function (segment) {
            if (segment === '..') segments.pop();
            else if (segment && segment !== '.') segments.push(segment);
        });
        return '/' + segments.join('/');
    }
    function isDisabled(value) {
        var path = normalizedPath(value);
        if (path === '/advertvedio.html' || path === '/bigscreen/js/box2.js') return true;
        var parts = path.split('/').filter(Boolean);
        if (parts[0] === 'app' || parts[0] === 'api' || parts[0] === 'callcomponent') {
            parts.shift();
            if (parts[0] === 'upload') parts.shift();
            var operation = parts.join('/');
            if (parkingOperations.has(operation.replace(/\//g, '.'))) return false;
            // This shared endpoint binds an owner's photo and remains part of owner management.
            if (operation === 'machine.uploadownerphoto' || operation === 'machine/uploadownerphoto') return false;
            if (disabledOperations.has(operation)) return true;
            var service = (parts[0] || '').split('.')[0];
            return disabledComponents.has(service) || disabledServices.has(service);
        }
        if (parts[0] === 'pages' || parts[0] === 'components') {
            return parts.slice(2).some(function (part) {
                return disabledComponents.has(part.replace(/\.(html|js|css)$/, ''));
            });
        }
        return false;
    }
    function filterMenus(menus) {
        if (!Array.isArray(menus)) return [];
        return menus.reduce(function (result, menu) {
            if (!menu || disabledMenuGroups.has(String(menu.id)) || isDisabled(menu.href || menu.url || '')) return result;
            var copy = Object.assign({}, menu);
            if (Array.isArray(menu.childs)) {
                copy.childs = filterMenus(menu.childs);
                if (!copy.childs.length && !(menu.href && menu.href !== '#')) return result;
            }
            result.push(copy);
            return result;
        }, []);
    }
    return { isDisabled: isDisabled, filterMenus: filterMenus, browserMessagesEnabled: false };
}));
