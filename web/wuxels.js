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
    };

    webapp.fire = function(event, eventData){
        if (webapp.events[event]){
            webapp.events[event](eventData);
        }
    };

    webapp.state = function(url){
        var options = {};
        var state;
        var sep = location.hash.indexOf('?');
        var i;
        if (sep > 0){
            var optString = location.hash.substr(sep+1);
            var optParts = optString.split('&');
            var opts;
            for (i in optParts){
                opts = optParts[i].split("=");
                if (opts.length == 2){
                    options[opts[0]] = opts[1];
                }
            }
            state = location.hash.substr(1, sep-1);
        } else if (state){
            state = location.hash.substr(1);
        }
        return {
            hash: state,
            args: options
        };
    };

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
    $(window).on("popstate", function(ev){
        var state = web.app.state();
        var hash = state.hash || web.app.ui['default'];
        if (web.app.ui[hash]){
            //history.pushState(null, "", $this.attr("href"));
            web.app.ui[hash](state.args);
        }
    });
    webapp.run();
});

