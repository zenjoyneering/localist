function(doc){
    if (doc && doc.type == "i18n.resource"){
        emit([doc.project, doc.locale, doc.domain, doc.name], doc);
    }
}
