// settings
web.app({
    api: { //API URLs
        billing: "../_design/i18n/_view/billing?reduce=true"
    },
    service: {
        init: function(){
            web.app.data = {};
        },
        billing: function(opts, cb){
            // get all users list, and store it
            var url = web.app.api.billing + "&group_level=2",
                i, len, row;
            web.app.data.invoice = [];
            $.getJSON(url, function(data){
                for (i=0, len=data.rows.length; i<len; i++){
                    row = data.rows[i];
                    (function(info){
                        web.app.service.fillInvoice(info, len, opts, cb);
                    })({account: row.key[0],
                        lc_code: row.key[1]
                    });
                };
            });
        },
        fillInvoice: function(invoice, len, opts, cb){
            var url = web.app.api.billing + "&group_level=2" +
                      '&startkey=["' + invoice.account + '", "' +
                      invoice.lc_code + '", ' + opts.start.unix() + ']' +
                      '&endkey=["' + invoice.account + '", "' + 
                      invoice.lc_code + '", ' + opts.end.unix() + ']';
            $.getJSON(url, function(stats){
                invoice['symbols'] = stats.rows.length ? stats.rows[0].value : 0;
                invoice.locale = Locale(invoice.lc_code).name;
                web.app.data.invoice.push(invoice);
                if (web.app.data.invoice.length == len){
                    cb();
                }
            });
        }
    }
});
