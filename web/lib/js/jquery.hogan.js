/*
    Simple hogan (mustache templating tool) plugin for jQuery

    @author wirewit@yandex.ru
*/
jQuery.fn.hogan = function(context){
    return this.each(function(){
        var $this = $(this),
            template = $this.data("hogan");
        if (!template) {
            // Replacement allows to use template expressions inside the 
            // href attributes, which is escaped in jQuery.html
            $this.data(
                "hogan", 
                Hogan.compile(
                    $this.html().replace(/%7B%7B/g, '{{')
                                .replace(/%7D%7D/g, '}}')
                )
            );
            template = $this.data("hogan");
        }
        $this.html(template.render(context));
    });
}
