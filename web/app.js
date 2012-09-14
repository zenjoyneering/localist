web.app({
    auth: function(options){
        var authUrl = "/auth/session";
        if (!options){
            //just check from the cookie
            $.getJSON(authUrl, function(data){
                if (data.ok && data.userCtx.name){
                    web.app.data.user = data.userCtx;
                    web.app.fire('auth.login', data.userCtx);
                } else {
                    web.app.fire('auth.failure');
                }
            });
        } else {
            $.ajax({
                type: "post",
                url: authUrl,
                data: options,
                complete: function(jqXHR, textStatus){
                    var status = $.parseJSON(jqXHR.responseText);
                    var event = status.ok ? 'auth.login' : 'auth.failure';
                    web.app.fire(event, status);
                }
            });
        }
    },

    logout: function(cb){
        $.ajax({
            type: "delete",
            url: "/auth/session",
            complete: function(){
                if (cb) {
                    cb();
                }
                window.location = "/auth/";
            }
        });
    },


    start: function(){
        web.app.service.init();
        web.app.ui.init();
        history.pushState(null, null, "#projects");
        web.app.ui.projects();
        //web.app.ui.domains();
    }

});
