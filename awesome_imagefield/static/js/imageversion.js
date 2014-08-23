var imageversion = {
    setCropCoords: function(c, cfmap, scale){
        $.each(cfmap, function(key, value) {
          $('#' + value).val(Math.round(c[key]/scale));
        });
    },
    doCropper: function(cfmap, name, width, height, scale){
        var img = $('#' + name);
        var ver = $('#' + name + '_version');

        width = Math.round(width * scale);
        height = Math.round(height * scale);
        if( ver.length > 0 ){
            $('#' + name + '_cropon').hide();
            $('#' + name + '_cropoff').show();
            ver.hide();
        }
        img.Jcrop({
            onSelect: function(c){ imageversion.setCropCoords(c, cfmap, scale); },
            bgColor:  'black',
            bgOpacity: 0.4,
            minSize:  [width, height],
            aspectRatio: width / height,
            keySupport: false
        });
    },
    removeCropper: function(name, fields){
        $.each(fields, function(key, value) {
          $('#' + value).val('');
        });
        var ver = $('#' + name + '_version');
        var org = $('#' + name);
        org.data('Jcrop').destroy();
        org.hide();/*Jcrop unhides the original image on destroy */
        ver.show();
        $('#' + name + '_cropoff').hide();
        $('#' + name + '_cropon').show();
    },
    addCropper: function(cfmap, name, width, height, active, scale){
        if(active){
            imageversion.doCropper(cfmap, name, width, height, scale);
        }else{
            $('#' + name + '_cropon').click(function(){imageversion.doCropper(cfmap, name, width, height, scale);});
            $('#' + name + '_cropoff').click(function(){imageversion.removeCropper(name, cfmap);});
        }
    }
};
