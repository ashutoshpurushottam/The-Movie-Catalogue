// appearance/disappearance of scroll button
var amountScrolled = 300;

$(window).scroll(function() {
	if ( $(window).scrollTop() > amountScrolled ) {
		$('a.back-to-top').fadeIn('slow');
	} else {
		$('a.back-to-top').fadeOut('slow');
	}
});

$('a.back-to-top').click(function() {
	$('html, body').animate({
		scrollTop: 0
	}, 700);
	return false;
});

// image preview in create genre
$('#poster_url').on('change', function() {
	var posterUrl = $('#poster_url').val();
	$('#image-div').show();
	var image = $('#preview-image');
	image.attr('src', posterUrl);
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