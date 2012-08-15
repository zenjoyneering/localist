(function(){
    //var _app = {};

    webapp = function(spec){
        $.extend(webapp, spec);
    };

    $.extend(webapp, { 
        events: {
            'auth.login': function(user){
                webapp.user = user;
                webapp.start();
            },
            'auth.failure': function(status){
                webapp.ui.login(status);
            }
        },
        data: {}
    });

    webapp.run = function(){
        webapp.auth();
    }

    webapp.fire = function(event, eventData){
        if (webapp.events[event]){
            webapp.events[event](eventData);
        };
    }

    window.web = window.web || {};
    window.web.app = webapp;
})();

(function(){
    var UI = function(actions, init){
        var f = init;
        $.extend(f, actions);
        return f;
    }

    window.web = window.web || {};
    window.web.UI = UI;
})();

$(function(){
    $('*[data-unit]').on('click', '*[data-action]', {}, function(event){
        var $this = $(this);
        var unit = $(event.delegateTarget).data('unit');
        var action = $this.data('action');
        console.log(unit);
        if (web.app.ui[unit] && web.app.ui[unit][action]){
            web.app.ui[unit][action]($(event.delegateTarget), event);
        }
        // find unit
        // exec action
        event.preventDefault();
    });
    $(window).on("click", "a[data-ui-state]", {}, function(event){
        var $this = $(this);
        var state = $this.data("uiState");
        if (web.app.ui[state]){
            history.pushState({}, "", $this.attr("href"));
            web.app.ui[state]($this.data());
            event.preventDefault();
        }
    });
    webapp.run();
});

