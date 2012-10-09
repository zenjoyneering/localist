web.app({
    start: function(){
        web.app.service.init();
        web.app.ui.init();
    },
    auth: function(){
        web.app.fire("auth.login", {});
    }
});
