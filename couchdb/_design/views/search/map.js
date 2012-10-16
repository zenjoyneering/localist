function(doc){
    if (doc.type && doc.type == "i18n.resource"){
        emit(doc.message, doc.locale + "/" + doc.domain + "/" + doc.name);
    }
}
