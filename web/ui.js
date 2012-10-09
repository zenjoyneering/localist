moment.lang('ru');

web.app({
    ui: {
        "default": "projects",
        init: function(){
            $(window).on("change", ".edit textarea", {}, function(){
                var $this = $(this);
                web.app.service.translate(
                    $.trim($this.val()), $this.data(),
                    function(data){
                        if (!data.error){
                            $this.closest('tr').removeClass("untranslated");
                        }
                    }
                );
            });
            $(window).on("change", ".edit-plural textarea", {}, function(ev){
                var $textarea = $(this);
                var $node = $textarea.closest(".edit-plural");
                var options = $node.data();
                options.quantity = $textarea.data("quantity");
                web.app.service.translatePlural(
                    $.trim($textarea.val()), options,
                    function(data){
                        if (!data.error){
                            $node.closest("tr").removeClass("untranslated");
                        }
                    }
                );
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
            // helpers to check the translation state, `this` is an resource
            resource = {
                is_untranslated: function(res){
                    return !web.app.data.translation.to[res._id];
                },
                is_obsolete: function(res){
                    return web.app.data.translation.to[res._id] &&
                           web.app.data.translation.to[res._id].source.rev != res._rev;
                },
                is_reviewed: function(res){
                    return true; // @TODO: Write some code here...
                }
            };
            web.app.data.resource_status = function(){
                    if (resource.is_untranslated(this)){
                        return "untranslated";
                    } else if (resource.is_obsolete(this)){
                        return "obsolete";
                    } else if (resource.is_reviewed(this)){
                        return "reviewed";
                    }
                },
            web.app.data.translate = function(){
                // this == doc with type == 'i18n.resource'
                if (web.app.data.translation.to[this._id]){
                    return web.app.data.translation.to[this._id].message;
                } else {
                    return "";//return this.message;
                }
            };
            web.app.data.translateId = function(){
                if (web.app.data.translation.to[this._id]){
                    return web.app.data.translation.to[this._id]._id;
                } else {
                    return "";
                }
            };
            web.app.data.resourceIsPlural = function(){
                return 'plurals' in this ? true : false;
            }
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
            web.app.logout();
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
                    $("#translation .edit textarea").each(function(el){
                        $(this).css('min-height', $(this).parent().height() + "px");
                    });
                });
            }
        )
    }

});
