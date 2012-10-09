function(doc){
    if (doc.type && doc.type == "i18n.resource" && doc.locale && doc.created && doc.created.by != "team"){
        emit([doc.created.by, doc.locale, doc.created.at], doc.message.length);
    }
}
