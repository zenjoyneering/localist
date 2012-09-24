function(doc){
    if(doc.type == "i18n.resource" && doc.domain){
        emit(doc.domain, 1);
    }
}
