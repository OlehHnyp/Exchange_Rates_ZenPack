Ext.onReady(function() {
    let DEVICE_ID = 'deviceoverviewpanel_snmpsummary';
    Ext.ComponentMgr.onAvailable(DEVICE_ID, function(){
        let overview = Ext.getCmp(DEVICE_ID);

        /* overview.addListener("afterrender", function(){ */
            overview.removeField('snmpDescription');
            overview.removeField('snmpContact');
            overview.removeField('snmpLocation');
            overview.removeField('snmpSysName');

            overview.addField({
                name: 'examplePropery',
                xtype: 'displayfield',
                fieldLabel: _t('Example property')
            });
        /*}); */
    });
});
