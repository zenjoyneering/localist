(function(){
    var app = {
        login: function(){
            var login = $(".login input[type=text]").val();
            var password = $(".login input[type=password]").val();
            if (!login || !password){
                console.log("msg");
                return;
            }
        },

        signin: function(){
        }
    }
    window.app = app;
})();

$(function(){
    $(".login form").on("submit", function(event){
        app.login();
        event.preventDefault();
    });
});
