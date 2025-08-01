$('<link>')
  .appendTo($('head'))
  .attr({type : 'text/css', rel : 'stylesheet'})
  .attr('href', 'Content/skin.css');
var _lastsearch = "";
$( document ).ready( function() {
window.setInterval( function() {
                var newsearch = $("#results-heading").find(".query").html();
                if( newsearch  == undefined || newsearch == "")
                                return;
                if( newsearch.substring(0,1) == '"' )
                {
                                newsearch = newsearch.substring(1, newsearch.length-1 );
                }
                newsearch = newsearch.trim();
                if( newsearch != "" && newsearch != _lastsearch )
                {
                                _lastsearch = newsearch;
                                var totalResults = $("#results-heading").find(".total-results").html();
                                console.log("SearchResult:"+totalResults+":"+newsearch);

                }
}, 500 );
});
