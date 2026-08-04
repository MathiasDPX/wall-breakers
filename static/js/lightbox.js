// Fork of https://raw.githubusercontent.com/jhvanderschee/jekyllcodex/gh-pages/js/lightbox.js

function setGallery(el) {
    var elements = document.body.querySelectorAll(".gallery");
    elements.forEach(element => {
        element.classList.remove('gallery');
	});
    el.classList.add('current');
}

document.addEventListener("DOMContentLoaded", function() {
    //create lightbox div in the footer
    var newdiv = document.createElement("div");
    newdiv.setAttribute('id',"lightbox");
    document.body.appendChild(newdiv);

    //remove the clicked lightbox
    document.getElementById('lightbox').addEventListener("click", function(event) {
        this.innerHTML = '';
        document.getElementById('lightbox').style.display = 'none';

        // reenable scrolling
        document.body.classList.remove("remove-scrolling");
    });

    // add the image lightbox on click
    var elements = document.querySelectorAll('article figure:has( img)');
    elements.forEach(element => {
        const image = element.querySelector("img");
        const caption = element.querySelector("figcaption")?.innerHTML || "";
        image.addEventListener("click", function(event) {
            event.preventDefault();
            document.getElementById('lightbox').innerHTML = '<div class="img" style="background: url(\''+this.getAttribute('src')+'\') center center / contain no-repeat;" title="'+caption+'" ><img src="'+this.getAttribute('src')+'" alt="'+caption+'" /></div><span>'+caption+'</span>';
            document.getElementById('lightbox').style.display = 'block';

            // disable scroll
            document.body.classList.add("remove-scrolling"); 

            setGallery(this);
        });
    });

});