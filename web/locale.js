var Locale = (function(){
    var LANG_CODE_LENGTH = 2;

    var locales = {};

    var quantity = {
        ZERO: "zero",
        ONE: "one",
        TWO: "two",
        FEW: "few",
        MANY: "many",
        OTHER: "other"
    };

    var Locale = function(code){
        // try to get full match
        if (locales[code]){
            return locales[code];
        }
        //try to find by lang part only
        var lang = code.substr(code, LANG_CODE_LENGTH);
        if (locales[lang]){
            return locales[lang];
        }
        // nothing found, return mock
        return {
            name: code,
            localName: code,
            code: code,
            pluralForms: 2,       // this is valid for most languages
            plural: function(n){
                return n>1;       // most common forms is "n>0" and "n!=1"
            }
        };
    };

    Locale.all = function(){
        return locales;
    };

    Locale.allCodes = function(){
        var keys;
        if (Object.keys){
            keys = Object.keys(locales);
        } else {
            keys = [];
            for (var code in locales){
                keys.push(code);
            }
        }
        return keys;
    };

    locales.ru = {
        name: "Russian",
        localName: "Русский",
        code: "ru_RU",
        pluralForms: [quantity.ONE, quantity.FEW, quantity.OTHER],
        plural: function(n){
            return ( n%10==1 && n%100!=11 ?
                0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2
            );
        }
    };

    locales.en = {
        name: "English",
        localName: "English",
        code: "en_US",
        pluralForms: [quantity.ONE, quantity.OTHER],
        plural: function(n){
            return n != 1;
        }
    };

    locales.es = {
        name: "Spanish",
        localName: "Español",
        code: "es_ES",
        pluralForms: [quantity.ONE, quantity.OTHER],
        plural: function(n){
            return n != 1;
        }
    };

    return Locale;
})();
