function(head, req){
    var row;
    while (row = getRow()){
        if (row.value.i18n && row.value.i18n.message){
            // string resource
            send('"' + row.value.i18n.key + '" = ' +
                '"' + row.value.i18n.message) + '"\n';
        } else if (row.value.i18n && row.value.i18n.plurals){
            //plurals resource
        }
    }
    send('</resources>');
}
