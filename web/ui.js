moment.lang('ru');

web.app({
    ui: {
        "default": "projects",
        init: function(){
            $(window).on("change", ".edit textarea", {}, function(){
                var $this = $(this);
                web.app.service.translate($.trim($this.val()), $this.data());
            });
            $(window).on("change", ".edit-plural textarea", {}, function(ev){
                var $textarea = $(this);
                var $node = $textarea.closest(".edit-plural");
                var options = $node.data();
                options.quantity = $textarea.data("quantity");
                web.app.service.translatePlural($.trim($textarea.val()), options);
            });
            // some helpers for rendering
            var pluralFormsForLocale = function(locale, content){
                return function(text){
                    var pluralForms = locale.pluralForms;
                    var forms = [];
                    for (var quantity in pluralForms){
                        forms.push({
                            quantity: pluralForms[quantity],
                            text: content[pluralForms[quantity]] || ""
                        });
                    }
                    return Hogan.compile(text).render({forms: forms});
                };
            };
            web.app.data.pluralsFrom = function(){
                return pluralFormsForLocale(web.app.data.fromLocale, this);
            };
            web.app.data.pluralsTo = function(){
                var context;
                if (web.app.data.translation.to[this._id]){
                    context = web.app.data.translation.to[this._id].plurals;
                } else {
                    context = this.plurals;
                }
                return pluralFormsForLocale(web.app.data.toLocale, context);
            };
        },
        login: web.UI({
                signin: function($node){
                    var userName = $node.find('input[name="login"]').val();
                    var userPassword = $node.find('input[name="password"]').val();
                    if (!userName || ! userPassword){
                        $node.find('.alert')
                             .removeClass('alert-info')
                             .addClass('alert-error')
                             .text('You must provide username and password');
                        return;
                    }
                    // try login
                    web.app.auth({
                        name: userName,
                        password: userPassword
                    });
                } 
            }, function(status){
                $("section").hide();
                if (status && status.error && status.reason){
                    $("#login .alert").removeClass('alert-info')
                                      .addClass('alert-error')
                                      .text(status.reason);
                }
                $("#login").show();
            }
        ),
        logout: web.UI({}, function(){
            web.app.data = {};
            web.app.logout(function(){
                web.app.ui.login();
            });
        }),
        projects: web.UI(
            {},
            function(){
                $("section").hide();
                web.app.fetch("projects", {}, function(){
                    $("#projects").hogan(web.app.data).show();
                });
            }
        ),
        progress: web.UI(
            {
            }, 
            function(opts){
                $("section").hide();
                web.app.fetch("locales", opts, function(){
                    $("#progress").hogan(web.app.data).show();
                });
            }
        ),
        domains: web.UI(
            {
            },
            function(opts){
                $("section").hide();
                web.app.fetch("domains", opts, function(){
                    $("#domains").hogan(web.app.data);
                    $("#domains").show();
                });
            }
        ), 
        translate: web.UI(
            {
            },
            function(opts){
                web.app.fetch("translations", opts, function(){
                    $("section").hide();
                    $("#translation").hogan(web.app.data);
                    // fix textarea heights
                    $("#translation").show();
                    $("#translation textarea").each(function(el){
                        $(this).css('min-height', $(this).parent().height() + "px");
                    });
                });
            }
        )
    }

});
