function(doc){
    if (doc && doc.i18n){
        emit([doc.i18n.locale, doc.i18n.domain], doc);
    }
}
