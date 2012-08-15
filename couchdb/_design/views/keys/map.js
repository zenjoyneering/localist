function(doc){
    if (doc.i18n){
        emit(doc.i18n.key, null);
    }
}
