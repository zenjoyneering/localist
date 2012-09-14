(function(){
    function uuid(){
        var s = [], itoh = "0123456789ABCDEF";
        for (var i = 0; i<32; i++) {
            s[i] = itoh[Math.floor(Math.random()*0x10)];
        }
        return s.join('');
    }

    var app = {
        login: function(){
            var login = $(".login input[type=text]").val();
            var password = $(".login input[type=password]").val();
            if (!login || !password){
                return;
            }
            $.ajax({
                type: "post",
                url: "/auth/session",
                data: {
                    name: login,
                    password: password
                },
                complete: function(jqXHR, textStatus){
                    var status = $.parseJSON(jqXHR.responseText);
                    if (status.ok){
                        window.location = "/";
                    }
                }
            });
        },

        signin: function(){
            var opts = {},
                i = 0,
                fields = $(".signin form").serializeArray(),
                allFieldsProvided = true;
            for (i in fields){
                opts[fields[i].name] = fields[i].value;
                allFieldsProvided = allFieldsProvided && fields[i].value;
            }
            if (!allFieldsProvided) {
                $(".signin .msg").text("You should fill all fields");
                return;
            }
            if (opts.password != opts.passCheck){
                $(".signin .msg").text("Your passwords not match!");
                return;
            }
            var salt = uuid();
            var userDoc = {
                "type": "user",
                "_id": "org.couchdb.user:" + opts.email,
                "name": opts.email,
                "fullName": opts.name,
                "salt": salt,
                "password_sha": hex_sha1(opts.password + salt),
                "roles": []
            };
            $.ajax({
                type: "post",
                url: "/auth/signin",
                contentType: "application/json",
                data: JSON.stringify(userDoc),
                complete: function(jqXHR, textStatus){
                    var status = $.parseJSON(jqXHR.responseText);
                    if (status.ok){
                        $(".signin").html("<p>You've sucessfully registered. Now wait a mail from us</p>");
                    } else {
                        $(".signin .msg").text("Sorry, but account for this email already registered");
                    }
                }
            });
        }
    };
    window.app = app;
})();

$(function(){
    $(".login form").on("submit", function(event){
        app.login();
        event.preventDefault();
    });
    $(".signin form").on("submit", function(event){
        app.signin();
        event.preventDefault();
    });
});
