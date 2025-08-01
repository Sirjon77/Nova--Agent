// Injects/ensures a stable session_id cookie
(function(){
  function uuidv4(){return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g,c=>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );}
  function getCookie(n){return document.cookie.split('; ').find(r=>r.startsWith(n+'='))?.split('=')[1];}
  if(!getCookie('session_id')){
    var id = uuidv4();
    document.cookie = 'session_id='+id+'; path=/; samesite=Lax';
  }
})();
