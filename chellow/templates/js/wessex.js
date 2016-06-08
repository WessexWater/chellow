/* 
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */


$( document ).ready( function() {
    
    initSameHeight();
    
    setTimeout( function() {
        initSameHeight();
    }, 1000 );

    $( '.main-navigation h4' ).click( function() {
         var navi 	= $( this ).closest( 'nav' );
         var naviUl 	= $( navi ).find( 'ul' );

         $( navi ).siblings().find( 'ul' ).slideUp( 400 ).removeClass( 'active' );
         $( naviUl ).slideDown( 400 ).addClass( 'active' );
    } );
} );


function initSameHeight() {
    var screen_width    = $( window ).width();
    
    if( screen_width >= 768 ) {
        $( '.bodySameHeight' ).responsiveEqualHeightGrid();
    }
    
    $( '.colSameHeight' ).responsiveEqualHeightGrid();
    $( '.customerServiceCatalogue' ).responsiveEqualHeightGrid();
    $( '.section-item' ).responsiveEqualHeightGrid(4);
    $( '.thumb .CatalogTable tr' ).responsiveEqualHeightGrid(2);
    $( '.layer-sectionProfile .dataBorder' ).responsiveEqualHeightGrid(2);
}
