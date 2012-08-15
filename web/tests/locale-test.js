test("get known locale by lang code", function(){
    var locale = Locale("ru");
    equal(locale.code, "ru_RU", "Locale code differs from expected");
});

test("get known locale by full underscore-separated locale code", function(){
    var locale = Locale("ru_RU");
    equal(locale.code, "ru_RU", "Locale code differs from expected");
});

test("get known locale non-standart locale code", function(){
    var locale = Locale("en-US");
    equal(locale.code, "en_US", "Locale code differs from expected");
});

test("get unknown locale", function(){
    var locale = Locale("--");
    equal(locale.code, "--", "Locale code differs from expected");
});


test("Locale codes iteration", function(){
    var codes = 0;
    for (var code in Locale.all()){
        codes++;
    };
    equal(codes, Locale.allCodes().length, "Iteration fail!");
});

test("get locale by android locale def", function(){
    var locale = Locale("pt-rBR");
    equal(locale.code, "pt_BR", "Locale code differs from expected");
});
