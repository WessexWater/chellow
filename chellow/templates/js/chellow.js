/* 
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
/* 
    Created on  : May 27, 2016, 11:03:30 AM
    Edited on   : July 20, 2016, 12:15:08 PM
    Author      : AL
*/


$( document ).ready( function() {
    
    initSameHeight();
    checkScreenWidth();
    updateBreadcrumbLength();
    
    setTimeout( function() {
        initSameHeight();
    }, 1000 );
    
    $( window ).resize( function() {
        initSameHeight();
        checkScreenWidth();
        updateBreadcrumbLength();
    } );
    
    $( 'body' ).on( 'click', '.layer-page', function( e ) {
        if( $( e.target ).closest( '.layer-sidebar' ).length ) {
            return;
        }
        
        if( $( e.target ).closest( '.panel-mainmenubutton' ).length ) {
            return;
        }
        
//        toggleMenuMain( true );
    } );
} );


function initSameHeight() {
    var screen_width    = $( window ).width();
    
    if( screen_width >= 768 ) {
        $( '.bodySameHeight' ).responsiveEqualHeightGrid();
        $( '.headerSameHeight' ).responsiveEqualHeightGrid();
    }
    
    $( '.colSameHeight' ).responsiveEqualHeightGrid();
    $( '.customerServiceCatalogue' ).responsiveEqualHeightGrid();
    $( '.section-item' ).responsiveEqualHeightGrid(4);
    $( '.thumb .CatalogTable tr' ).responsiveEqualHeightGrid(2);
    $( '.layer-sectionProfile .dataBorder' ).responsiveEqualHeightGrid(2);
}

function toggleMenuMain( boolHideMenu ) {
    var layerSidebar    = $( '.layer-sidebar' );
    var screenSize      = $( window ).width();
    
    if( $( layerSidebar ).hasClass( 'shown' ) || boolHideMenu ) {
        $( layerSidebar ).removeClass( 'shown' ).animate( { left: '-100%' }, 300 );
        
        $( 'body' ).removeClass( 'overflowHidden' );
        
        $( '.panel-mainmenubutton i' ).removeClass( 'fa-times' ).addClass( 'fa-bars' );
    } else {
        $( layerSidebar ).addClass( 'shown' ).animate( { left: 0 }, 300 );
        
        if( screenSize < 768 ) $( 'body' ).addClass( 'overflowHidden' );
        
        $( '.panel-mainmenubutton i' ).removeClass( 'fa-bars' ).addClass( 'fa-times' );
    }
}

function checkScreenWidth() {
    var windowSize  = $( window ).width();
    
    $( '.menuHide .layer-sidebar' ).removeClass( 'shown' ).animate( { left: '-100%' }, 300 );
    $( 'body' ).removeClass( 'overflowHidden' );
    $( '.panel-mainmenubutton i' ).removeClass( 'fa-times' ).addClass( 'fa-bars' );
    
    if( windowSize < 768 ) {
        mobileFunctions();
    }
    
    if( windowSize >= 768 ) {
        desktopFunctions();
    }
    
    $( '.main-navigation h4' ).click( function() {
        console.log( 'asd' );
        console.log( windowSize );
        
        var navi 	= $( this ).closest( 'nav' );
        var naviUl 	= $( navi ).find( 'ul' );
        var isActive = $( this ).siblings( 'ul' ).attr( 'class' );
        if( isActive == 'active' ){
        //    $( navi ).siblings().find( 'ul' ).slideUp( 400 ).removeClass( 'active' );
            $( naviUl ).slideUp( 400 ).removeClass( 'active' );
        }else{
            
            $( navi ).siblings().find( 'ul' ).slideUp( 400 ).removeClass( 'active' );
            $( naviUl ).slideDown( 400 ).addClass( 'active' );
        
        }
        
        // if( !windowSize > 768 ) {
        //    $( navi ).siblings().find( 'ul' ).slideUp( 400 ).removeClass( 'active' );
        //    $( naviUl ).slideDown( 400 ).addClass( 'active' );
        // }
    } );
    
    return windowSize;
}

function mobileFunctions() {
    
}

function desktopFunctions() {
    
}

function updateBreadcrumbLength() {
    var widthTopHeader  = $( '.top-header' ).width();
    var pullLeft        = $( '.top-header .pull-left' );
    var pullRight       = $( '.top-header .pull-right' );
    var widthPullRight  = $( pullRight ).width();
    var widthBreadcrumb = widthTopHeader - widthPullRight - 15;
    
    if( widthTopHeader != widthPullRight && widthPullRight != 0 && $( pullRight ).is( ':visible' ) ) {
        $( pullLeft ).width( widthBreadcrumb );
    } else {
        $( pullLeft ).css( { 'width' : '100%' } );
    }
}


function removePlaceHolder() {
    
    var siteSearch      = $( '.siteSearch input[name="pattern"]' );
    var siteSearchVal   = $( siteSearch ).val();
    
    var supplySearch    = $( '.supplySearch input[name="search_pattern"]' );
    var supplySearchVal = $( supplySearch ).val();
    
    if( siteSearchVal == 'Search Sites...' ) {
        $( siteSearch ).val( '' );
    }
    
    if( supplySearchVal == 'Search Supplies...' ) {
        $( supplySearch ).val( '' );
    }
    
}
