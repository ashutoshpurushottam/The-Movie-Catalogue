// appearance/disappearance of scroll button
var amountScrolled = 300;

$(window).scroll(function() {
	if ( $(window).scrollTop() > amountScrolled ) {
		$('a.back-to-top').fadeIn('slow');
	} else {
		$('a.back-to-top').fadeOut('slow');
	}
});

// image preview in create genre
// $('#poster').change(function() {
// 	console.log("poster chagned");
// 	var posterUrl = $('#poster').val();
// 	console.log(posterUrl);
// 	var posterName = posterUrl.split('\\')[2];
// 	$('#image-div').show();
// 	var image = $('#preview-image');
// 	var source = 'static/image/' + posterName;
// 	console.log(source);
// 	image.attr('src', source);
// });
// $('#poster').on('click', function() {
// 	console.log("inside image");
// 	var posterUrl = $('#poster').val();
// 	$('#image-div').show();
// 	var image = $('#preview-image');
// 	image.attr('src', 'static/image/' + posterUrl);
// });

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