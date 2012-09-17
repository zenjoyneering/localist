function(head, req){
    var row;
    send('/*\n    Generated by localist web service\n*/\n\n');
    while (row = getRow()){
        if (row.value.type == "i18n.resource" && row.value.message){
            // string resource
            send('"' + row.value.name + '" = ' +
                '"' + row.value.message + '";\n\n');
        } else if (row.value.type == "i18n.resource" && row.value.plurals){
            //plurals resource
            send("//Plural forms\n");
            for (var quantity in row.value.plurals){
                send('"' + row.value.name + '_' + quantity.toUpperCase() + '" = "' +
                    row.value.plurals[quantity] + '";\n');
            }
            send('\n');
        }
    }
}