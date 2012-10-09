moment.lang("ru");

web.app({
    ui: {
        init: function(){
            //prefill filter form
            var endDate = moment().startOf('day');
            var startDate = moment().startOf('day').subtract('days', 1);
            $("#start_date").val(startDate.date());
            $("#start_month").val(startDate.month() + 1);
            $("#start_year").val(startDate.year());
            $("#end_date").val(endDate.date());
            $("#end_month").val(endDate.month() + 1);
            $("#end_year").val(endDate.year());
            // start fetch and display
            web.app.ui.renderInvoice({start: startDate, end: endDate});
            // bind events
            $(".date-filter").on("submit", function(ev){
                var start = moment(new Date(ev.target.start_year.value,
                                            ev.target.start_month.value - 1,
                                            ev.target.start_date.value));
                var end = moment(new Date(ev.target.end_year.value,
                                            ev.target.end_month.value - 1,
                                            ev.target.end_date.value));
                web.app.ui.renderInvoice({start: start, end: end});
                ev.preventDefault();
            });
            $(".bill").on("keyup", "input", function(ev){
                var $input = $(ev.target);
                var val = parseFloat($input.val());
                if (isNaN(val)){
                    return;
                }
                var cost = (parseInt($input.parent().prev().text(), 10) * val).toFixed(2);
                $input.parent().next().text(cost);
            });
        },
        renderInvoice: function(opts){
            web.app.service.billing(
                opts,
                function(){
                    $(".bill").hogan(web.app.data);
                }
            );
        }
    }
});
