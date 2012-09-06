function(doc){
    if (doc.type == 'i18n.project'){
        emit(doc._id, doc);
    }
}
