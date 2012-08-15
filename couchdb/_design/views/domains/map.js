function(doc){
    if(doc.i18n && doc.i18n.domain){
        emit([doc.i18n.locale, doc.i18n.domain], 1);
    }
}
