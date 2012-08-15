function(head, req){
    var row;
    var xmlEscape = function(str){
        return str.replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;');
    };
    send('<?xml version="1.0" encoding="utf-8"?>\n');
    send('<resources xmlns:xliff="urn:oasis:names:tc:xliff:document:1.2">\n');
    while (row = getRow()){
        if (row.value.i18n && row.value.i18n.message){
            // string resource
            send('    <string name="' + row.value.i18n.key + '">' +
                xmlEscape(row.value.i18n.message) + '</string>\n');
        } else if (row.value.i18n && row.value.i18n.plurals){
            //plurals resource
        }
    }
    send('</resources>');
}
