// appearance/disappearance of scroll button
var amountScrolled = 300;

$(window).scroll(function() {
	if ( $(window).scrollTop() > amountScrolled ) {
		$('a.back-to-top').fadeIn('slow');
	} else {
		$('a.back-to-top').fadeOut('slow');
	}
});

// Show image on focus in edit genre
$('#poster_url').focus(function() {
	var posterUrl = $('#poster_url').val();
	console.log(posterUrl);
	$('#image-div').show();
	var image = $('#preview-image');
	image.attr('src', posterUrl);

});

$('.grid').masonry({
  // options
  itemSelector: '.panel',
  columnWidth: 400
});