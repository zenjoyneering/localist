function(doc){
    if (doc.type && doc.type == "i18n.resource" && doc.source){
        emit([doc.source.id, doc.locale], doc);
    }
}
